import getpass,json,sys,base64
from pathlib import Path
import winrm
p=getpass.getpass('Windows maintenance password: ')
w=winrm.Session('http://pbirs.example.internal:5985/wsman',auth=('Administrator',p),transport='ntlm',proxy=None)
print('READY',flush=True)
for line in sys.stdin:
 path=line.strip()
 if path=='exit':break
 try:
  if path.startswith('download '):
   _,remote,local=path.split(' ',2)
   if not remote.startswith('C:\\ProgramData\\P4RlsDemo\\'):raise ValueError('Download scope rejected')
   r=w.run_ps("[Convert]::ToBase64String([IO.File]::ReadAllBytes('"+remote+"'))")
   if r.status_code:raise ValueError(r.std_err.decode(errors='replace'))
   data=base64.b64decode(r.std_out);Path(local).write_bytes(data);print('Downloaded bytes:',len(data),flush=True);continue
  r=w.run_ps(Path(path).read_text());print('STATUS',r.status_code,flush=True);print(r.std_out.decode(errors='replace'),flush=True)
  if r.status_code:print(r.std_err.decode(errors='replace')[-4000:],flush=True)
 except Exception as e:print(type(e).__name__,str(e)[:500],flush=True)
 print('READY',flush=True)
