import copy,json,sys
from pathlib import Path
import requests
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from ticket_auth import BASE,establish
from rls_admin import canonical
ROOT=Path(__file__).resolve().parent.parent;URL=BASE+':8765';RID=json.loads((ROOT/'rls-demo/published.json').read_text())['report'];TEMPLATE=json.loads((ROOT/'rls-demo/query-template.json').read_text())
def session():
 s=requests.Session();s.trust_env=False;return s
def login(info):
 s=session();r=s.post(URL+'/api/login',json=info,timeout=60);r.raise_for_status();return s
admin=login(json.loads((ROOT/'demo-admin-login.local.json').read_text()));ordinary=login({'username':'demo1','password':json.loads((ROOT/'app-logins.local.json').read_text())['demo1']['password']})
for path in ['/api/admin/rls/catalog','/api/admin/rls/reports','/api/admin/rls?reportId='+RID]:
 assert ordinary.get(URL+path,timeout=60).status_code==403
 assert session().get(URL+path,timeout=60).status_code==401
assert ordinary.post(URL+'/api/admin/rls',json={},timeout=60).status_code==403
r=admin.get(URL+'/api/admin/rls/catalog',timeout=120);r.raise_for_status();catalog=r.json();assert not catalog['failedCount'],catalog
report=next(i for i in catalog['reports'] if i['Id']==RID);assert {r['Name'] for r in report['roles']}=={'Province_A','Province_B'}
assert any(not r['roles'] for r in catalog['reports']);print('All-report RLS inventory, no-role reports and admin API isolation passed',flush=True)
def view():
 r=admin.get(URL+'/api/admin/rls',params={'reportId':RID},timeout=60);r.raise_for_status();return r.json()
def save(ids,revision=None):
 current=view();r=admin.post(URL+'/api/admin/rls',json={'reportId':RID,'username':'demo1','roleIds':ids,'revision':revision or current['revision']},timeout=60);return r
native,_=establish('p4:maintenance');endpoint=BASE+'/Reports/api/v2.0/PowerBIReports('+RID+')/DataModelRoleAssignments'
r=native.get(endpoint);r.raise_for_status();original=r.json()['value'];original_user=next(a['DataModelRoles'] for a in original if a['GroupUserName']=='p4:demo1');others=[a for a in original if a['GroupUserName']!='p4:demo1']
viewer,_=establish('p4:demo1')
def query():
 r=viewer.get(BASE+'/powerbi/api/explore/reports/'+RID+'/modelsAndExploration?preferReadOnlySession=true',timeout=60);r.raise_for_status();data=copy.deepcopy(TEMPLATE);data['modelId']=r.json()['models'][0]['id']
 r=viewer.post(BASE+'/powerbi/api/explore/reports/'+RID+'/querydata',json=data,timeout=60);r.raise_for_status();return [i['C'] for i in r.json()['results'][0]['result']['data']['dsr']['DS'][0]['PH'][0]['DM0']]
initial=view();roles={r['Name']:r['Id'] for r in initial['roles']};assert query()==[['A',600]]
try:
 r=save([roles['Province_B']]);r.raise_for_status();assert query()==[['B',1500]]
 assert canonical([a for a in native.get(endpoint).json()['value'] if a['GroupUserName']!='p4:demo1'])==canonical(others)
 r=save(original_user,initial['revision']);assert r.status_code==409,r.text;assert query()==[['B',1500]]
 r=save(['not-a-role']);assert r.status_code==400,r.text
 r=admin.post(URL+'/api/admin/rls',json={'reportId':RID,'username':'admin','roleIds':[],'revision':view()['revision']});assert r.status_code==400
 print('Demo save changes real data A600 to B1500; others preserved; stale/invalid/protected writes rejected',flush=True)
 r=save([]);r.raise_for_status()
 try:query();raise AssertionError('Unassigned RLS user unexpectedly read data')
 except requests.HTTPError as error:assert error.response.status_code in (401,403)
 print('Removing all model roles rejects data query',flush=True)
finally:
 r=save(original_user);r.raise_for_status()
assert query()==[['A',600]]
assert canonical(native.get(endpoint).json()['value'])==canonical(original)
(ROOT/'rls-management/verification.json').write_text(json.dumps({'catalogReportCount':len(catalog['reports']),'catalogRoleCount':catalog['roleCount'],'aToBAndRestore':True,'othersPreserved':True,'staleWriteRejected':True,'unassignedDenied':True},indent=2))
print('Original A role restored; exact full native assignment list preserved',flush=True)
