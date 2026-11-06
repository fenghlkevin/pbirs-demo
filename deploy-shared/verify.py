import json,secrets,sys
from pathlib import Path
from html.parser import HTMLParser
import requests
ROOT=Path(__file__).resolve().parent.parent
BASE='http://pbirs.example.internal';URL=BASE+':8765'
def session():
 s=requests.Session();s.trust_env=False;return s
class Form(HTMLParser):
 def __init__(self):super().__init__();self.values={}
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='input' and 'name' in a:self.values[a['name']]=a.get('value','')
def native(name,password,success=True):
 s=session();r=s.get(BASE+'/ReportServer/P4Login.aspx',timeout=30);assert r.status_code==200,(r.status_code,r.text[:150])
 f=Form();f.feed(r.text);f.values.update(username=name,password=password)
 r=s.post(BASE+'/ReportServer/P4Login.aspx',data=f.values,timeout=30)
 if not success:assert r.status_code==401,(r.status_code,r.text[:120]);return
 assert r.status_code==200,(r.status_code,r.text[:300]);f=Form();f.feed(r.text);assert 'ticket' in f.values,r.text[:300]
 r=s.post(BASE+'/ReportServer/P4Login.aspx',data=f.values,allow_redirects=False,timeout=30);assert r.status_code==303,r.text[:200]
 r=s.get(BASE+'/Reports/api/v2.0/me',timeout=30);assert r.ok,r.text[:200]
 return s,r.json()['Username']
info=json.loads((ROOT/'demo-admin-login.local.json').read_text());admin=session()
r=admin.post(URL+'/api/login',json=info,timeout=45);assert r.ok,(r.status_code,r.text[:200]);print('Shared Demo admin login passed',flush=True)
assert session().post(URL+'/internal/authenticate',json=info).status_code==403
native('admin',info['password']);print('PBIRS login through Demo API passed',flush=True)
name='unified_'+secrets.token_hex(3);password='Unified!'+secrets.token_urlsafe(12)
r=admin.post(URL+'/api/admin/users',json={'username':name,'password':password,'displayName':'统一账号验收用户'},timeout=45);assert r.status_code==201,r.text;principal=r.json()['user']['principal']
s,actual=native(name,password);assert actual==principal
A='17a6ac24-f1b4-4347-8b67-5046af70614d';B='7171bf30-077e-4192-b4a8-fd713e40b77a'
def status(id):return s.get(BASE+'/Reports/api/v2.0/PowerBIReports('+id+')',timeout=30).status_code
assert status(A)==403
r=admin.post(URL+'/api/admin/access',json={'username':name,'reportIds':[A]},timeout=90);assert r.ok,r.text
assert status(A)==200 and status(B)==403
print('New user immediately logs into PBIRS; grant A and deny B passed',flush=True)
new='Reset!'+secrets.token_urlsafe(12)
r=admin.post(URL+'/api/admin/users/'+name+'/password',json={'password':new},timeout=45);assert r.ok,r.text
native(name,password,False);native(name,new)
r=admin.post(URL+'/api/admin/users/'+name+'/status',json={'enabled':False},timeout=90);assert r.ok,r.text
native(name,new,False);assert status(A)==403
r=admin.post(URL+'/api/admin/users/'+name+'/status',json={'enabled':True},timeout=90);assert r.ok,r.text
native(name,new);assert status(A)==200
(ROOT/'unified-review-login.local.json').write_text(json.dumps({'username':name,'password':new,'principal':principal}))
(ROOT/'unified-review-login.local.json').chmod(0o600)
print('Reset, disable, enable and existing-session access enforcement passed',flush=True)
