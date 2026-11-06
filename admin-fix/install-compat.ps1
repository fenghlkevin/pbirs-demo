$ErrorActionPreference='Stop'
$base='E:\PowerBI\PBIRS';$work='C:\ProgramData\P4PbirsDemo';$probe='C:\ProgramData\P4CompatibilityProbe'
$baseline=@{}
foreach($name in @('rssrvpolicy.config','web.config','rsreportserver.config')){$baseline[$name]=(Get-FileHash "$base\ReportServer\$name" -Algorithm SHA256).Hash}
$backup=Join-Path $work ('compat-backup-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory $backup | Out-Null
Copy-Item "$base\ReportServer\bin\P4.Reporting.dll" "$backup\P4.Reporting.dll"
$baseline | ConvertTo-Json | Set-Content "$backup\config-hashes.json"
Copy-Item "$probe\LegacyCompatibility.cs" "$backup\P4Security.cs"
Copy-Item "$probe\LegacyCompatibility.cs" "$work\P4Security.cs" -Force
& C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /nologo /target:library /out:"$work\P4.Reporting.dll" /reference:"$base\ReportServer\bin\Microsoft.ReportingServices.Interfaces.dll" /reference:System.Web.dll /reference:System.Web.Extensions.dll "$probe\LegacyCompatibility.cs"
if($LASTEXITCODE -ne 0){throw 'Compatibility build failed'}
Stop-Service PowerBIReportServer -Force
try {
 foreach($target in @('ReportServer\bin','Portal','PowerBI')){Copy-Item "$work\P4.Reporting.dll" "$base\$target\P4.Reporting.dll" -Force}
 foreach($name in $baseline.Keys){if((Get-FileHash "$base\ReportServer\$name" -Algorithm SHA256).Hash -ne $baseline[$name]){throw "Configuration changed unexpectedly: $name"}}
 Start-Service PowerBIReportServer
 [IO.File]::WriteAllText("$work\compat-backup-path.txt",$backup)
 Write-Output 'Compatibility DLL installed; all three server configuration hashes unchanged'
 Write-Output ('Backup: '+$backup)
} catch {
 foreach($target in @('ReportServer\bin','Portal','PowerBI')){Copy-Item "$backup\P4.Reporting.dll" "$base\$target\P4.Reporting.dll" -Force}
 Start-Service PowerBIReportServer
 throw
}
