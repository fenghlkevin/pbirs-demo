"""Demo user management and PBIRS item-policy administration; no Windows credentials."""
import copy
import hashlib
import json
import os
import re
import secrets
import threading
from pathlib import Path

import requests
BASE = os.environ.get("P4_PBIRS_URL", "http://pbirs.example.internal").rstrip("/")

ROOT = Path(__file__).resolve().parent
ACCOUNTS_PATH = Path(os.environ.get('P4_ACCOUNTS_PATH',str(ROOT / 'app-accounts.local.json')))
FOLDER_ID = '98130126-1a80-474d-a151-d20bb2678de4'
MUTATION_LOCK = threading.RLock()


class AdminError(Exception):
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)


def atomic_json(path, data):
    temporary = path.with_name(path.name + '.' + secrets.token_hex(6) + '.tmp')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def password_record(password):
    if not isinstance(password, str) or not 8 <= len(password) <= 128:
        raise AdminError(400, '密码长度需要为 8～128 个字符')
    salt = secrets.token_hex(16)
    return {'salt': salt, 'iterations': 600000, 'passwordHash': hashlib.pbkdf2_hmac(
        'sha256', password.encode(), bytes.fromhex(salt), 600000).hex()}


def load_accounts():
    return json.loads(ACCOUNTS_PATH.read_text(encoding='utf-8'))


def is_admin(account):
    return account.get('role') == 'admin'


def principal_equal(left, right):
    return left.casefold() == right.casefold() if os.environ.get('P6_AUTH_MODE') == 'windows' else left == right


def public_user(name, account):
    return {'username': name, 'displayName': account.get('displayName', name),
            'enabled': account.get('enabled', True), 'role': account.get('role', 'viewer'),
            'principal': account['principal']}


class Policies:
    def __init__(self):
        # Administrative control plane only. Report viewing NEVER uses this identity.
        if os.environ.get('P6_AUTH_MODE') == 'windows':
            from ad_integration import windows_session
            self.session = windows_session()
        else:
            from ticket_auth import establish
            self.session, _ = establish('p4:maintenance')

    def call(self, method, path, payload=None):
        response = self.session.request(method, BASE + '/Reports/api/v2.0' + path,
                                        json=payload, timeout=35, allow_redirects=False)
        if not response.ok:
            raise AdminError(502, 'PBIRS 授权操作失败（HTTP ' + str(response.status_code) + '）')
        return response.json() if response.content else None

    def catalog(self):
        data=self.call('GET','/CatalogItems');items=[]
        while True:
            items.extend({key:item[key] for key in ('Id','Name','Path','Type')}
                         for item in data.get('value',[]) if item.get('Type') in ('Folder','PowerBIReport','Report'))
            link=data.get('@odata.nextLink')
            if not link:break
            # Only accept pagination within this API, never arbitrary upstream URLs.
            prefix=BASE+'/Reports/api/v2.0'
            if not link.startswith(prefix+'/'):raise AdminError(502,'目录分页地址异常')
            data=self.call('GET',link[len(prefix):])
        return sorted(items,key=lambda x:(x['Path'].count('/'),x['Path'].lower()))

    @staticmethod
    def policy_path(item):
        collection={'Folder':'Folders','PowerBIReport':'PowerBIReports','Report':'Reports'}[item['Type']]
        return '/'+collection+'('+item['Id']+')/Policies'

    def reports(self):
        return [item for item in self.catalog() if item['Type']!='Folder']

    def read(self,path):
        data=self.call('GET',path)
        return {'InheritParentPolicy':data.get('InheritParentPolicy',False),'Policies':data.get('Policies',[])}

    def matrix(self):
        items=self.catalog()
        for item in items:
            try:
                policy=self.read(self.policy_path(item))
                item['policies']=policy['Policies'];item['inherits']=policy['InheritParentPolicy']
            except AdminError:
                if os.environ.get('P6_AUTH_MODE') != 'windows':raise
                # Legacy Custom-only descriptors can be unreadable by Windows.
                # Keep them visible to administrators, never infer an empty ACL.
                item.update(policies=[], inherits=False, policyReadError=True)
        return items

    def replace_selection(self,principal,folder_ids,report_ids,enabled,commit):
        items=self.matrix();by_id={item['Id']:item for item in items};by_path={item['Path']:item for item in items}
        folders=set(folder_ids);reports=set(report_ids)
        if any(i not in by_id or by_id[i]['Type']!='Folder' for i in folders):
            raise AdminError(400,'目录不存在或类型不正确')
        if any(i not in by_id or by_id[i]['Type']=='Folder' for i in reports):
            raise AdminError(400,'报表不存在或类型不正确')
        paths=[by_id[i]['Path'] for i in folders]
        def allowed(item):
            return enabled and (item['Id'] in reports or any(under(item['Path'],path) for path in paths))
        # Native portal browsing requires every ancestor folder, including Home.
        # Treat navigation separately from blanket directory selection.
        navigation={folder['Id'] for folder in items if folder['Type']=='Folder'
                    and any(allowed(child) and under(child['Path'],folder['Path']) for child in items)}
        def desired(item):return allowed(item) or (enabled and item['Id'] in navigation)
        changes=[]
        for item in items:
            if item.get('policyReadError'):
                if allowed(item):raise AdminError(409,'此旧资源的 Windows 权限不可读，请先完成资源迁移')
                continue
            path=self.policy_path(item)
            original={'InheritParentPolicy':item['inherits'],'Policies':item['policies']}
            parent=by_path.get(item['Path'].rsplit('/',1)[0] or '/') if item['Path']!='/' else None
            # Native inherited children follow the selected ancestor automatically.
            # Independent children get matching direct grants, without resetting anyone else's ACL.
            if item['inherits'] and parent is not None and desired(item)==desired(parent):continue
            break_inheritance=item['inherits'] and parent is not None and desired(item)!=desired(parent)
            entries=copy.deepcopy(original['Policies'])
            previous=[entry for entry in entries if principal_equal(entry['GroupUserName'],principal)]
            if any(any(role['Name']!='Browser' for role in entry.get('Roles',[])) for entry in previous):
                raise AdminError(409,'该用户存在高级资源角色，请先在 PBIRS 核查，Demo 不覆盖高级权限')
            granted=desired(item)
            if bool(previous)==granted and not break_inheritance:continue
            entries=[entry for entry in entries if not principal_equal(entry['GroupUserName'],principal)]
            if granted:entries.append({'GroupUserName':principal,'Roles':[{'Name':'Browser'}]})
            changes.append((path,original,{'InheritParentPolicy':False,'Policies':entries}))
        applied=[]
        try:
            # Protect unselected inherited children before granting ancestor Browser.
            for path,original,updated in reversed(changes):
                self.call('PUT',path,updated);applied.append((path,original))
            commit()
        except Exception:
            failed=False
            for path,original in reversed(applied):
                try:self.call('PUT',path,original)
                except Exception:failed=True
            if failed:raise AdminError(502,'授权保存失败，回滚未全部成功，请检查 PBIRS 授权')
            raise

    def replace_viewer(self,principal,report_ids,enabled,commit):
        # Compatibility for older validation helpers; no automatic parent Browser grant.
        return self.replace_selection(principal,[],report_ids,enabled,commit)


