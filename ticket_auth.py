"""P4 identity-ticket issuer and PBIRS forms-session bridge (no Windows auth)."""
import os,base64,hashlib,hmac,json,secrets,time
from pathlib import Path
import requests
BASE=os.environ.get('P4_PBIRS_URL','http://pbirs.example.internal').rstrip('/')
KEY=base64.b64decode(json.loads(Path(__file__).with_name('ticket-signing.local.json').read_text(encoding='utf-8'))['key'])
def b64(value):return base64.urlsafe_b64encode(value).rstrip(b'=')
def issue_ticket(principal,lifetime=30,*,browser=False,return_url="/Reports"):
 now=int(time.time())
 payload={'iss':'p4-demo','aud':'pbirs-demo','sub':principal,'iat':now,'exp':now+lifetime,'jti':secrets.token_hex(16)}
 if browser:payload.update({'flow':'browser','returnUrl':return_url})
 body=b64(json.dumps(payload,separators=(',',':')).encode())
 return (body+b'.'+b64(hmac.new(KEY,body,hashlib.sha256).digest())).decode()
def establish(principal):
 s=requests.Session();s.trust_env=False
 r=s.post(BASE+'/ReportServer/P4Login.aspx',data={'ticket':issue_ticket(principal)},timeout=45,allow_redirects=False)
 if r.status_code!=200 or not r.json().get('authenticated'):raise ValueError('PBIRS ticket authentication failed: '+str(r.status_code))
 r=s.get(BASE+'/Reports/api/v2.0/me',timeout=45,allow_redirects=False)
 if r.status_code!=200 or r.json().get('Username')!=principal:raise ValueError('PBIRS authenticated identity mismatch: '+str(r.status_code))
 return s,r.json()
