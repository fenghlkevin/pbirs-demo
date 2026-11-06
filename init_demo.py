"""Create fresh local-only demo identities and an HMAC key; never contact PBIRS."""
import base64
import hashlib
import json
import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def create(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)

def main():
    names = ['ticket-signing.local.json', 'app-accounts.local.json',
             'app-logins.local.json', 'demo-admin-login.local.json', 'admin-login.local.json']
    if any((ROOT / name).exists() for name in names):
        raise SystemExit('Local configuration already exists. Refusing to overwrite credentials.')
    accounts, logins = {}, {}
    for name in ['demo1', 'demo2', 'demo3', 'admin', 'p4admin']:
        password = secrets.token_urlsafe(24)
        salt = secrets.token_hex(16)
        admin = name in ('admin', 'p4admin')
        principal = 'p4:portaladmin' if name == 'p4admin' else 'p4:' + name
        accounts[name] = {'salt': salt, 'iterations': 600000,
                         'passwordHash': hashlib.pbkdf2_hmac('sha256', password.encode(),
                                                          bytes.fromhex(salt), 600000).hex(),
                         'principal': principal, 'role': 'admin' if admin else 'viewer',
                         'enabled': True, 'displayName': name, 'version': 1}
        logins[name] = {'password': password, 'principal': principal}
    create(ROOT / names[0], {'key': base64.b64encode(secrets.token_bytes(32)).decode()})
    create(ROOT / names[1], accounts)
    create(ROOT / names[2], logins)
    create(ROOT / names[3], {'username': 'admin', **logins['admin']})
    create(ROOT / names[4], {'username': 'p4admin', **logins['p4admin']})
    print('Created fresh local configuration with mode 0600. No passwords printed.')
    print('No PBIRS policies or Windows/AD accounts were created.')

if __name__ == '__main__':
    main()
