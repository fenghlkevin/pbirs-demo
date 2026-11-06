import json,sys,copy,html
from pathlib import Path
from html.parser import HTMLParser
import requests
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from ticket_auth import BASE,establish
ROOT=Path(__file__).resolve().parent.parent
class Form(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.action=None;self.values={}
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='form':self.action=a.get('action')
  if tag=='input' and 'name' in a:self.values[a['name']]=a.get('value','')
def parse(r):
 f=Form();f.feed(r.text);assert f.action;return f
native,_=establish('p4:maintenance');rid=json.loads((ROOT/'rls-demo/published.json').read_text())['report'];endpoint=BASE+'/Reports/api/v2.0/PowerBIReports('+rid+')/DataModelRoleAssignments';before=native.get(endpoint).json()
for lang in ['pt-AO','zh-CN']:
 s=requests.Session();s.trust_env=False
 r=s.get(BASE+'/ReportServer/P4Login.aspx',params={'lang':lang,'returnUrl':'/Reports'},timeout=60);r.raise_for_status();assert "lang='"+lang+"'" in r.text
 assert ('Entrar com a sua conta' if lang=='pt-AO' else '登录系统账号') in r.text
 assert r.headers['Content-Language']==lang
 form=parse(r);assert form.values['lang']==lang
 invalid=s.post(BASE+form.action,data={**form.values,'csrf':'invalid','username':'demo1','password':'invalid'},timeout=60);assert invalid.status_code==403
 assert ('O pedido de início' if lang=='pt-AO' else '登录请求已失效') in html.unescape(invalid.text)
 form=parse(s.get(BASE+'/ReportServer/P4Login.aspx',params={'lang':lang},timeout=60))
 info=json.loads((ROOT/'app-logins.local.json').read_text())['demo1'];form.values.update(username='demo1',password=info['password'])
 r=s.post(BASE+form.action,data=form.values,timeout=60);r.raise_for_status();assert ('Sessão iniciada' if lang=='pt-AO' else '已登录') in r.text
 bridge=parse(r);r=s.post(BASE+bridge.action,data=bridge.values,allow_redirects=False,timeout=60);assert r.status_code==303
 me=s.get(BASE+'/Reports/api/v2.0/me',timeout=30);me.raise_for_status();assert me.json()['Username']=='p4:demo1'
 assert s.get(BASE+"/Reports/api/v2.0/Folders(Path='/')/CatalogItems",timeout=30).status_code==200
 anon=requests.Session();anon.trust_env=False
 err=anon.get(BASE+':8765/api/admin/users',headers={'Accept-Language':lang},timeout=30);assert err.status_code==401
 assert ('Inicie sessão' if lang=='pt-AO' else '请先登录') in err.json()['error']
 print(lang,'native login, CSRF protection, portal navigation, API errors passed',flush=True)
assert native.get(endpoint).json()==before
print('RLS assignments unchanged',flush=True)
