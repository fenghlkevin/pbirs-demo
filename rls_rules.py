"""Read-only TOM rule snapshots, bound to the current PBIRS report revision."""
import json
import os
import subprocess
import threading
import time
from pathlib import Path


COLLECT_LOCK = threading.Lock()

def collect_rules():
    library = os.environ.get('P6_TOM_LIBRARY')
    output = os.environ.get('P6_RULES_PATH')
    if not library or not output:
        return
    with COLLECT_LOCK:
        try:
            if time.time() - Path(output).stat().st_mtime < 30:
                return
        except OSError:
            pass
        args = ['powershell.exe', '-NoProfile', '-NonInteractive', '-File',
                str(Path(__file__).resolve().parent / 'ad/export-rules.ps1'),
                '-OutputPath', output, '-TomLibrary', library]
        if os.environ.get('P6_MODEL_BINDINGS_PATH'):
            args += ['-BindingsPath', os.environ['P6_MODEL_BINDINGS_PATH']]
        try:
            subprocess.run(args, capture_output=True, timeout=120, check=True)
        except (OSError, subprocess.SubprocessError):
            # Existing snapshot is still checked for version and age on every read.
            pass


def rules_for(policies, report_id, roles):
    result = {r['ModelRoleId']: {'ruleStatus': 'unavailable', 'rules': [],
              'ruleMessage': '尚未采集此报表的模型规则'} for r in roles}
    path = os.environ.get('P6_RULES_PATH')
    if not path:
        return result
    try:
        snapshot = json.loads(Path(path).read_text(encoding='utf-8-sig'))['reports'][report_id]
        age = time.time() - snapshot['capturedAt']
        if not 0 <= age <= int(os.environ.get('P6_RULES_MAX_AGE', '600')):
            raise ValueError('规则快照已过期，请重新采集')
        current = policies.call('GET', '/PowerBIReports(' + report_id + ')')
        if current.get('ModifiedDate') != snapshot['modifiedDate']:
            raise ValueError('报表已重新发布，规则快照需更新')
        stored = snapshot['roles']
        if set(stored) != {r['ModelRoleId'] for r in roles}:
            raise ValueError('模型角色已变化，请重新采集规则')
        for role in roles:
            item = stored[role['ModelRoleId']]
            if item['name'] != role['ModelRoleName']:
                raise ValueError('角色名称已变化，请重新采集规则')
        return {r['ModelRoleId']: {'ruleStatus': 'ok', 'rules': stored[r['ModelRoleId']]['rules'],
                'capturedAt': snapshot['capturedAt'], 'source': 'TOM',
                'ruleMessage': ''} for r in roles}
    except (OSError, ValueError, KeyError, TypeError):
        return {key: {**value, 'ruleMessage': '规则未采集、读取失败或已过期，请重新采集模型规则'}
                for key, value in result.items()}


class RuleRlsMixin:
    def user_inventory(self, username, accounts):
        from demo_admin import AdminError, is_admin, public_user, principal_equal
        from rls_admin import revision
        account = accounts.get(username)
        if not account or is_admin(account):
            raise AdminError(400, '请选择普通用户')
        collect_rules()
        identities = {account['principal'].casefold(), *(g.casefold() for g in account.get('groups', []))}
        results = []
        for report in self.reports():
            try:
                _, roles, assignments = self.read(report['Id'])
                details = rules_for(self.policies, report['Id'], roles) if roles else {}
                selected = sorted({rid for a in assignments
                    if principal_equal(a['GroupUserName'], account['principal'])
                    for rid in a.get('DataModelRoles', [])})
                results.append({**report, 'status': 'ok',
                    'roles': [{'Id': r['ModelRoleId'], 'Name': r['ModelRoleName'],
                               **details[r['ModelRoleId']]} for r in roles],
                    'roleIds': selected, 'revision': revision(roles, assignments),
                    'groupAssignments': [a for a in assignments
                        if a['GroupUserName'].casefold() in identities
                        and not principal_equal(a['GroupUserName'], account['principal'])]})
            except Exception:
                results.append({**report, 'status': 'error', 'roles': [],
                    'error': '此报表的 Windows 模型权限不可读取，未参与保存；请先完成旧资源迁移'})
        return {'user': public_user(username, account), 'reports': results}
