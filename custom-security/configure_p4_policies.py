import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ticket_auth import establish,BASE
s,identity=establish('p4:maintenance');print('Deployment identity:',identity['Username'])
def policy(names):return {'InheritParentPolicy':False,'Policies':[{'GroupUserName':'p4:maintenance','Roles':[{'Name':'Content Manager'}]}]+[{'GroupUserName':'p4:'+n,'Roles':[{'Name':'Browser'}]} for n in names]}
paths={'/Folders(98130126-1a80-474d-a151-d20bb2678de4)/Policies':['demo1','demo2','demo3']}
for r in json.loads(Path('demo-manifest.json').read_text()):paths[f"/PowerBIReports({r['id']})/Policies"]=[u.replace('a','demo') for u in r['allowed']]
for path,names in paths.items():
 r=s.put(BASE+'/Reports/api/v2.0'+path,json=policy(names),timeout=45);r.raise_for_status();print('Authorized',path,names)
print('P4 policies configured')
