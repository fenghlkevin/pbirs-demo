import base64,sys
from pathlib import Path
src,dest=sys.argv[1:];raw=Path(src).read_bytes();paths=[]
for i,start in enumerate(range(0,len(raw),1200)):
 p=Path('/tmp/rls-upload-'+str(i)+'.ps1');mode='Create' if i==0 else 'Append'
 p.write_text("$f=[IO.File]::Open('%s',[IO.FileMode]::%s);try{$b=[Convert]::FromBase64String('%s');$f.Write($b,0,$b.Length)}finally{$f.Close()}"%(dest,mode,base64.b64encode(raw[start:start+1200]).decode()));paths.append(str(p))
Path('/tmp/rls-upload-paths.txt').write_text('\n'.join(paths)+'\n');print('chunks',len(paths))
