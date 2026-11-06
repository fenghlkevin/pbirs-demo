"""Independent Demo sessions and per-user Windows credential storage."""
import base64
import hashlib
import hmac
import os
import secrets
import threading
import time
from pathlib import Path

import requests
from requests_ntlm import HttpNtlmAuth
from ad_integration import directory
from demo_admin import AdminError, MUTATION_LOCK, atomic_json, password_record

SESSIONS = {}; ATTEMPTS = {}; LOCK = threading.RLock(); LOCAL = threading.local()
TTL = 3600


def demo_name(account):
    return account.get('demoLogin') or account['principal'].split('\\')[-1]


def public_account(uid, account):
    from demo_admin import public_user
    return {**public_user(uid, account), 'loginName': demo_name(account),
            'hasDemoPassword': bool(account.get('demoPassword')),
            'hasWindowsCredential': bool(account.get('windowsCredential')),
            'sid': account['sid'], 'upn': account.get('upn', ''), 'inScope': account.get('inScope', True)}


def login(name, password, peer):
    if not isinstance(name, str) or not isinstance(password, str) or len(password) > 128:
        raise AdminError(401, 'Demo 账号或密码错误')
    now = time.time()
    with LOCK:
        recent = [t for t in ATTEMPTS.get((peer, name.casefold()), []) if now-t < 60]
        if len(recent) >= 10:
            raise AdminError(429, '登录尝试过多，请稍后重试')
        ATTEMPTS[(peer, name.casefold())] = recent + [now]
    matches = [(uid, a) for uid, a in directory()['users'].items()
               if name.casefold() in {demo_name(a).casefold(), a['principal'].casefold()}]
    account = matches[0][1] if len(matches) == 1 else None
    record = account.get('demoPassword', {}) if account else {}
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(record.get('salt', '00'*16)),
                                 record.get('iterations', 600000)).hex()
    if not account or not account.get('enabled') or not hmac.compare_digest(digest, record.get('passwordHash', '')):
        raise AdminError(401, 'Demo 账号或密码错误')
    token = secrets.token_urlsafe(32)
    with LOCK:
        ATTEMPTS.pop((peer, name.casefold()), None)
        SESSIONS[token] = {'uid': matches[0][0], 'expires': now + TTL,
                           'version': account.get('demoVersion', 0)}
    return token, public_account(matches[0][0], account)


def identity(token):
    with LOCK:
        session = SESSIONS.get(token)
        account = directory()['users'].get(session['uid']) if session else None
        if (session and account and account.get('enabled') and session['expires'] > time.time()
                and account.get('demoVersion', 0) == session['version']):
            return session['uid'], account
        SESSIONS.pop(token, None)
    raise AdminError(401, '请先登录 Demo 系统')


def set_demo_password(uid, password):
    record = password_record(password)
    from ad_integration import DIRECTORY
    with MUTATION_LOCK:
        state = directory(); account = state['users'].get(uid)
        if not account:
            raise AdminError(404, '用户不存在')
        account['demoPassword'] = record
        account['demoVersion'] = account.get('demoVersion', 0) + 1
        atomic_json(DIRECTORY, state)


def encrypt_password(uid, password):
    import win32crypt
    return base64.b64encode(win32crypt.CryptProtectData(password.encode(), 'P6 Windows viewer',
                              uid.encode(), None, None, 0)).decode()


def decrypt_password(uid, value):
    import win32crypt
    return win32crypt.CryptUnprotectData(base64.b64decode(value), uid.encode(), None, None, 0)[1].decode()


def credential_session(uid, account):
    value = account.get('windowsCredential')
    if not value:
        raise AdminError(409, '此用户尚未配置 Windows 报表凭据，请联系管理员')
    key = (uid, account.get('windowsVersion', 0))
    if not hasattr(LOCAL, 'connections'):
        LOCAL.connections = {}
    if key not in LOCAL.connections:
        password = decrypt_password(uid, value)
        s = requests.Session(); s.trust_env = False
        s.auth = HttpNtlmAuth(account['principal'], password)
        LOCAL.connections = {k: v for k, v in LOCAL.connections.items() if k[0] != uid}
        LOCAL.connections[key] = s
    return LOCAL.connections[key]


def set_windows_password(uid, password):
    if not isinstance(password, str) or not 1 <= len(password) <= 256:
        raise AdminError(400, '请输入有效的 Windows 密码')
    from ad_integration import DIRECTORY
    with MUTATION_LOCK:
        state = directory(); account = state['users'].get(uid)
        if not account or not account.get('enabled'):
            raise AdminError(400, '请选择已启用用户')
        s = requests.Session(); s.trust_env = False
        s.auth = HttpNtlmAuth(account['principal'], password)
        response = s.get(os.environ['P4_PBIRS_URL'].rstrip('/')+'/Reports/api/v2.0/me',
                         timeout=35, allow_redirects=False)
        if response.status_code != 200 or response.json().get('Username', '').casefold() != account['principal'].casefold():
            raise AdminError(400, 'Windows 凭据验证失败或返回身份不匹配，未保存')
        account['windowsCredential'] = encrypt_password(uid, password)
        account['windowsVersion'] = account.get('windowsVersion', 0) + 1
        atomic_json(DIRECTORY, state)


def import_demo_passwords():
    """One-time import of existing Demo password hashes, never Windows passwords."""
    import json
    source = os.environ.get('P6_DEMO_IMPORT_PATH')
    mapping = json.loads(os.environ.get('P6_DEMO_IMPORT_MAP', '{}'))
    if not source or not mapping:
        return
    from ad_integration import DIRECTORY
    with MUTATION_LOCK:
        previous = json.loads(Path(source).read_text(encoding='utf-8-sig'))
        state = directory(); changed = False
        for source_name, windows_name in mapping.items():
            old = previous.get(source_name)
            targets = [a for a in state['users'].values()
                       if a['principal'].split('\\')[-1].casefold() == windows_name.casefold()]
            if old and len(targets) == 1 and not targets[0].get('demoPassword'):
                targets[0]['demoPassword'] = {k: old[k] for k in ('salt','iterations','passwordHash')}
                targets[0]['demoLogin'] = source_name if targets[0]['role']=='admin' else windows_name
                targets[0]['demoVersion'] = 1; changed = True
        if changed:
            atomic_json(DIRECTORY, state)
