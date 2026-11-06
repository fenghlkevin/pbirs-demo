import base64
from pathlib import Path
source=Path('custom-security/P4Login.aspx').read_bytes();paths=[]
for i,offset in enumerate(range(0,len(source),1400)):
 chunk=base64.b64encode(source[offset:offset+1400]).decode();mode='Create' if i==0 else 'Append';p=Path(f'portal-deploy/login-{i:02}.ps1')
 p.write_text(f"$ErrorActionPreference='Stop';$f=[IO.File]::Open('C:\\ProgramData\\P4PbirsDemo\\P4Login.aspx',[IO.FileMode]::{mode});try{{$b=[Convert]::FromBase64String('{chunk}');$f.Write($b,0,$b.Length)}}finally{{$f.Close()}}")
 paths.append(str(p))
print('\n'.join(paths))
