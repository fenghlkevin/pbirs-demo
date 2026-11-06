import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import requests
from ticket_auth import establish,BASE
from demo_admin import Policies,under
ROOT=Path(__file__).resolve().parent.parent
p=Policies();before=p.matrix();before_reports={i['Id']:{a['GroupUserName']:sorted(r['Name'] for r in a['Roles']) for a in i['policies']} for i in before if i['Type']!='Folder'}
s=requests.Session();s.trust_env=False;s.post(BASE+':8765/api/login',json=json.loads((ROOT/'demo-admin-login.local.json').read_text()),timeout=30).raise_for_status()
for name in ['demo1','demo2','demo3']:
 r=s.get(BASE+':8765/api/admin/access',params={'username':name},timeout=60);r.raise_for_status();selection=r.json()['selection']
 r=s.post(BASE+':8765/api/admin/access',json={'username':name,**selection},timeout=60);r.raise_for_status()
 current=s.get(BASE+':8765/api/admin/access',params={'username':name},timeout=60).json();assert current['selection']==selection
 native,_=establish('p4:'+name)
 home=native.get(BASE+"/Reports/api/v2.0/Folders(Path='/')/CatalogItems",timeout=30);home.raise_for_status()
 print(name,'Home browse',home.status_code,flush=True)
 for item in before:
  if item['Type']=='Folder':continue
  r=native.get(BASE+'/Reports/api/v2.0/PowerBIReports('+item['Id']+')',timeout=30)
  expected=name.replace('demo','p4:demo') in before_reports[item['Id']]
  assert (r.status_code==200)==expected,(name,item['Path'],expected,r.status_code)
 after=p.matrix();assert all({a['GroupUserName']:sorted(r['Name'] for r in a['Roles']) for a in i['policies']}==before_reports[i['Id']] for i in after if i['Type']!='Folder')
print('All report identities and effective grants unchanged; directory selections unchanged',flush=True)
