$ErrorActionPreference='Stop'
$base='E:\PowerBI\PBIRS'
Get-FileHash "$base\ReportServer\rssrvpolicy.config","$base\ReportServer\web.config","$base\ReportServer\rsreportserver.config" -Algorithm SHA256 | Select Path,Hash | ConvertTo-Json
Get-ChildItem "$base\LogFiles" -Filter 'ReportingServicesService*.log' | Sort LastWriteTime -Descending | Select -First 1 | ForEach-Object {Get-Content $_.FullName -Tail 100 | Select-String 'error|Inheritance security|Could not load' -Context 0,2}
