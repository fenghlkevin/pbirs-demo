$ErrorActionPreference='Stop';$work='C:\ProgramData\P4CompatibilityProbe'
Copy-Item 'E:\PowerBI\PBIRS\ReportServer\bin\Microsoft.ReportingServices.Interfaces.dll' "$work\Microsoft.ReportingServices.Interfaces.dll" -Force
$csc='C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe'
foreach($name in @('Current','Plain','Aptca','SafeCritical','LegacyCompatibility')) {
 & $csc /nologo /target:library /out:"$work\$name.dll" /reference:"$work\Microsoft.ReportingServices.Interfaces.dll" /reference:System.Web.dll /reference:System.Web.Extensions.dll "$work\$name.cs"
 if($LASTEXITCODE -ne 0){throw "Compile failed: $name"}
}
& $csc /nologo /out:"$work\CasProbe.exe" "$work\CasProbe.cs"
if($LASTEXITCODE -ne 0){throw 'Probe build failed'}
& "$work\CasProbe.exe" "$work\Current.dll" "$work\Plain.dll" "$work\Aptca.dll" "$work\SafeCritical.dll" "$work\LegacyCompatibility.dll"
