"""AD-only Demo backend. Start behind the authenticated Windows gateway."""
import base64
import hashlib
import hmac
import json
import os
import secrets
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import requests
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ad_integration import directory, directory_status, sync_directory
from demo_admin import AdminError, MUTATION_LOCK, Policies, atomic_json, public_user, selection_for, effective_ids
from rls_admin import RlsAdmin
from rls_rules import RuleRlsMixin

ROOT = Path(__file__).resolve().parent
NONCES = {}; NONCE_LOCK = threading.Lock()


class AdRls(RuleRlsMixin, RlsAdmin):
    pass


def verify_gateway(headers, method, path, body, key, now=None):
    now = time.time() if now is None else now
    try:
        stamp = headers['X-P6-Time']; nonce = headers['X-P6-Nonce']; encoded = headers['X-P6-User']
        if abs(now - int(stamp)) > 30 or len(nonce) != 32:
            raise ValueError()
        message = '\n'.join([method, path, stamp, nonce, encoded, hashlib.sha256(body).hexdigest()])
        expected = hmac.new(key, message.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, headers.get('X-P6-Signature', '')):
            raise ValueError()
        principal = base64.b64decode(encoded, validate=True).decode('utf-8')
        if '\\' not in principal:
            raise ValueError()
        with NONCE_LOCK:
            for value, expiry in list(NONCES.items()):
                if expiry < now:
                    del NONCES[value]
            if nonce in NONCES:
                raise ValueError()
            NONCES[nonce] = now + 60
        return principal
    except (ValueError, TypeError, KeyError, UnicodeError):
        raise AdminError(401, 'Windows 登录凭证无效，请通过 AD 登录入口访问')


