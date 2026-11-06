import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from demo_admin import Policies,AdminError
P='p4:test'
def entry(p):return {'GroupUserName':p,'Roles':[{'Name':'Browser'}]}
class Fake(Policies):
 def __init__(self):
  self.items=[{'Id':i,'Path':path,'Name':path,'Type':kind,'inherits':inherit,'policies':[entry('p4:other')]} for i,path,kind,inherit in [
   ('root','/','Folder',False),('f','/F','Folder',False),('a','/F/A','PowerBIReport',False),
   ('s','/F/Sub','Folder',True),('b','/F/Sub/B','PowerBIReport',True),('o','/Other','PowerBIReport',True)]]
  self.writes=[];self.fail=None
 def matrix(self):return copy.deepcopy(self.items)
 def call(self,method,path,payload=None):
  self.writes.append((path,copy.deepcopy(payload)))
  if self.fail==len(self.writes):raise AdminError(502,'injected')
  item=next(i for i in self.items if self.policy_path(i)==path)
  item.update(inherits=payload['InheritParentPolicy'],policies=copy.deepcopy(payload['Policies']))
class Test(unittest.TestCase):
 def test_folder_covers_independent_and_leaves_native_inheritance(self):
  p=Fake();p.replace_selection(P,['f'],[],True,lambda:None)
  self.assertEqual({path for path,_ in p.writes},{'/Folders(root)/Policies','/Folders(f)/Policies','/PowerBIReports(a)/Policies','/PowerBIReports(o)/Policies'})
  self.assertTrue(all(entry('p4:other') in item['policies'] for item in p.items))
 def test_single_report_adds_navigation_but_denies_siblings(self):
  p=Fake();p.replace_selection(P,[],['b'],True,lambda:None)
  self.assertEqual({path for path,_ in p.writes},{'/Folders(root)/Policies','/Folders(f)/Policies','/PowerBIReports(o)/Policies'})
  self.assertNotIn(entry(P),p.items[2]['policies']);self.assertNotIn(entry(P),p.items[5]['policies'])
  self.assertFalse(p.items[5]['inherits'])
  self.assertLess([path for path,_ in p.writes].index('/PowerBIReports(o)/Policies'),[path for path,_ in p.writes].index('/Folders(root)/Policies'))
  self.assertTrue(p.items[4]['inherits'])
 def test_rollback(self):
  p=Fake();before=copy.deepcopy(p.items);p.fail=2
  with self.assertRaises(AdminError):p.replace_selection(P,['f'],[],True,lambda:None)
  self.assertEqual(before,p.items)
 def test_invalid_ids_no_writes(self):
  p=Fake()
  with self.assertRaises(AdminError):p.replace_selection(P,['a'],[],True,lambda:None)
  self.assertEqual([],p.writes)
if __name__=='__main__':unittest.main()
