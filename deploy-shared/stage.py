import base64,io,zipfile
from pathlib import Path
root=Path(__file__).resolve().parent.parent
buffer=io.BytesIO()
with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as z:
 for name in ['server.py','demo_admin.py','ticket_auth.py','index.html','app-accounts.local.json','ticket-signing.local.json','custom-security/P4Login.aspx']:
  z.write(root/name,name)
raw=buffer.getvalue();paths=[]
for i,offset in enumerate(range(0,len(raw),1350)):
 path=Path('/tmp/p4-package-%03d.ps1'%i)
 data=base64.b64encode(raw[offset:offset+1350]).decode()
 mode='Create' if i==0 else 'Append'
 path.write_text("$f=[IO.File]::Open('C:\\ProgramData\\P4DemoApp\\package.zip',[IO.FileMode]::%s);try{$b=[Convert]::FromBase64String('%s');$f.Write($b,0,$b.Length)}finally{$f.Close()}"%(mode,data))
 paths.append(str(path))
Path('/tmp/p4-package-paths.txt').write_text('\n'.join(paths)+'\n')
print('Package bytes:',len(raw),'chunks:',len(paths))
