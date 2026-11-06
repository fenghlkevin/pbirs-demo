import base64,json
from pathlib import Path
work='C:\\ProgramData\\P4PbirsDemo'
files=[(Path('custom-security/P4Security.cs'),work+'\\P4Security.cs'),(Path('custom-security/P4Login.aspx'),work+'\\P4Login.aspx'),(Path('custom-security/P4Portal.aspx'),work+'\\P4Portal.aspx'),(Path('app-accounts.local.json'),work+'\\system-users.json')]
paths=[];number=0
for source,target in files:
 data=source.read_bytes()
 for offset in range(0,len(data),1400):
  chunk=base64.b64encode(data[offset:offset+1400]).decode();mode='Create' if offset==0 else 'Append'
  p=Path(f'portal-deploy/upload-{number:02}.ps1');p.write_text(f"$ErrorActionPreference='Stop';$f=[IO.File]::Open('{target}',[IO.FileMode]::{mode});try{{$b=[Convert]::FromBase64String('{chunk}');$f.Write($b,0,$b.Length)}}finally{{$f.Close()}}")
  paths.append(str(p));number+=1
Path('portal-deploy/upload-paths.txt').write_text('\n'.join(paths)+'\n');print('\n'.join(paths))
