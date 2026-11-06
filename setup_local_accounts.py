"""Create application demo accounts without creating Windows/AD accounts."""
import argparse,hashlib,json,os,re,secrets
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--user',action='append');args=parser.parse_args()
accounts_path=Path('app-accounts.local.json');logins_path=Path('app-logins.local.json')
accounts=json.loads(accounts_path.read_text()) if accounts_path.exists() else {}
logins=json.loads(logins_path.read_text()) if logins_path.exists() else {}
for name in args.user or ['demo1','demo2','demo3']:
 if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',name) or name=='maintenance':raise ValueError('Invalid username')
 if name in accounts:print(name,'already exists');continue
 password='P4!'+secrets.token_urlsafe(12)+'9a';salt=secrets.token_hex(16)
 accounts[name]={'salt':salt,'iterations':600000,'passwordHash':hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),600000).hex(),'principal':'p4:'+name}
 logins[name]={'password':password,'principal':'p4:'+name};print('Created application user',name,'without Windows account')
for path,data in [(accounts_path,accounts),(logins_path,logins)]:
 temporary=path.with_suffix('.tmp');fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'w') as f:json.dump(data,f,indent=2)
 os.replace(temporary,path)
print('Restart demo server after account changes. Grant report policies separately.')
