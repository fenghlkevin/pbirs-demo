import copy,json,sys
from pathlib import Path
import requests
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from ticket_auth import BASE,establish
from rls_admin import canonical
ROOT=Path(__file__).resolve().parent.parent;URL=BASE+':8765';RID=json.loads((ROOT/'rls-demo/published.json').read_text())['report']
s=requests.Session();s.trust_env=False
s.post(URL+'/api/login',json=json.loads((ROOT/'demo-admin-login.local.json').read_text()),timeout=60).raise_for_status()
def inventory():
 r=s.get(URL+'/api/admin/rls/user',params={'username':'demo1'},timeout=120);r.raise_for_status();return r.json()
def batch(changes):
 return s.post(URL+'/api/admin/rls/batch',json={'username':'demo1','changes':changes},timeout=120)
native,_=establish('p4:maintenance')
def actual(rid):
 r=native.get(BASE+'/Reports/api/v2.0/PowerBIReports('+rid+')/DataModelRoleAssignments',timeout=60);r.raise_for_status();return r.json()['value']
def change(r,ids):return {'reportId':r['Id'],'revision':r['revision'],'roleIds':ids}
data=inventory();assert all(r['status']=='ok' for r in data['reports'])
r=next(r for r in data['reports'] if r['Id']==RID);second=next(i for i in data['reports'] if i['Id']!=RID and i['roles']);original=actual(RID);other=actual(second['Id']);roles={i['Name']:i['Id'] for i in r['roles']};old=r['roleIds']
try:
 out=batch([change(r,[roles['Province_B']]),change(second,second['roleIds'])]);out.raise_for_status();assert out.json()['complete'],out.text;assert len(out.json()['results'])==2
 assert next(i['DataModelRoles'] for i in actual(RID) if i['GroupUserName']=='p4:demo1')==[roles['Province_B']]
 assert canonical([i for i in actual(RID) if i['GroupUserName']!='p4:demo1'])==canonical([i for i in original if i['GroupUserName']!='p4:demo1'])
 assert canonical(actual(second['Id']))==canonical(other)
 stale=batch([change(r,old)]);assert stale.status_code==409,stale.text
 print('Two-report batch confirmed; other users/report unchanged; stale batch rejected',flush=True)
finally:
 current=next(i for i in inventory()['reports'] if i['Id']==RID);restore=batch([change(current,old)]);restore.raise_for_status();assert restore.json()['complete']
assert canonical(actual(RID))==canonical(original)
for who in [None,'demo1']:
 c=requests.Session();c.trust_env=False
 if who:c.post(URL+'/api/login',json={'username':who,'password':json.loads((ROOT/'app-logins.local.json').read_text())[who]['password']},timeout=60).raise_for_status()
 expected=401 if who is None else 403
 assert c.get(URL+'/api/admin/rls/user?username=demo1',timeout=60).status_code==expected
 assert c.post(URL+'/api/admin/rls/batch',json={},timeout=60).status_code==expected
print('Batch identities isolated; original complete assignments restored',flush=True)
