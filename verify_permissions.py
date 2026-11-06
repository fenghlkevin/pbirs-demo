import json
from pathlib import Path
from ticket_auth import establish,BASE
reports=json.loads(Path('demo-manifest.json').read_text());results=[]
for name in ('demo1','demo2','demo3'):
 s,me=establish('p4:'+name);assert me['Username']=='p4:'+name
 base=BASE+'/Reports/api/v2.0'
 catalog=s.get(base+'/Folders(98130126-1a80-474d-a151-d20bb2678de4)/CatalogItems');catalog.raise_for_status()
 visible=[r['Path'] for r in catalog.json().get('value',[]) if r.get('Type')=='PowerBIReport']
 expected={r['path'] for r in reports if name.replace('demo','a') in r['allowed']}
 assert set(visible)==expected,(name,visible,expected)
 for r in reports:
  metadata=s.get(base+f"/PowerBIReports({r['id']})")
  model=s.get(BASE+'/powerbi/api/explore/reports/'+r['id']+'/modelsAndExploration?preferReadOnlySession=true')
  allowed=name.replace('demo','a') in r['allowed']
  assert metadata.ok==allowed,(name,metadata.status_code)
  assert model.ok==allowed,(name,model.status_code)
  results.append({'user':me['Username'],'report':r['path'],'allowed':allowed,'metadataStatus':metadata.status_code,'modelStatus':model.status_code})
 print(name,'identity and permissions passed',visible)
Path('verification-results.json').write_text(json.dumps(results,indent=2))
print('P4 identity permission matrix passed without Windows accounts')
