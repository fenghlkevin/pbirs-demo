"""One-time remote deployment. Refuses to replace an existing deployment/backup."""
import base64,getpass,json,secrets,sys
from pathlib import Path
import winrm
root=Path(__file__).resolve().parents[1]
keyfile=root/'ticket-signing.local.json'
if not keyfile.exists():raise RuntimeError('Create a permission-600 HMAC key file before deployment')
key=json.loads(keyfile.read_text())['key']
w=winrm.Session('http://pbirs.example.internal:5985/wsman',auth=('Administrator',getpass.getpass('Maintenance password: ')),transport='ntlm',proxy=None)
def run(script):
 r=w.run_ps("$ErrorActionPreference='Stop';\n"+script)
 if r.status_code:raise RuntimeError(r.std_out.decode(errors='replace')+r.std_err.decode(errors='replace')[-2000:])
 print(r.std_out.decode(errors='replace').strip())
def upload(data,path):
 for offset in range(0,len(data),1500):
  chunk=base64.b64encode(data[offset:offset+1500]).decode();mode='Create' if offset==0 else 'Append'
  run(f"$f=[IO.File]::Open('{path}',[IO.FileMode]::{mode});try {{$b=[Convert]::FromBase64String('{chunk}');$f.Write($b,0,$b.Length)}}finally{{$f.Close()}}")
work='C:\\ProgramData\\P4PbirsDemo'
run(f"if(Test-Path '{work}\\backup-path.txt'){{throw 'Existing deployment detected; refusing to overwrite backup'}};New-Item -ItemType Directory '{work}\\used' -Force|Out-Null; & icacls '{work}' /inheritance:r /grant 'BUILTIN\\Administrators:(OI)(CI)F' 'NT AUTHORITY\\SYSTEM:(OI)(CI)F' 'NT SERVICE\\PowerBIReportServer:(OI)(CI)RX'|Out-Null; & icacls '{work}\\used' /grant 'NT SERVICE\\PowerBIReportServer:(OI)(CI)M'|Out-Null")
for name in ('P4Security.cs','P4Login.aspx','deploy.ps1'):upload((root/'custom-security'/name).read_bytes(),work+'\\'+name)
upload(key.encode(),work+'\\ticket-key.txt')
upload((root/'app-accounts.local.json').read_bytes(),work+'\\system-users.json')
run(f'& C:\\Windows\\Microsoft.NET\\Framework64\\v4.0.30319\\csc.exe /nologo /target:library /out:"{work}\\P4.Reporting.dll" /reference:"E:\\PowerBI\\PBIRS\\ReportServer\\bin\\Microsoft.ReportingServices.Interfaces.dll" /reference:System.Web.dll /reference:System.Web.Extensions.dll "{work}\\P4Security.cs"; if($LASTEXITCODE -ne 0){{throw "Build failed"}}')
run(f"& '{work}\\deploy.ps1'")
print('Deployment complete. Configure P4 policies after server startup.')