def under(path,folder):
    return folder=='/' or path==folder or path.startswith(folder.rstrip('/')+'/')


def selection_for(account,items):
    stored=account.get('accessSelection')
    if stored is not None:return copy.deepcopy(stored)
    # Existing demo folder entries were navigation grants, never blanket directory grants.
    return {'folderIds':[],'reportIds':grants_for(account,items)}


def effective_ids(selection,items):
    by_id={item['Id']:item for item in items}
    paths=[by_id[i]['Path'] for i in selection['folderIds'] if i in by_id]
    return {item['Id'] for item in items if item['Id'] in selection['reportIds']
            or any(under(item['Path'],path) for path in paths)}


def reconcile_permissions():
    import time
    while True:
        time.sleep(60)
        try:
            with MUTATION_LOCK:
                for account in load_accounts().values():
                    if is_admin(account) or 'accessSelection' not in account:continue
                    policies=Policies();items=policies.catalog();known={i['Id'] for i in items}
                    selection=account['accessSelection']
                    # Deleted resources stop applying; IDs are stable across renames/moves.
                    policies.replace_selection(account['principal'],
                        [i for i in selection['folderIds'] if i in known],
                        [i for i in selection['reportIds'] if i in known],account.get('enabled',True),lambda:None)
        except Exception as error:
            print('Permission reconciliation failed: '+str(error),flush=True)


def grants_for(account, reports):
    if account['principal'] in ('p4:portaladmin','p4:maintenance'):
        return [report['Id'] for report in reports if report['Type']!='Folder']
    principal = account['principal']
    return [report['Id'] for report in reports if report['Type']!='Folder' and any(
        principal_equal(entry['GroupUserName'], principal) and any(role['Name'] in ('Browser', 'Content Manager')
                                                   for role in entry.get('Roles', []))
        for entry in report.get('policies', []))]


def bootstrap():
    with MUTATION_LOCK:
        accounts = load_accounts()
        changed = False
        for name, account in accounts.items():
            if account['principal'] == 'p4:portaladmin' and account.get('role') != 'admin':
                account['role'] = 'admin'
                changed = True
        created = 'admin' not in accounts
        if created:
            password = 'DemoAdmin!' + secrets.token_urlsafe(16)
            accounts['admin'] = {**password_record(password), 'principal': 'p4:admin',
                                 'displayName': 'Demo 管理员', 'enabled': True,
                                 'role': 'admin', 'version': 1}
            atomic_json(ROOT / 'demo-admin-login.local.json',
                        {'username': 'admin', 'password': password})
            changed = True
        if created:
            policies = Policies()
            reports = policies.reports()
            policies.replace_viewer('p4:admin', [report['Id'] for report in reports], True,
                                    lambda: atomic_json(ACCOUNTS_PATH, accounts))
        elif changed:
            atomic_json(ACCOUNTS_PATH, accounts)
