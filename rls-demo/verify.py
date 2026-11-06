import copy,json
from pathlib import Path
from ticket_auth import BASE,establish
root=Path(__file__).resolve().parent
payload=json.loads((root/'query-template.json').read_text())
rid=json.loads((root/'published.json').read_text())['report']
expected={'demo1':[['A',600]],'demo2':[['B',1500]],'demo3':[['A',600],['B',1500]]}
results={}
def query(s):
 r=s.get(BASE+'/powerbi/api/explore/reports/'+rid+'/modelsAndExploration?preferReadOnlySession=true',timeout=90);r.raise_for_status();model=r.json()['models'][0]['id']
 data=copy.deepcopy(payload);data['modelId']=model
 r=s.post(BASE+'/powerbi/api/explore/reports/'+rid+'/querydata',json=data,timeout=90);r.raise_for_status();return r.json()
for name,rows in expected.items():
 s,me=establish('p4:'+name);out=query(s);raw=json.dumps(out)
 assert 'error' not in raw.lower(),(name,out)
 actual=[r['C'] for r in out['results'][0]['result']['data']['dsr']['DS'][0]['PH'][0]['DM0']]
 assert actual==rows,(name,actual,rows);results[name]={'principal':me['Username'],'provinceTotals':actual};print(name,actual,flush=True)
 # Direct detail query must enforce the same security, not just the chart.
 layout=json.loads((root/'report-layout.json').read_text());v=next(v for v in layout['sections'][0]['visualContainers'] if json.loads(v['config']).get('singleVisual',{}).get('visualType')=='tableEx')
 data=copy.deepcopy(payload);data['queries'][0]['Query']=json.loads(v['query']);r=s.post(BASE+'/powerbi/api/explore/reports/'+rid+'/querydata',json=data,timeout=90);r.raise_for_status();detail=r.json();text=json.dumps(detail);assert 'error' not in text.lower(),(name,detail)
 ds=detail['results'][0]['result']['data']['dsr']['DS'][0]
 assert set(ds['ValueDicts']['D0'])=={row[0] for row in rows},(name,ds)
 assert len(ds['PH'][1]['DM1'])==(6 if name=='demo3' else 3),(name,ds)
 (root/(name+'-detail.json')).write_text(json.dumps(detail,ensure_ascii=False,indent=2))
# A principal with Browser alone must not get unfiltered data from an RLS model.
admin,_=establish('p4:maintenance');api=BASE+'/Reports/api/v2.0/PowerBIReports('+rid+')/Policies'
r=admin.get(api);r.raise_for_status();original=r.json();body={k:original[k] for k in ('InheritParentPolicy','Policies')}
try:
 test=copy.deepcopy(body);test['InheritParentPolicy']=False;test['Policies'].append({'GroupUserName':'p4:rls_nomember','Roles':[{'Name':'Browser'}]})
 r=admin.put(api,json=test);r.raise_for_status()
 s,_=establish('p4:rls_nomember')
 try:
  out=query(s);assert 'error' in json.dumps(out).lower(),out
 except __import__('requests').HTTPError as error:
  assert error.response.status_code in (401,403),error.response.status_code
 print('Browser without RLS membership rejected at model query',flush=True)
finally:
 r=admin.put(api,json=body);r.raise_for_status()
(root/'verification.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print('RLS query verification passed',flush=True)
