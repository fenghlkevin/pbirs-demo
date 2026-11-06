"""Demo login with per-user Windows-authenticated PBIRS viewing."""
import base64
import hashlib
import gzip
from http.cookies import SimpleCookie
import hmac
import json
import os
import secrets
import socket
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
from report_export import operation, check_export_access, download_disposition
from demo_identity import (login, identity, public_account, credential_session,
                           set_demo_password, set_windows_password, import_demo_passwords, SESSIONS, LOCK, TTL)

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
    protocol_version = "HTTP/1.1"
    def log_message(self, *args):
        pass

    def reply(self, status, data, kind='application/json; charset=utf-8', cookie=None, static=False, disposition=None):
        raw = json.dumps(data, ensure_ascii=False).encode() if not isinstance(data, bytes) else data
        compressed = len(raw) > 1024 and 'gzip' in self.headers.get('Accept-Encoding', '') and any(
            value in kind for value in ('text/', 'javascript', 'json', 'svg'))
        if compressed:
            raw = gzip.compress(raw, compresslevel=6)
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'private, max-age=3600' if static else 'no-store')
        if compressed:self.send_header('Content-Encoding', 'gzip')
        self.send_header('Vary', 'Accept-Encoding')
        if cookie:self.send_header('Set-Cookie', cookie)
        if disposition:self.send_header('Content-Disposition', disposition)
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
            if not 0 <= size <= 16 * 1024 * 1024:
                raise AdminError(413, '请求过大')
            raw = self.rfile.read(size)
            path = urlsplit(self.path).path; query = parse_qs(urlsplit(self.path).query)
            origin = os.environ['P6_PUBLIC_URL'].rstrip('/')
            if self.command == 'POST' and self.headers.get('Origin') != origin:
                raise AdminError(403, '请求来源不匹配')
            if path in ('/tree.js', '/app.js') and self.command == 'GET':
                return self.reply(200, (ROOT / 'ad' / path[1:]).read_bytes(), 'text/javascript; charset=utf-8')
            if path == '/' and self.command == 'GET':
                return self.reply(200, (ROOT / 'ad/index.html').read_bytes(), 'text/html; charset=utf-8')
            # Viewer query bodies can exceed management JSON size and have a different schema.
            proxy_path = path.lower().startswith(('/reports/', '/powerbi/', '/reportserver/'))
            data = {} if proxy_path else (json.loads(raw) if raw else {})
            if not isinstance(data, dict):
                raise AdminError(400, '请求内容不正确')
            cookies = SimpleCookie(self.headers.get('Cookie', ''))
            token = cookies['p6_demo_session'].value if 'p6_demo_session' in cookies else ''
            secure = '; Secure' if origin.startswith('https:') else ''
            if path == '/api/login' and self.command == 'POST':
                new_token, user = login(data.get('username'), data.get('password'), self.client_address[0])
                with LOCK:SESSIONS.pop(token, None)
                return self.reply(200, user, cookie='p6_demo_session='+new_token+
                    '; HttpOnly; SameSite=Strict; Path=/; Max-Age='+str(TTL)+secure)
            uid, account = identity(token)
            state = directory(); accounts = state['users']
            if path == '/api/logout' and self.command == 'POST':
                with LOCK:SESSIONS.pop(token, None)
                return self.reply(200, {'ok': True}, cookie='p6_demo_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'+secure)
            if proxy_path:
                request_operation = operation(path)
                if self.command == 'POST' and not request_operation:
                    raise AdminError(403, '仅允许浏览、查询报表及导出 CSV / Excel')
                exporting = bool(request_operation and request_operation['format'])
                upstream = os.environ['P4_PBIRS_URL'].rstrip('/')
                headers = {key: value for key, value in self.headers.items() if key.lower() in
                    ('content-type','accept','accept-language','x-requested-with','requestverificationtoken',
                     'activityid','requestid') or key.lower().startswith('x-powerbi-')}
                viewer = credential_session(uid, account)
                if exporting:
                    check_export_access(viewer, upstream, request_operation['id'])
                response = viewer.request(self.command, upstream+self.path,
                    headers=headers, data=raw or None, timeout=120, allow_redirects=False)
                if response.is_redirect:
                    destination=response.headers.get('Location', '')
                    if destination.startswith(upstream+'/'):destination=destination[len(upstream):]
                    if not destination.startswith('/') or destination.startswith('//'):
                        raise AdminError(502, '报表返回了不受信任的跳转')
                    self.send_response(response.status_code);self.send_header('Location', destination)
                    self.send_header('Content-Length','0');self.end_headers();return
                if response.status_code in (401,403):
                    raise AdminError(403, '当前用户的 Windows 身份无权查看此报表或数据；请检查资源和 RLS 绑定')
                disposition=download_disposition(response.headers.get('Content-Disposition'))
                content=response.content;kind=response.headers.get('Content-Type','application/octet-stream')
                if not exporting and not disposition and any(value in kind for value in ('text/','javascript','json')):
                    content=content.replace(upstream.encode(), origin.encode())
                static=self.command=='GET' and path.lower().startswith(('/reports/assets/','/powerbi/libs/','/powerbi/assets/'))
                return self.reply(response.status_code,content,kind,static=static and not exporting,disposition=disposition)
            if path == '/api/me' and self.command == 'GET':
                return self.reply(200, {**public_account(uid, account),
                    'pbirsUrl': os.environ['P4_PBIRS_URL'].rstrip('/'), 'authentication': 'Demo', 'reportAuthentication': 'Windows'})
            if path == '/api/catalog' and self.command == 'GET':
                if not account.get('windowsCredential'):
                    return self.reply(200, {'value': [], 'credentialRequired': True})
                viewer=credential_session(uid, account);visible=[]
                for item in Policies().catalog():
                    if item['Path']=='/':continue
                    endpoint=Policies.policy_path(item).removesuffix('/Policies')
                    response=viewer.get(os.environ['P4_PBIRS_URL'].rstrip('/')+'/Reports/api/v2.0'+endpoint,
                                        timeout=35,allow_redirects=False)
                    if response.status_code==200:visible.append(item)
                return self.reply(200, {'value': visible})
            if not path.startswith('/api/admin/'):
                raise AdminError(404, '接口不存在')
            if account['role'] != 'admin':
                raise AdminError(403, '需要 Demo 管理员权限')
            if path == '/api/admin/ad' and self.command == 'GET':
                return self.reply(200, directory_status())
            if path == '/api/admin/ad/sync' and self.command == 'POST':
                return self.reply(200, sync_directory())
            if path == '/api/admin/demo-password' and self.command == 'POST':
                set_demo_password(data.get('username'), data.get('password'))
                return self.reply(200, {'ok': True})
            if path == '/api/admin/windows-credential' and self.command == 'POST':
                set_windows_password(data.get('username'), data.get('password'))
                return self.reply(200, {'ok': True})
            with MUTATION_LOCK:
                state = directory(); accounts = state['users']
                if path == '/api/admin/users' and self.command == 'GET':
                    return self.reply(200, {'users': [public_account(uid, a) for uid, a in accounts.items()]})
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


class DemoServer(ThreadingHTTPServer):
    # Windows SO_REUSEADDR can otherwise let stale workers share one port.
    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def main():
    if os.environ.get('P6_AUTH_MODE') != 'windows':
        raise SystemExit('Set P6_AUTH_MODE=windows for the PBIRS connection')
    # Fail before opening the listener if dependencies or initial AD sync fail.
    sync_directory()
    import_demo_passwords()
    server = DemoServer(('127.0.0.1', int(os.environ.get('P6_BACKEND_PORT', '8766'))), Handler)
    threading.Thread(target=background_sync, daemon=True).start()
    print('Demo login backend listening on loopback; PBIRS remains Windows authenticated', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
