import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import demo_identity as auth
from demo_admin import AdminError, password_record
from ad_integration import merge_directory


class DemoIdentityTests(unittest.TestCase):
    def setUp(self):
        self.record = {'principal': 'PC\\a1','sid':'sid1','enabled':True,'role':'viewer',
                       'demoLogin':'demo-a1','demoPassword':password_record('independent-demo-password'),
                       'demoVersion':1, 'windowsCredential':'opaque-encrypted-credential'}
        self.state={'users':{'sid1':self.record}}
        auth.SESSIONS.clear();auth.ATTEMPTS.clear()

    def test_demo_login_uses_independent_password_and_rejects_windows_password(self):
        with patch.object(auth, 'directory', return_value=self.state):
            with self.assertRaises(AdminError):auth.login('demo-a1','different-windows-password','peer')
            token,user=auth.login('demo-a1','independent-demo-password','peer')
            self.assertEqual(auth.identity(token)[0],'sid1')
            self.assertTrue(user['hasWindowsCredential'])
            self.assertNotIn('windowsCredential',user)
            self.assertNotIn('demoPassword',user)
            self.assertEqual(user['loginName'],'demo-a1')

    def test_password_reset_or_disabled_source_invalidates_demo_session(self):
        with patch.object(auth,'directory',return_value=self.state):
            token,_=auth.login('demo-a1','independent-demo-password','peer')
            self.record['demoVersion']+=1
            with self.assertRaises(AdminError):auth.identity(token)
            self.record['demoVersion']=1;token,_=auth.login('demo-a1','independent-demo-password','peer')
            self.record['enabled']=False
            with self.assertRaises(AdminError):auth.identity(token)

    def test_sync_does_not_replace_demo_password_or_windows_credential(self):
        source={'id':'sid1','sid':'sid1','principal':'PC\\a1','displayName':'renamed display',
                'enabled':True,'groups':[]}
        updated=merge_directory(self.state,[source],set())['users']['sid1']
        self.assertEqual(updated['demoPassword'],self.record['demoPassword'])
        self.assertEqual(updated['windowsCredential'],self.record['windowsCredential'])

    def test_missing_windows_credential_never_uses_service_account(self):
        with self.assertRaises(AdminError) as error:auth.credential_session('sid1',{'principal':'PC\\a1'})
        self.assertEqual(error.exception.status,409)

    def test_wrong_windows_identity_is_not_saved(self):
        response=type('Response',(),{'status_code':200,'json':lambda self:{'Username':'PC\\someone-else'}})()
        with patch.dict('os.environ',{'P4_PBIRS_URL':'http://pbirs.example.internal'}), \
             patch.object(auth,'directory',return_value=self.state), \
             patch.object(auth.requests,'Session') as session, patch.object(auth,'atomic_json') as write:
            session.return_value.get.return_value=response
            with self.assertRaises(AdminError):auth.set_windows_password('sid1','windows-password')
            write.assert_not_called()

if __name__=='__main__':unittest.main()