def visible_items(policies, account):
    identities = {account['principal'].casefold(), *(g.casefold() for g in account.get('groups', []))}
    # Navigation is metadata only; PBIRS authorizes every actual iframe request.
    items = policies.matrix()
    visible = [i for i in items if any(a['GroupUserName'].casefold() in identities
                  and a.get('Roles') for a in i['policies'])]
    by_path = {i['Path']: i for i in items}; result = {i['Id']: i for i in visible}
    for item in visible:
        parent = item['Path'].rsplit('/', 1)[0]
        while parent:
            folder = by_path.get(parent)
            if folder and folder['Id'] not in result:
                result[folder['Id']] = {**folder, 'navigationOnly': True}
            parent = parent.rsplit('/', 1)[0]
    return [{k: i[k] for k in ('Id', 'Name', 'Path', 'Type')} for i in result.values()]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, data, kind='application/json; charset=utf-8'):
        raw = json.dumps(data, ensure_ascii=False).encode() if not isinstance(data, bytes) else data
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        self.handle_api()

    def do_POST(self):
        self.handle_api()

    def handle_api(self):
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 <= size <= 1024 * 1024:
                raise AdminError(413, '请求过大')
            raw = self.rfile.read(size)
            principal = verify_gateway(self.headers, self.command, self.path, raw, self.server.gateway_key)
            if self.command == 'POST' and self.headers.get('Origin') != os.environ['P6_PUBLIC_URL'].rstrip('/'):
                raise AdminError(403, '请求来源不匹配')
            state = directory(); accounts = state['users']
            account = next((a for a in accounts.values() if a['principal'].casefold() == principal.casefold()), None)
            if not account or not account['enabled']:
                raise AdminError(403, 'Windows 用户尚未同步、已停用或不在同步范围')
            path = urlsplit(self.path).path; query = parse_qs(urlsplit(self.path).query)
            data = json.loads(raw) if raw else {}
            if not isinstance(data, dict):
                raise AdminError(400, '请求内容不正确')
            if path == '/' and self.command == 'GET':
                return self.reply(200, (ROOT / 'ad/index.html').read_bytes(), 'text/html; charset=utf-8')
            if path == '/api/me' and self.command == 'GET':
                return self.reply(200, {**public_user(account['username'], account),
                    'pbirsUrl': os.environ['P4_PBIRS_URL'].rstrip('/'), 'authentication': 'Windows'})
            if path == '/api/catalog' and self.command == 'GET':
                return self.reply(200, {'value': visible_items(Policies(), account)})
            if not path.startswith('/api/admin/'):
                raise AdminError(404, '接口不存在')
            if account['role'] != 'admin':
                raise AdminError(403, '需要 Demo 管理员权限')
            if path == '/api/admin/ad' and self.command == 'GET':
                return self.reply(200, directory_status())
            if path == '/api/admin/ad/sync' and self.command == 'POST':
                return self.reply(200, sync_directory())
            with MUTATION_LOCK:
                state = directory(); accounts = state['users']
                if path == '/api/admin/users' and self.command == 'GET':
                    return self.reply(200, {'users': [public_user(uid, a) | {'sid': a['sid'],
                        'upn': a['upn'], 'inScope': a['inScope']} for uid, a in accounts.items()]})
                name = query.get('username', [''])[0] if self.command == 'GET' else data.get('username')
                if path == '/api/admin/access':
                    target = accounts.get(name) if isinstance(name, str) else None
                    if not target:
                        raise AdminError(404, '请选择已同步的 Windows 用户')
                    policies = Policies()
                    if self.command == 'GET':
                        items = policies.matrix(); selection = selection_for(target, items)
                        identities = {g.casefold() for g in target.get('groups', [])}
                        group_grants = [{'itemId': i['Id'], 'Path': i['Path'], 'assignment': a}
                            for i in items for a in i['policies'] if a['GroupUserName'].casefold() in identities]
                        return self.reply(200, {'user': public_user(name, target), 'selection': selection,
                            'items': [{k: i[k] for k in ('Id', 'Name', 'Path', 'Type')} |
                                      {'policyReadError': i.get('policyReadError', False)} for i in items],
                            'groupGrants': group_grants})
                    if target['role'] == 'admin' or not target['enabled']:
                        raise AdminError(400, '管理员或停用用户不允许在此修改绑定')
                    selection = {'folderIds': data.get('folderIds'), 'reportIds': data.get('reportIds')}
                    if any(not isinstance(v, list) or len(v) > 1000 or
                           any(not isinstance(i, str) for i in v) for v in selection.values()):
                        raise AdminError(400, '目录或报表列表不正确')
                    target['accessSelection'] = selection
                    from ad_integration import DIRECTORY
                    policies.replace_selection(target['principal'], selection['folderIds'], selection['reportIds'],
                                               True, lambda: atomic_json(DIRECTORY, state))
                    return self.reply(200, {'ok': True, 'message': '直接绑定已保存；AD 组继承权限独立生效'})
                if path == '/api/admin/rls/user' and self.command == 'GET':
                    return self.reply(200, AdRls().user_inventory(name, accounts))
                if path == '/api/admin/rls/batch' and self.command == 'POST':
                    return self.reply(200, AdRls().save_many(data, accounts))
            raise AdminError(404, '接口不存在；Windows 用户不在 Demo 中创建、改密或启停')
        except AdminError as error:
            self.reply(error.status, {'error': str(error)})
        except (ValueError, TypeError, KeyError):
            self.reply(400, {'error': '请求或配置格式不正确'})
        except Exception:
            self.reply(502, {'error': 'Windows / PBIRS 读取或写入未确认，请检查服务日志和连接配置'})


def background_sync():
    while True:
        time.sleep(max(60, int(os.environ.get('P6_AD_SYNC_SECONDS', '300'))))
        try:
            sync_directory()
        except Exception:
            print('Windows account sync failed; last complete directory retained', flush=True)


def main():
    if os.environ.get('P6_AUTH_MODE') != 'windows':
        raise SystemExit('Set P6_AUTH_MODE=windows; this entry point does not use Forms authentication')
    key = base64.b64decode(os.environ['P6_GATEWAY_KEY'], validate=True)
    if len(key) < 32:
        raise SystemExit('Gateway key must contain at least 32 random bytes')
    # Fail before opening the listener if dependencies or initial AD sync fail.
    sync_directory()
    server = ThreadingHTTPServer(('127.0.0.1', int(os.environ.get('P6_BACKEND_PORT', '8766'))), Handler)
    server.gateway_key = key
    threading.Thread(target=background_sync, daemon=True).start()
    print('Windows backend listening on loopback; no user passwords stored', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
