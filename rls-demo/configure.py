import json
from pathlib import Path
import requests
from ticket_auth import BASE,establish
ROOT=Path(__file__).resolve().parent.parent;id=json.loads((ROOT/'rls-demo/published.json').read_text())['report']
admin=requests.Session();admin.trust_env=False
r=admin.post(BASE+':8765/api/login',json=json.loads((ROOT/'demo-admin-login.local.json').read_text()),timeout=60);r.raise_for_status()
for name in ['demo1','demo2','demo3']:
 r=admin.get(BASE+':8765/api/admin/access',params={'username':name},timeout=60);r.raise_for_status();selection=r.json()['selection'];selection['reportIds']=list(dict.fromkeys(selection['reportIds']+[id]))
 r=admin.post(BASE+':8765/api/admin/access',json={'username':name,**selection},timeout=120);r.raise_for_status();print(name,'resource access added',flush=True)
s,_=establish('p4:maintenance');api=BASE+'/Reports/api/v2.0/PowerBIReports('+id+')'
roles=s.get(api+'/DataModelRoles',timeout=60).json()['value'];by_name={r['ModelRoleName']:r['ModelRoleId'] for r in roles}
assignments=[{'GroupUserName':'p4:demo1','DataModelRoles':[by_name['Province_A']]},{'GroupUserName':'p4:demo2','DataModelRoles':[by_name['Province_B']]},{'GroupUserName':'p4:demo3','DataModelRoles':[by_name['Province_A'],by_name['Province_B']]}]
# Keep administration usable without granting any administrator identity to viewers.
for p in ['p4:portaladmin','p4:maintenance']:assignments.append({'GroupUserName':p,'DataModelRoles':list(by_name.values())})
r=s.put(api+'/DataModelRoleAssignments',json=assignments,timeout=60);print('RLS assignment',r.status_code,r.text[:1000]);r.raise_for_status()
r=s.get(api+'/DataModelRoleAssignments',timeout=60);r.raise_for_status();(ROOT/'rls-demo/assignments.json').write_text(json.dumps(r.json(),indent=2));print('Assignments verified',flush=True)
