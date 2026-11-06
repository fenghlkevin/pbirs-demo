import base64,json
from pathlib import Path
from ticket_auth import BASE,establish
s,_=establish('p4:maintenance');API=BASE+'/Reports/api/v2.0'
def call(method,path,data=None):
 r=s.request(method,API+path,json=data,timeout=120);print(method,path,r.status_code,flush=True)
 if not r.ok:print(r.text[:1800]);r.raise_for_status()
 return r.json() if r.content else None
folder=call('POST','/Folders',{'Name':'P6_RLS_Demo','Path':'/P6_RLS_Demo'})
Path('rls-demo/published.json').write_text(json.dumps({'folder':folder['Id']}))
report=call('POST','/PowerBIReports',{'Name':'Province_RLS_Demo','Path':'/P6_RLS_Demo/Province_RLS_Demo','ContentType':'application/octet-stream','Content':base64.b64encode(Path('rls-demo/Province_RLS_Demo.pbix').read_bytes()).decode()})
Path('rls-demo/published.json').write_text(json.dumps({'folder':folder['Id'],'report':report['Id']}))
print(call('GET','/PowerBIReports('+report['Id']+')/DataModelRoles'))
