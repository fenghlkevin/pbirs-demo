$ErrorActionPreference='Stop'
$lib='C:\Program Files\Microsoft SQL Server\170\DTS\Binn'
[Reflection.Assembly]::LoadFrom("$lib\Microsoft.AnalysisServices.Core.dll") | Out-Null
[Reflection.Assembly]::LoadFrom("$lib\Microsoft.AnalysisServices.Tabular.dll") | Out-Null
$s=New-Object Microsoft.AnalysisServices.Tabular.Server;$s.Connect('Data Source=localhost');$d=$s.Databases.FindByName('P4_RLS_Demo_Build')
if($d -and $d.ID -eq 'P4_RLS_Demo_Build'){$d.Drop();Write-Output 'Removed isolated build database'};$s.Disconnect()
Get-FileHash 'E:\PowerBI\PBIRS\ReportServer\rssrvpolicy.config','E:\PowerBI\PBIRS\ReportServer\web.config','E:\PowerBI\PBIRS\ReportServer\rsreportserver.config' | ForEach-Object {$_.Path+' '+$_.Hash}
