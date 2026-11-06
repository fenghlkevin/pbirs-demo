import getpass,json,sys
from pathlib import Path
import winrm
p=getpass.getpass('Windows maintenance password: ')
w=winrm.Session('http://pbirs.example.internal:5985/wsman',auth=('Administrator',p),transport='ntlm',proxy=None)
print('READY',flush=True)
for line in sys.stdin:
 path=line.strip()
 if path=='exit':break
 try:
  r=w.run_ps(Path(path).read_text());print('STATUS',r.status_code,flush=True);print(r.std_out.decode(errors='replace'),flush=True)
  if r.status_code:print(r.std_err.decode(errors='replace')[-4000:],flush=True)
 except Exception as e:print(type(e).__name__,str(e)[:500],flush=True)
 print('READY',flush=True)
