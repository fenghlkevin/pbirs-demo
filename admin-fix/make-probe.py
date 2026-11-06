import base64
from pathlib import Path
root=Path('admin-fix');sources={'CasProbe.cs':(root/'CasProbe.cs').read_text()}
original=Path('custom-security/P4Security.cs').read_text()
plain=original.replace('[System.Security.SecurityCritical]','')
sources['Current.cs']=original
sources['Plain.cs']=plain
sources['Aptca.cs']=plain.replace('namespace P4.Reporting {','[assembly: System.Security.AllowPartiallyTrustedCallers]\nnamespace P4.Reporting {')
sources['SafeCritical.cs']=original.replace('[System.Security.SecurityCritical]','[System.Security.SecuritySafeCritical]').replace('namespace P4.Reporting {','[assembly: System.Security.AllowPartiallyTrustedCallers]\nnamespace P4.Reporting {')
# Isolated compatibility test only; this does not change any server permission grant.
sources['LegacyCompatibility.cs']=plain.replace('namespace P4.Reporting {','[assembly: System.Security.SecurityRules(System.Security.SecurityRuleSet.Level1)]\nnamespace P4.Reporting {')
paths=[];i=0
for name,source in sources.items():
 data=source.encode()
 for offset in range(0,len(data),1350):
  value=base64.b64encode(data[offset:offset+1350]).decode();mode='Create' if offset==0 else 'Append';p=root/f'probe-{i:02}.ps1'
  p.write_text(f"$ErrorActionPreference='Stop';New-Item -ItemType Directory 'C:\\ProgramData\\P4CompatibilityProbe' -Force|Out-Null;$f=[IO.File]::Open('C:\\ProgramData\\P4CompatibilityProbe\\{name}',[IO.FileMode]::{mode});try{{$b=[Convert]::FromBase64String('{value}');$f.Write($b,0,$b.Length)}}finally{{$f.Close()}}")
  paths.append(str(p));i+=1
(root/'probe-paths.txt').write_text('\n'.join(paths)+'\n');print('\n'.join(paths))
