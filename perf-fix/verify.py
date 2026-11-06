import json,time,copy
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parent.parent;BASE='http://pbirs.example.internal:8765';rid=json.loads((ROOT/'rls-demo/published.json').read_text())['report'];creds=json.loads((ROOT/'app-logins.local.json').read_text());template=json.loads((ROOT/'rls-demo/query-template.json').read_text())
def session():
 s=requests.Session();s.trust_env=False;return s
expected={'demo1':[['A',600]],'demo2':[['B',1500]],'demo3':[['A',600],['B',1500]]};stats={}
for name,rows in expected.items():
 s=session();r=s.post(BASE+'/api/login',json={'username':name,'password':creds[name]['password']},timeout=60);r.raise_for_status()
 r=s.get(BASE+'/powerbi/api/explore/reports/'+rid+'/modelsAndExploration?preferReadOnlySession=true',timeout=90);r.raise_for_status();assert r.headers.get('Cache-Control')=='no-store'
 payload=copy.deepcopy(template);payload['modelId']=r.json()['models'][0]['id'];r=s.post(BASE+'/powerbi/api/explore/reports/'+rid+'/querydata',json=payload,timeout=90);r.raise_for_status();assert r.headers.get('Cache-Control')=='no-store'
 actual=[v['C'] for v in r.json()['results'][0]['result']['data']['dsr']['DS'][0]['PH'][0]['DM0']];assert actual==rows,(name,actual)
 print(name,'proxy RLS and no-store passed',actual,flush=True)
 if name=='demo1':
  path='/powerbi/libs/scripts/reportServerHostModern.js';t=time.monotonic();asset=s.get(BASE+path,timeout=120);asset.raise_for_status();elapsed=time.monotonic()-t
  assert asset.raw.version==11;assert asset.headers.get('Content-Encoding')=='gzip';assert asset.headers['Cache-Control']=='private, max-age=3600'
  stats={'mainScriptDecodedBytes':len(asset.content),'mainScriptWireBytes':int(asset.headers['Content-Length']),'requestSeconds':round(elapsed,3),'serverTiming':asset.headers.get('Server-Timing')}
  repeat=s.get(BASE+path,headers={'If-None-Match':asset.headers['ETag']},timeout=30);assert repeat.status_code==304 and not repeat.content
  assert session().get(BASE+path,timeout=30).status_code==401
  logout=s.post(BASE+'/api/logout',json={},timeout=30);logout.raise_for_status();assert s.get(BASE+'/powerbi/api/explore/reports/'+rid+'/modelsAndExploration',timeout=30).status_code==401
  print('gzip, HTTP1.1, private static cache, ETag, anonymous rejection and logout passed',stats,flush=True)
(ROOT/'perf-fix/verification.json').write_text(json.dumps(stats,indent=2))
