import getpass,json,requests
from pathlib import Path
from requests_ntlm import HttpNtlmAuth
s=requests.Session();s.trust_env=False;s.auth=HttpNtlmAuth('Administrator',getpass.getpass('Windows maintenance password (after NTLM rollback): '))
base='http://pbirs.example.internal/Reports/api/v2.0'
for path,original in json.loads(Path(__file__).with_name('original-policies.json').read_text()).items():
 payload={k:original[k] for k in ('InheritParentPolicy','Policies')}
 r=s.put(base+path,json=payload,timeout=30);r.raise_for_status();print('Restored',path)
