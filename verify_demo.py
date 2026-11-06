import json,requests,concurrent.futures
from pathlib import Path
users=json.loads(Path('app-logins.local.json').read_text());reports=json.loads(Path('demo-manifest.json').read_text());base='http://127.0.0.1:8765'
sessions={}
for name,info in users.items():
 s=requests.Session();s.trust_env=False
 r=s.post(base+'/api/login',json={'username':name,'password':info['password']});assert r.ok,(name,r.text)
 assert r.json()['pbirsIdentity']['Username']==info['principal']
 sessions[name]=s
 bad=s.post(base+'/api/login',json={'username':'Administrator','password':'invalid'});assert bad.status_code==401

def verify(name):
 s=sessions[name];visible=s.get(base+'/api/reports').json()['value'];assert {x['Path'] for x in visible}=={x['path'] for x in reports if name.replace('demo','a') in x['allowed']}
 for r in reports:
  response=s.get(base+'/powerbi/api/explore/reports/'+r['id']+'/modelsAndExploration?preferReadOnlySession=true')
  assert response.ok==(name.replace('demo','a') in r['allowed']),(name,r,response.status_code)
 return name+' isolated session and model permissions passed'
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
 for result in executor.map(verify,users):print(result)
s=sessions['demo1'];cookie=s.cookies.get('demo_session');assert s.post(base+'/api/logout').ok
s.cookies.set('demo_session',cookie);assert s.get(base+'/api/me').status_code==401
anon=requests.Session();anon.trust_env=False;assert anon.get(base+'/api/reports').status_code==401
assert sessions['demo2'].post(base+'/Reports/api/v2.0/Folders',json={}).status_code==403
print('Logout revocation, anonymous rejection, admin rejection, mutation rejection passed')

for name in ('a1','a2','a3','demo1'):
 response=anon.post(base+'/api/login',json={'username':name,'password':'wrong'})
 assert response.status_code==401
print('Windows logins and incorrect application password rejected')
# Client-supplied mapping fields cannot override the trusted server-side binding.
test=requests.Session();test.trust_env=False
r=test.post(base+'/api/login',json={'username':'demo1','password':users['demo1']['password'],'principal':users['demo2']['principal'],'windowsAccount':'a2'})
assert r.ok and r.json()['principal']==users['demo1']['principal']
assert 'password' not in r.text
assert test.get(base+'/api/me').json()['username']=='demo1'
test.post(base+'/api/logout')
print('Client mapping override rejected; login response contains no password')
