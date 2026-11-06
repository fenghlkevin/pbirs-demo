"""End-to-end shared-login and native-portal checks, using independent browser cookies."""
import json,time
from pathlib import Path
from html.parser import HTMLParser
import requests
from ticket_auth import BASE,issue_ticket
class Form(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.action=None;self.values={}
 def handle_starttag(self,tag,attributes):
  attributes=dict(attributes)
  if tag=='form':self.action=attributes.get('action')
  if tag=='input' and 'name' in attributes:self.values[attributes['name']]=attributes.get('value','')
def form(response):
 parsed=Form();parsed.feed(response.text);assert parsed.action is not None,(response.status_code,response.text[:100]);return parsed
users=json.loads(Path('app-logins.local.json').read_text());admin=json.loads(Path('admin-login.local.json').read_text());users['p4admin']=admin
sessions={};report_ids=json.loads(Path('demo-manifest.json').read_text())
for name,info in users.items():
 s=requests.Session();s.trust_env=False
 r=s.get(BASE+'/ReportServer/P4Login.aspx',params={'ReturnUrl':'/ReportServer/localredirect?url=%252fReports'},timeout=30)
 assert r.status_code==200 and '/P4Login.aspx' in r.url,(name,r.status_code,r.url)
 login=form(r);login.values.update(username=name,password=info['password'])
 r=s.post(BASE+login.action,data=login.values,timeout=60);assert r.status_code==200,(name,r.status_code)
 bridge=form(r);assert bridge.action=='/ReportServer/P4Login.aspx'
 r=s.post(BASE+bridge.action,data=bridge.values,allow_redirects=False,timeout=30)
 assert r.status_code==303,(name,r.status_code,r.text[:100])
 expected='/Reports' if name=='p4admin' else '/Reports/browse/P4_Identity_Demo'
 assert r.headers['Location']==expected,(name,r.headers.get('Location'))
 me=s.get(BASE+'/Reports/api/v2.0/me',timeout=30);assert me.ok and me.json()['Username']==info['principal']
 sessions[name]=s
 print(name,'native browser session:',me.json()['Username'],'return:',expected)
# Native APIs enforce the same read and management boundaries as the embedded demo.
root='09a9c3aa-f589-4f42-8025-44a0918c124d';api=BASE+'/Reports/api/v2.0'
assert sessions['demo1'].get(api+'/PowerBIReports('+report_ids[1]['id']+')').status_code==403
assert sessions['demo2'].get(api+'/PowerBIReports('+report_ids[0]['id']+')').status_code==403
assert sessions['demo1'].get(api+f'/Folders({root})/Policies').status_code==403
assert sessions['p4admin'].get(api+f'/Folders({root})/Policies').status_code==200
name='P4_Portal_Admin_Verify_'+str(int(time.time()))
created=sessions['p4admin'].post(api+'/Folders',json={'Name':name,'Path':'/'+name},timeout=30);created.raise_for_status();folder=created.json()['Id']
try:
 assert sessions['demo1'].post(api+'/Folders',json={'Name':name+'_denied','Path':'/'+name+'_denied'},timeout=30).status_code==403
finally:
 removed=sessions['p4admin'].delete(api+f'/Folders({folder})',timeout=30);removed.raise_for_status()
print('Administrator can manage native resources; ordinary users cannot; temporary folder removed')
# Deep-link return and open-redirect protection are enforced after ticket verification.
for target,expected in [('/Reports/powerbi/P4_Identity_Demo/Report_A?rs:embed=true','/Reports/powerbi/P4_Identity_Demo/Report_A?rs:embed=true'),('https://example.com','/Reports/browse/P4_Identity_Demo'),('//example.com','/Reports/browse/P4_Identity_Demo'),('/Reports/../../evil','/Reports/browse/P4_Identity_Demo')]:
 r=sessions['demo1'].post(BASE+'/ReportServer/P4Login.aspx',data={'ticket':issue_ticket('p4:demo1',browser=True,return_url=target)},allow_redirects=False,timeout=30)
 assert r.status_code==303 and r.headers['Location']==expected,(target,r.status_code,r.headers.get('Location'))
anonymous=requests.Session();anonymous.trust_env=False
assert anonymous.post(BASE+'/ReportServer/P4Login.aspx',data={'username':'demo1','password':'wrong'},timeout=30).status_code==403
print('Native deep links, redirect protection and login CSRF rejection passed')
