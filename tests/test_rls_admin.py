import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from rls_admin import RlsAdmin,revision,canonical
from demo_admin import AdminError
REPORT='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';A='11111111-1111-4111-8111-111111111111';B='22222222-2222-4222-8222-222222222222'
ACCOUNTS={'demo1':{'principal':'p4:demo1'},'demo2':{'principal':'p4:demo2'},'admin':{'principal':'p4:admin','role':'admin'},'off':{'principal':'p4:off','enabled':False}}
class Fake:
 def __init__(self):
  self.roles=[{'ModelRoleId':A,'ModelRoleName':'A'},{'ModelRoleId':B,'ModelRoleName':'B'}]
  self.assignments=[{'GroupUserName':'p4:demo1','DataModelRoles':[A]},{'GroupUserName':'p4:demo2','DataModelRoles':[B]},{'GroupUserName':'p4:maintenance','DataModelRoles':[A,B]}];self.writes=[];self.fail=False
 def catalog(self):return [{'Id':REPORT,'Name':'R','Path':'/R','Type':'PowerBIReport'}]
 @staticmethod
 def policy_path(r):return '/Policies'
 def read(self,path):return {'Policies':[{'GroupUserName':'p4:demo1','Roles':[{'Name':'Browser'}]}]}
 def call(self,method,path,payload=None):
  if path.endswith('/DataModelRoles'):return {'value':copy.deepcopy(self.roles)}
  if method=='GET':return {'value':copy.deepcopy(self.assignments)}
  self.writes.append(copy.deepcopy(payload))
  if self.fail:raise RuntimeError('upstream failure')
  self.assignments=copy.deepcopy(payload)
class Test(unittest.TestCase):
 def setUp(self):self.p=Fake();self.r=RlsAdmin(self.p)
 def data(self,ids):return {'reportId':REPORT,'username':'demo1','roleIds':ids,'revision':revision(self.p.roles,self.p.assignments)}
 def test_replace_preserves_others_and_view_is_actual(self):
  other=copy.deepcopy(self.p.assignments[1:]);out=self.r.save(self.data([B]),ACCOUNTS)
  self.assertEqual(self.p.assignments[:2],other);self.assertEqual(next(a for a in out['assignments'] if a['username']=='demo1')['roleIds'],[B]);self.assertTrue(next(u for u in out['users'] if u['username']=='demo1')['hasReportAccess'])
 def test_clear_only_selected_user(self):
  self.r.save(self.data([]),ACCOUNTS);self.assertEqual({a['GroupUserName'] for a in self.p.assignments},{'p4:demo2','p4:maintenance'})
 def test_stale_revision_no_write(self):
  data=self.data([B]);self.p.assignments[1]['DataModelRoles']=[A]
  with self.assertRaises(AdminError) as e:self.r.save(data,ACCOUNTS)
  self.assertEqual(e.exception.status,409);self.assertEqual(self.p.writes,[])
 def test_invalid_or_protected_user_no_write(self):
  for change in [{'roleIds':['bad-id']},{'username':'admin'},{'username':'off'},{'reportId':'bad-id'},{'reportId':'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'}]:
   with self.subTest(change=change):
    with self.assertRaises(AdminError):self.r.save({**self.data([A]),**change},ACCOUNTS)
  self.assertEqual(self.p.writes,[])
 def test_upstream_failure_never_reports_success(self):
  self.p.fail=True
  with self.assertRaises(AdminError) as e:self.r.save(self.data([B]),ACCOUNTS)
  self.assertEqual(e.exception.status,502)
 def test_read_no_roles(self):
  self.p.roles=[];out=self.r.view(REPORT,ACCOUNTS);self.assertEqual(out['roles'],[])
class BatchTest(unittest.TestCase):
 def test_preflight_checks_all_before_writing(self):
  p=Fake();r=RlsAdmin(p);rev=revision(p.roles,p.assignments)
  with self.assertRaises(AdminError):r.save_many({'username':'demo1','changes':[{'reportId':REPORT,'revision':rev,'roleIds':[B]},{'reportId':'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb','revision':rev,'roleIds':[B]}]},ACCOUNTS)
  self.assertEqual(p.writes,[])
 def test_batch_preserves_other_members(self):
  p=Fake();r=RlsAdmin(p);others=copy.deepcopy(p.assignments[1:])
  out=r.save_many({'username':'demo1','changes':[{'reportId':REPORT,'revision':revision(p.roles,p.assignments),'roleIds':[B]}]},ACCOUNTS)
  self.assertTrue(out['complete']);self.assertEqual(p.assignments[:2],others)
 def test_partial_failure_is_reported(self):
  class Stub(RlsAdmin):
   def save(self,data,accounts,validate_only=False):
    if validate_only:return
    if data['reportId']=='second':raise AdminError(502,'failed')
    return {'revision':'new'}
  out=Stub(Fake()).save_many({'username':'demo1','changes':[{'reportId':'first'},{'reportId':'second'}]},ACCOUNTS)
  self.assertFalse(out['complete']);self.assertEqual([r['status'] for r in out['results']],['saved','error'])
 def test_duplicate_report_rejected(self):
  p=Fake()
  with self.assertRaises(AdminError):RlsAdmin(p).save_many({'username':'demo1','changes':[{'reportId':REPORT},{'reportId':REPORT}]},ACCOUNTS)
  self.assertEqual(p.writes,[])
if __name__=='__main__':unittest.main()
