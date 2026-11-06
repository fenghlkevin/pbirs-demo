import base64
import copy
import hashlib
import hmac
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from ad_integration import merge_directory
from ad_server import verify_gateway, NONCES, visible_items, AdRls
from demo_admin import AdminError
from rls_rules import rules_for
from test_rls_admin import Fake, REPORT, A, B, revision


class WindowsTests(unittest.TestCase):
    def record(self, **kwargs):
        return {'id': 'sid-one', 'sid': 'S-1-5-21-1', 'principal': 'PC\\a1',
                'displayName': 'One', 'enabled': True, 'groups': [], **kwargs}

    def test_sync_keeps_bindings_and_marks_missing_inactive(self):
        previous = {'users': {'sid-one': self.record(accessSelection={'folderIds': [], 'reportIds': ['R']}),
                              'gone': self.record(id='gone', principal='PC\\gone')}}
        out = merge_directory(previous, [self.record(displayName='New name')], set())
        self.assertEqual(out['users']['sid-one']['accessSelection']['reportIds'], ['R'])
        self.assertFalse(out['users']['gone']['enabled'])
        self.assertTrue(previous['users']['gone']['enabled'])
        self.assertNotIn('passwordHash', out['users']['sid-one'])

    def test_sync_rejects_empty_rename_duplicate_without_mutation(self):
        previous = {'users': {'sid-one': self.record()}}
        before = copy.deepcopy(previous)
        for records in [[], [self.record(principal='PC\\renamed')], [self.record(), self.record()]]:
            with self.assertRaises(AdminError):
                merge_directory(previous, records, set())
        self.assertEqual(previous, before)

    def test_admin_role_only_from_server_config(self):
        out = merge_directory({'users': {}}, [self.record(role='admin')], set())
        self.assertEqual(out['users']['sid-one']['role'], 'viewer')

    def test_sync_filters_missing_local_group_values(self):
        out = merge_directory({'users': {}}, [self.record(groups=[None, '', 'PC\\Users'])], set())
        self.assertEqual(out['users']['sid-one']['groups'], ['PC\\Users'])

    def test_legacy_windows_policy_is_never_overwritten(self):
        from test_folder_policies import Fake as FolderFake
        p = FolderFake(); p.items[2]['policyReadError'] = True
        with self.assertRaises(AdminError):
            p.replace_selection('PC\\a1', [], ['a'], True, lambda: None)
        self.assertEqual(p.writes, [])

    def signed(self):
        key = b'x' * 32
        headers = {'X-P6-Time': str(int(time.time())), 'X-P6-Nonce': 'a' * 32,
                   'X-P6-User': base64.b64encode(b'PC\\a1').decode()}
        message = '\n'.join(['POST', '/api/admin/access', headers['X-P6-Time'],
                             headers['X-P6-Nonce'], headers['X-P6-User'], hashlib.sha256(b'{}').hexdigest()])
        headers['X-P6-Signature'] = hmac.new(key, message.encode(), hashlib.sha256).hexdigest()
        return headers, key

    def test_gateway_binds_identity_body_path_and_rejects_replay(self):
        NONCES.clear(); headers, key = self.signed()
        for path, body in [('/api/admin/rls/batch', b'{}'), ('/api/admin/access', b'{"admin":true}')]:
            with self.assertRaises(AdminError):
                verify_gateway(headers, 'POST', path, body, key)
        self.assertEqual(verify_gateway(headers, 'POST', '/api/admin/access', b'{}', key), 'PC\\a1')
        with self.assertRaises(AdminError):
            verify_gateway(headers, 'POST', '/api/admin/access', b'{}', key)

    def test_gateway_rejects_stale_or_unsigned_headers(self):
        NONCES.clear(); headers, key = self.signed()
        with self.assertRaises(AdminError):
            verify_gateway(headers, 'POST', '/api/admin/access', b'{}', key, now=time.time()+60)
        with self.assertRaises(AdminError):
            verify_gateway({'X-P6-User': 'PC\\Administrator'}, 'GET', '/', b'', key)

    def test_windows_rls_replaces_case_insensitive_user_preserves_groups(self):
        p = Fake(); p.assignments[0]['GroupUserName'] = 'pc\\A1'
        p.assignments.append({'GroupUserName': 'PC\\RegionalGroup', 'DataModelRoles': [A]})
        account = {'u': self.record()}
        with patch.dict(os.environ, {'P6_AUTH_MODE': 'windows'}):
            AdRls(p).save({'reportId': REPORT, 'username': 'u', 'roleIds': [B],
                          'revision': revision(p.roles, p.assignments)}, account)
        direct = [a for a in p.assignments if a['GroupUserName'].casefold() == 'pc\\a1']
        self.assertEqual(len(direct), 1)
        self.assertEqual(direct[0]['DataModelRoles'], [B])
        self.assertIn({'GroupUserName': 'PC\\RegionalGroup', 'DataModelRoles': [A]}, p.assignments)

    def test_rules_validate_report_revision_and_age(self):
        p = Fake(); original = p.call
        p.call = lambda method, path, payload=None: {'ModifiedDate': 'revision-one'} if path.endswith(')') else original(method, path, payload)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'rules.json'
            snapshot = {'reports': {REPORT: {'modifiedDate': 'revision-one', 'capturedAt': time.time(),
                'roles': {A: {'name': 'A', 'rules': [{'table': 'Sales', 'expression': '[Province] = "A"'}]},
                          B: {'name': 'B', 'rules': []}}}}}
            path.write_text(json.dumps(snapshot))
            with patch.dict(os.environ, {'P6_RULES_PATH': str(path)}):
                self.assertEqual(rules_for(p, REPORT, p.roles)[A]['rules'][0]['table'], 'Sales')
                snapshot['reports'][REPORT]['modifiedDate'] = 'old'
                path.write_text(json.dumps(snapshot))
                self.assertEqual(rules_for(p, REPORT, p.roles)[A]['ruleStatus'], 'unavailable')
                snapshot['reports'][REPORT].update(modifiedDate='revision-one', capturedAt=0)
                path.write_text(json.dumps(snapshot))
                self.assertEqual(rules_for(p, REPORT, p.roles)[A]['ruleStatus'], 'unavailable')


if __name__ == '__main__':
    unittest.main()
