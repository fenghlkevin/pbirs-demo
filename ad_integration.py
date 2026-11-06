"""Read-only LDAPS directory sync and native Windows PBIRS control plane."""
import copy
import json
import os
import ssl
import subprocess
import time
import uuid
from pathlib import Path

import requests
from demo_admin import AdminError, MUTATION_LOCK, atomic_json

ROOT = Path(__file__).resolve().parent
DIRECTORY = Path(os.environ.get('P6_DIRECTORY_PATH', str(ROOT / 'ad-directory.local.json')))


def windows_session():
    # Uses the Windows service's existing logon token, never a report viewer token.
    from requests_negotiate_sspi import HttpNegotiateAuth
    session = requests.Session()
    session.trust_env = False
    session.auth = HttpNegotiateAuth()
    return session


def directory():
    return json.loads(DIRECTORY.read_text(encoding='utf-8-sig')) if DIRECTORY.exists() else {'users': {}, 'syncedAt': None}


def read_ad():
    from ldap3 import Server, Connection, Tls, SIMPLE, SUBTREE
    host = os.environ.get('P6_AD_HOST', '')
    base = os.environ.get('P6_AD_BASE_DN', '')
    domain = os.environ.get('P6_AD_NETBIOS', '')
    bind = os.environ.get('P6_AD_BIND_USER', '')
    password = os.environ.get('P6_AD_BIND_PASSWORD', '')
    if not all((host, base, domain, bind, password)):
        raise AdminError(503, '请配置 AD 域控、Base DN、NetBIOS 域名和只读绑定账号')
    tls = Tls(validate=ssl.CERT_REQUIRED, version=ssl.PROTOCOL_TLS_CLIENT,
              ca_certs_file=os.environ.get('P6_AD_CA_FILE') or None)
    server = Server(host, port=int(os.environ.get('P6_AD_PORT', '636')), use_ssl=True,
                    tls=tls, connect_timeout=10)
    conn = Connection(server, user=bind, password=password, authentication=SIMPLE,
                      auto_bind=True, receive_timeout=30, raise_exceptions=True)
    records = []; group_names = {}
    try:
        # Fixed user filter: no write operations, no user-supplied LDAP syntax.
        entries = list(conn.extend.standard.paged_search(base,
            '(&(objectCategory=person)(objectClass=user))', SUBTREE,
            attributes=['objectGUID', 'objectSid', 'sAMAccountName', 'userPrincipalName',
                        'displayName', 'userAccountControl', 'tokenGroups'],
            paged_size=500, generator=True))
        if conn.result.get('result', 0) != 0:
            raise ValueError('AD user search did not complete')
        for entry in entries:
            if entry['type'] != 'searchResEntry':
                continue
            a = entry['attributes']; raw = entry.get('raw_attributes', {})
            guid = str(uuid.UUID(bytes_le=raw['objectGUID'][0]))
            # tokenGroups is a constructed attribute; request with a BASE search
            # on this exact user to include nested and primary security groups.
            from ldap3 import BASE
            conn.search(entry['dn'], '(objectClass=*)', BASE, attributes=['tokenGroups'])
            if not conn.entries:
                raise ValueError('Cannot read AD user security groups')
            groups = conn.entries[0].entry_raw_attributes.get('tokenGroups', [])
            if isinstance(groups, (str, bytes)):
                groups = [groups]
            from ldap3.protocol.formatters.formatters import format_sid
            names = ['Everyone', 'NT AUTHORITY\\Authenticated Users']
            sids = []
            for g in groups:
                sid = format_sid(g) if isinstance(g, bytes) else str(g)
                sids.append(sid)
                if sid not in group_names:
                    if not isinstance(g, bytes):
                        raise ValueError('Expected binary AD security group SID')
                    escaped = ''.join('\\%02x' % b for b in g)
                    conn.search(base, '(objectSid=' + escaped + ')', SUBTREE,
                                attributes=['sAMAccountName'])
                    group_names[sid] = [domain + '\\' + str(e.sAMAccountName) for e in conn.entries]
                names.extend(group_names[sid])
            records.append({'id': guid, 'sid': str(a['objectSid']),
                'principal': domain + '\\' + str(a['sAMAccountName']),
                'upn': str(a.get('userPrincipalName') or ''),
                'displayName': str(a.get('displayName') or a['sAMAccountName']),
                'enabled': not bool(int(a['userAccountControl']) & 2), 'groupSids': sids, 'groups': sorted(set(names))})
        if conn.result.get('result', 0) != 0:
            raise ValueError('AD search did not complete')
        return records
    finally:
        conn.unbind()


def read_local_users():
    script = ROOT / 'ad/read-local-users.ps1'
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-File', str(script)],
                            capture_output=True, timeout=90)
    if result.returncode:
        raise AdminError(502, '读取 Windows 本地用户失败，现有账号和绑定未修改')
    data = json.loads(result.stdout.decode('utf-8-sig'))
    return data['users']


def merge_directory(previous, records, admins):
    """Commit only complete, unambiguous snapshots; GUID anchors bindings."""
    users = copy.deepcopy(previous.get('users', {})); seen = set(); principals = set()
    counts = {'added': 0, 'updated': 0, 'inactive': 0}
    for record in records:
        uid = record['id']; principal = record['principal']
        if uid in seen or principal.casefold() in principals:
            raise AdminError(409, '账号源返回重复身份，本次同步未保存')
        seen.add(uid); principals.add(principal.casefold())
        old = users.get(uid, {})
        if old and (old['principal'].casefold() != principal.casefold() or old['sid'] != record['sid']):
            raise AdminError(409, 'Windows 账号标识已更名或变化，请迁移原 PBIRS 授权后再同步')
        counts['updated' if old else 'added'] += 1
        record = {**record, 'groups': [g for g in record.get('groups', []) if isinstance(g, str) and g]}
        users[uid] = {**old, **record, 'username': uid,
                      'role': 'admin' if principal.casefold() in admins else 'viewer',
                      'source': record.get('source', 'AD'), 'inScope': True}
    # A suspicious empty snapshot never deactivates the entire known directory.
    if not seen and users:
        raise AdminError(409, '账号源返回空目录，本次未覆盖现有用户')
    for uid, user in users.items():
        if uid not in seen:
            user.update(enabled=False, inScope=False); counts['inactive'] += 1
    return {'users': users, 'syncedAt': time.time(), 'summary': counts}


def sync_directory():
    # No local changes if LDAP paging/group expansion fails partway through.
    records = read_local_users() if os.environ.get('P6_DIRECTORY_SOURCE', 'local') == 'local' else read_ad()
    admins = {x.strip().casefold() for x in os.environ.get('P6_WINDOWS_ADMINS', os.environ.get('P6_AD_ADMINS', '')).split(';') if x.strip()}
    with MUTATION_LOCK:
        updated = merge_directory(directory(), records, admins)
        atomic_json(DIRECTORY, updated)
    return {'syncedAt': updated['syncedAt'], **updated['summary'], 'total': len(updated['users'])}


def directory_status():
    state = directory()
    return {'source': os.environ.get('P6_DIRECTORY_SOURCE', 'local'), 'host': os.environ.get('P6_AD_HOST', ''), 'baseDN': os.environ.get('P6_AD_BASE_DN', ''),
            'domain': os.environ.get('P6_AD_NETBIOS', ''), 'syncedAt': state['syncedAt'],
            'total': len(state['users']), 'summary': state.get('summary'),
            'intervalSeconds': int(os.environ.get('P6_AD_SYNC_SECONDS', '300'))}
