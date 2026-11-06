import json,time,base64,hashlib,hmac,secrets
from pathlib import Path
import requests
from ticket_auth import issue_ticket,establish,BASE,KEY,b64

def send(ticket):
 s=requests.Session();s.trust_env=False
 return s.post(BASE+'/ReportServer/P4Login.aspx',data={'ticket':ticket},timeout=30,allow_redirects=False)
ticket=issue_ticket('p4:demo1');first=send(ticket);assert first.status_code==200,first.status_code
assert send(ticket).status_code==401,'Ticket replay accepted'
assert send(issue_ticket('p4:demo1',-1)).status_code==401,'Expired ticket accepted'
assert send(ticket[:-1]+('A' if ticket[-1]!='A' else 'B')).status_code==401,'Tampered ticket accepted'
assert send(issue_ticket('p4:demo1',120)).status_code==401,'Overlong validity accepted'
now=int(time.time())
for field,value in [('aud','wrong-server'),('iss','untrusted-issuer'),('iat',now+1000)]:
 payload={'iss':'p4-demo','aud':'pbirs-demo','sub':'p4:demo1','iat':now,'exp':now+30,'jti':secrets.token_hex(16)};payload[field]=value
 body=b64(json.dumps(payload,separators=(',',':')).encode());forged=(body+b'.'+b64(hmac.new(KEY,body,hashlib.sha256).digest())).decode()
 assert send(forged).status_code==401,(field,'Accepted invalid claims')
# A previously unknown P4 identity authenticates without any Windows account provisioning,
# but gets no report access until a resource policy explicitly grants it.
subject='p4:new_'+secrets.token_hex(5)
s,me=establish(subject);assert me['Username']==subject
report=json.loads(Path('demo-manifest.json').read_text())[0]
r=s.get(BASE+'/powerbi/api/explore/reports/'+report['id']+'/modelsAndExploration?preferReadOnlySession=true');assert r.status_code==403
print('Ticket signature, expiry, replay, issuer, audience, future-time and default-deny tests passed')
print('New P4 identity authenticated without Windows account and denied ungranted report')
