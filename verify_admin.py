import json,os,secrets,time
from pathlib import Path
import requests
from ticket_auth import establish,BASE
from demo_admin import Policies,AdminError
ROOT=Path(__file__).resolve().parent;URL='http://127.0.0.1:8765'
def session():
 s=requests.Session();s.trust_env=False;return s
def login(name,password):
 s=session();r=s.post(URL+'/api/login',json={'username':name,'password':password});assert r.ok,(name,r.status_code,r.text);return s
admin_info=json.loads((ROOT/'demo-admin-login.local.json').read_text());admin=login(admin_info['username'],admin_info['password'])
listing=admin.get(URL+'/api/admin/users');assert listing.ok
assert 'passwordHash' not in listing.text and 'salt' not in listing.text
assert any(u['username']=='admin' and u['role']=='admin' for u in listing.json()['users'])
old=json.loads((ROOT/'app-logins.local.json').read_text())['demo1'];ordinary=login('demo1',old['password'])
assert ordinary.get(URL+'/api/admin/users').status_code==403
assert ordinary.post(URL+'/api/admin/users',json={'username':'baduser'}).status_code==403
assert session().get(URL+'/api/admin/users').status_code==401
policies=Policies();reports=policies.reports();assert len(reports)>=2
A,B=reports[:2];name='review_'+secrets.token_hex(3);password='User!'+secrets.token_urlsafe(14)
r=admin.post(URL+'/api/admin/users',json={'username':name,'displayName':'授权验证用户','password':password,'role':'admin','principal':'p4:portaladmin'});assert r.status_code==201,r.text
user=r.json()['user'];principal=user['principal'];assert user['role']=='viewer' and principal not in ('p4:portaladmin','p4:maintenance','p4:admin')
assert admin.post(URL+'/api/admin/users',json={'username':name,'password':password}).status_code==409
assert admin.post(URL+'/api/admin/users',json={'username':'invalid/name','password':password}).status_code==400
viewer=login(name,password);native,_=establish(principal)
def visible(s):
 response=s.get(URL+'/api/reports');assert response.ok,response.text;return {r['Id'] for r in response.json()['value']}
def native_status(report):return native.get(BASE+'/Reports/api/v2.0/PowerBIReports('+report['Id']+')').status_code
def grant(ids):
 r=admin.post(URL+'/api/admin/access',json={'username':name,'reportIds':ids});assert r.ok,r.text
assert visible(viewer)==set();assert native_status(A)==403
assert viewer.get(URL+'/api/admin/access?username='+name).status_code==403
print('Created unprivileged user; default deny and admin API isolation passed',flush=True)
grant([A['Id']]);assert visible(viewer)=={A['Id']};assert native_status(A)==200 and native_status(B)==403
r=admin.post(URL+'/api/admin/access',json={'username':name,'reportIds':['unknown-report']});assert r.status_code==400
assert visible(viewer)=={A['Id']}
grant([]);assert visible(viewer)==set() and native_status(A)==403
print('Grant and revoke enforced in PBIRS, including already-authenticated native session',flush=True)
grant([A['Id']])
r=admin.post(URL+'/api/admin/users/'+name+'/status',json={'enabled':False});assert r.ok,r.text
assert viewer.get(URL+'/api/me').status_code==401
assert session().post(URL+'/api/login',json={'username':name,'password':password}).status_code==401
assert native_status(A)==403
assert admin.post(URL+'/api/admin/access',json={'username':name,'reportIds':[]}).status_code==400
assert admin.post(URL+'/api/admin/users/admin/status',json={'enabled':False}).status_code==400
r=admin.post(URL+'/api/admin/users/'+name+'/status',json={'enabled':True});assert r.ok,r.text
viewer=login(name,password);assert visible(viewer)=={A['Id']} and native_status(A)==200
new_password='Reset!'+secrets.token_urlsafe(14)
r=admin.post(URL+'/api/admin/users/'+name+'/password',json={'password':new_password});assert r.ok
assert viewer.get(URL+'/api/me').status_code==401
assert session().post(URL+'/api/login',json={'username':name,'password':password}).status_code==401
viewer=login(name,new_password);assert visible(viewer)=={A['Id']}
print('Disable/re-enable, native permission removal, password reset and session revocation passed',flush=True)
# Fail the second remote write to verify that the first policy mutation is compensated.
p=Policies();before=p.matrix();original=p.call;count=[0];committed=[False]
def fail_second(method,path,payload=None):
 if method=='PUT':
  count[0]+=1
  if count[0]==2:raise AdminError(502,'Injected write failure')
 return original(method,path,payload)
p.call=fail_second
try:
 p.replace_viewer(principal,[B['Id']],True,lambda:committed.__setitem__(0,True));raise AssertionError('Expected failure')
except AdminError:pass
assert not committed[0] and visible(viewer)=={A['Id']}
after=Policies().matrix()
def normalized(items):
 return {r['Id']:sorted((x['GroupUserName'],tuple(sorted(y['Name'] for y in x['Roles']))) for x in r['policies']) for r in items}
assert normalized(before)==normalized(after),'Policy rollback changed another user'
print('Remote policy failure rollback passed; other users preserved',flush=True)
creds=ROOT/'demo-review-login.local.json';fd=os.open(creds,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
with os.fdopen(fd,'w') as f:json.dump({'username':name,'password':new_password,'displayName':'授权验证用户','grantedReport':A['Name']},f,ensure_ascii=False,indent=2)
print('All user-management and PBIRS authorization checks passed; example credentials saved locally',flush=True)
