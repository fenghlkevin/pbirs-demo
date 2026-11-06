import json,secrets,time,base64,sys
from pathlib import Path
import requests
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from ticket_auth import BASE,establish
from demo_admin import Policies
ROOT=Path(__file__).resolve().parent.parent;URL=BASE+':8765'
def sess():
 s=requests.Session();s.trust_env=False;return s
def post(s,path,data):
 r=s.post(URL+path,json=data,timeout=120);assert r.ok,(path,r.status_code,r.text[:400]);return r.json()
def get(s,path):
 r=s.get(URL+path,timeout=120);assert r.ok,(path,r.status_code,r.text[:400]);return r.json()
admin=sess();post(admin,'/api/login',json.loads((ROOT/'demo-admin-login.local.json').read_text()))
p=Policies();baseline=p.matrix();name='folders_'+secrets.token_hex(3);password='Folder!'+secrets.token_urlsafe(14)
user=post(admin,'/api/admin/users',{'username':name,'displayName':'目录授权验收用户','password':password})['user'];principal=user['principal']
viewer=sess();post(viewer,'/api/login',{'username':name,'password':password});native,_=establish(principal)
A='17a6ac24-f1b4-4347-8b67-5046af70614d';B='7171bf30-077e-4192-b4a8-fd713e40b77a';F='98130126-1a80-474d-a151-d20bb2678de4'
def status(i):return native.get(BASE+'/Reports/api/v2.0/PowerBIReports('+i+')',timeout=35).status_code
def grant(folders,reports):return post(admin,'/api/admin/access',{'username':name,'folderIds':folders,'reportIds':reports})
assert get(viewer,'/api/catalog')['value']==[]
grant([F],[]);assert status(A)==200 and status(B)==200
catalog=get(viewer,'/api/catalog')['value'];assert {i['Id'] for i in catalog}=={F,A,B},catalog
access=get(admin,'/api/admin/access?username='+name);assert access['selection']['folderIds']==[F]
print('Directory grant covers independently secured A/B; catalog is permission filtered',flush=True)
grant([],[A]);assert status(A)==200 and status(B)==403
catalog=get(viewer,'/api/catalog')['value'];assert {i['Id'] for i in catalog}=={F,A};assert next(i for i in catalog if i['Id']==F)['navigationOnly']
grant([F],[A]);grant([],[A]);assert status(A)==200 and status(B)==403
grant([],[]);assert status(A)==403 and get(viewer,'/api/catalog')['value']==[]
print('Single-report access does not expose siblings; overlapping grants and revoke passed',flush=True)
# Temporary nested folders and copied report verify native inheritance and reconciliation.
created=[]
def api(method,path,payload=None):
 r=p.session.request(method,BASE+'/Reports/api/v2.0'+path,json=payload,timeout=120);assert r.ok,(path,r.status_code,r.text[:400]);return r.json() if r.content else None
try:
 path='/P4_Folder_Verify_'+secrets.token_hex(3)
 folder=api('POST','/Folders',{'Name':path[1:],'Path':path});created.append(('Folders',folder['Id']))
 sub=api('POST','/Folders',{'Name':'Sub','Path':path+'/Sub'});created.append(('Folders',sub['Id']))
 # Explicitly retain maintenance access, independent of other catalog policies.
 for item in (folder,sub):api('PUT','/Folders('+item['Id']+')/Policies',{'InheritParentPolicy':False,'Policies':[{'GroupUserName':'p4:maintenance','Roles':[{'Name':'Content Manager'}]}]})
 content=p.session.get(BASE+'/Reports/api/v2.0/PowerBIReports('+A+')/Content/$value',timeout=60).content
 def report(name):
  item=api('POST','/PowerBIReports',{'Name':name,'Path':path+'/Sub/'+name,'Content':base64.b64encode(content).decode(),'ContentType':'application/octet-stream'});created.append(('PowerBIReports',item['Id']));return item
 nested=report('Nested_Report')
 grant([folder['Id']],[]);assert status(nested['Id'])==200
 print('Nested folder and report access passed',flush=True)
 new=report('Added_After_Grant')
 # Existing independent ACL must also be covered on the next reconciliation pass.
 api('PUT','/PowerBIReports('+new['Id']+')/Policies',{'InheritParentPolicy':False,'Policies':[{'GroupUserName':'p4:maintenance','Roles':[{'Name':'Content Manager'}]}]})
 deadline=time.monotonic()+85
 while status(new['Id'])!=200:
  assert time.monotonic()<deadline,'New independent report was not reconciled'
  time.sleep(3)
 print('New report after directory grant reconciled automatically',flush=True)
 post(admin,'/api/admin/users/'+name+'/status',{'enabled':False});assert status(nested['Id'])==403 and status(new['Id'])==403
 post(admin,'/api/admin/users/'+name+'/status',{'enabled':True});assert status(nested['Id'])==200
 grant([F],[])
finally:
 for kind,ident in reversed(created):api('DELETE','/'+kind+'('+ident+')')
# Every other subject/role on original resources must remain unchanged.
after={i['Id']:i for i in p.matrix()}
for item in baseline:
 def others(entries):return sorted((e['GroupUserName'],tuple(sorted(r['Name'] for r in e['Roles']))) for e in entries if e['GroupUserName']!=principal)
 assert others(item['policies'])==others(after[item['Id']]['policies']),item['Path']
(ROOT/'folder-review-login.local.json').write_text(json.dumps({'username':name,'password':password,'principal':principal}));(ROOT/'folder-review-login.local.json').chmod(0o600)
print('Disable/enable, temporary-resource cleanup and preservation of all other users passed',flush=True)
