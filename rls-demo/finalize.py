import json,requests
from pathlib import Path
from ticket_auth import BASE,establish
root=Path(__file__).resolve().parent;old=json.loads((root/'first-published.json').read_text())['report'];rid=json.loads((root/'published.json').read_text())['report']
a=requests.Session();a.trust_env=False;r=a.post(BASE+':8765/api/login',json=json.loads((root.parent/'demo-admin-login.local.json').read_text()),timeout=60);r.raise_for_status()
for name in ['demo1','demo2','demo3']:
 r=a.get(BASE+':8765/api/admin/access',params={'username':name},timeout=60);r.raise_for_status();selected=r.json()['selection'];selected['reportIds']=[i for i in selected['reportIds'] if i!=old]
 r=a.post(BASE+':8765/api/admin/access',json={'username':name,**selected},timeout=90);r.raise_for_status()
s,_=establish('p4:maintenance');api=BASE+'/Reports/api/v2.0/PowerBIReports'
r=s.delete(api+'('+old+')',timeout=60);r.raise_for_status()
r=s.patch(api+'('+rid+')',json={'Name':'Province_RLS_Demo','Path':'/P6_RLS_Demo/Province_RLS_Demo'},timeout=60);r.raise_for_status()
url=api+'('+rid+')'
r=s.get(url+'/Policies');r.raise_for_status();body=r.json();body={k:body[k] for k in ['InheritParentPolicy','Policies']}
body['Policies']=[e for e in body['Policies'] if e['GroupUserName']!='p4:admin']+[{'GroupUserName':'p4:admin','Roles':[{'Name':'Browser'}]}];body['InheritParentPolicy']=False
r=s.put(url+'/Policies',json=body);r.raise_for_status()
roles=s.get(url+'/DataModelRoles').json()['value'];assignments=s.get(url+'/DataModelRoleAssignments').json()['value'];assignments=[e for e in assignments if e['GroupUserName']!='p4:admin']+[{'GroupUserName':'p4:admin','DataModelRoles':[r['ModelRoleId'] for r in roles]}]
r=s.put(url+'/DataModelRoleAssignments',json=assignments);r.raise_for_status()
print('Removed draft, retained existing grants, enabled Demo administrator preview',flush=True)
