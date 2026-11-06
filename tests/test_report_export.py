import json
import os
import threading
import unittest
from unittest.mock import Mock, patch
from http.server import ThreadingHTTPServer

import requests
from ad_server import Handler
from demo_admin import AdminError
from report_export import operation, check_export_access, download_disposition

RID='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'

class ExportRouteTests(unittest.TestCase):
    def test_only_native_read_and_export_operations_are_allowed(self):
        for suffix in ['querydata','conceptualschema','export/csv','export/xlsx']:
            self.assertEqual(operation('/powerbi/api/explore/reports/'+RID+'/'+suffix)['id'],RID)
        for suffix in ['export/pdf','export/xlsx/delete','delete','export/xlsx/../delete']:
            self.assertIsNone(operation('/powerbi/api/explore/reports/'+RID+'/'+suffix))
        self.assertIsNone(operation('/powerbi/api/explore/reports/not-a-uuid/export/csv'))
        self.assertIsNone(operation('/Reports/api/v2.0/PowerBIReports('+RID+')'))

    def test_failure_to_check_permissions_is_closed(self):
        for status in [401,403,404,500,302]:
            session=Mock();session.get.return_value.status_code=status
            with self.assertRaises(AdminError):check_export_access(session,'http://pbirs',RID)

    def test_filename_header_preserves_utf8_encoding_and_rejects_injection(self):
        value="attachment; filename*=UTF-8''%E6%8A%A5%E8%A1%A8.xlsx"
        self.assertEqual(download_disposition(value),value)
        self.assertIsNone(download_disposition('x\r\nInjected: yes'))

class ExportHttpTests(unittest.TestCase):
    def setUp(self):
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.url='http://127.0.0.1:'+str(self.server.server_port)
        self.worker=threading.Thread(target=self.server.serve_forever,daemon=True);self.worker.start()
        self.env=patch.dict(os.environ,{'P6_PUBLIC_URL':self.url,'P4_PBIRS_URL':'http://pbirs.example.internal'})
        self.env.start()
        self.account={'principal':'PC\\viewer','enabled':True,'role':'viewer'}
        self.identity=patch('ad_server.identity',return_value=('viewer-id',self.account));self.identity_mock=self.identity.start()
        self.directory=patch('ad_server.directory',return_value={'users':{'viewer-id':self.account}});self.directory.start()
        self.viewer=Mock();self.viewer.get.return_value.status_code=200
        self.response=Mock(status_code=200,is_redirect=False,content=b'PK\x03\x04xlsx-binary\x00\xff')
        self.response.headers={'Content-Type':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                               'Content-Disposition':"attachment; filename*=UTF-8''report.xlsx"}
        self.viewer.request.return_value=self.response
        self.credential=patch('ad_server.credential_session',return_value=self.viewer);self.credential_mock=self.credential.start()
        self.policies=patch('ad_server.Policies');self.policies_mock=self.policies.start()
    def tearDown(self):
        self.server.shutdown();self.server.server_close()
        for patcher in [self.env,self.identity,self.directory,self.credential,self.policies]:patcher.stop()
    def export(self,fmt='xlsx'):
        return requests.post(self.url+'/powerbi/api/explore/reports/'+RID+'/export/'+fmt,
            json={'exportDataType':0,'principal':'pretend-admin'},headers={'Origin':self.url},timeout=10)
    def test_download_is_checked_and_forwarded_with_same_user_session(self):
        r=self.export();self.assertEqual(r.status_code,200)
        self.assertEqual(r.content,self.response.content)
        self.assertEqual(r.headers['Content-Disposition'],self.response.headers['Content-Disposition'])
        self.assertEqual(r.headers['Cache-Control'],'no-store')
        self.credential_mock.assert_called_once_with('viewer-id',self.account)
        self.policies_mock.assert_not_called()
        self.assertEqual([call[0] for call in self.viewer.method_calls],['get','request'])
    def test_csv_cell_urls_are_not_rewritten(self):
        self.response.content=b'Link,Amount\r\nhttp://pbirs.example.internal,600\r\n'
        self.response.headers={'Content-Type':'text/csv; charset=utf-8','Content-Disposition':'attachment; filename="data.csv"'}
        r=self.export('csv');self.assertEqual(r.status_code,200);self.assertEqual(r.content,self.response.content)
    def test_revoked_report_blocks_export_before_file_generation(self):
        self.viewer.get.return_value.status_code=403
        r=self.export();self.assertEqual(r.status_code,403);self.viewer.request.assert_not_called()
        self.assertNotIn('Content-Disposition',r.headers)
    def test_rls_denial_from_native_server_is_not_returned_as_a_download(self):
        self.response.status_code=403
        r=self.export();self.assertEqual(r.status_code,403);self.assertNotIn('Content-Disposition',r.headers)
    def test_anonymous_export_has_no_upstream_session(self):
        self.identity_mock.side_effect=AdminError(401,'请先登录 Demo 系统')
        self.assertEqual(self.export().status_code,401);self.credential_mock.assert_not_called()
    def test_other_post_endpoints_remain_blocked(self):
        r=requests.post(self.url+'/Reports/api/v2.0/PowerBIReports',json={},headers={'Origin':self.url},timeout=10)
        self.assertEqual(r.status_code,403);self.credential_mock.assert_not_called()

if __name__=='__main__':unittest.main()
