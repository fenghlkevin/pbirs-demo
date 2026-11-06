import getpass,json,requests
from pathlib import Path
from requests_ntlm import HttpNtlmAuth
s=requests.Session();s.trust_env=False;s.auth=HttpNtlmAuth('Administrator',getpass.getpass('Windows maintenance password: '))
base='http://pbirs.example.internal/Reports/api/v2.0'
paths=['/Folders(98130126-1a80-474d-a151-d20bb2678de4)/Policies']+[f"/PowerBIReports({r['id']})/Policies" for r in json.loads(Path('demo-manifest.json').read_text())]
backup={}
for path in paths:
 r=s.get(base+path,timeout=30);r.raise_for_status();backup[path]=r.json()
p=Path('custom-security/original-policies.json')
if p.exists():raise RuntimeError('Backup exists; refusing to overwrite')
p.write_text(json.dumps(backup,indent=2));print('Saved original demo folder and report policies')
