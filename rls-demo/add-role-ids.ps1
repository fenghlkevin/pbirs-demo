$ErrorActionPreference='Stop'
$lib='C:\Program Files\Microsoft SQL Server\170\DTS\Binn'
[Reflection.Assembly]::LoadFrom("$lib\Microsoft.AnalysisServices.Core.dll") | Out-Null
[Reflection.Assembly]::LoadFrom("$lib\Microsoft.AnalysisServices.Tabular.dll") | Out-Null
$s=New-Object Microsoft.AnalysisServices.Tabular.Server;$s.Connect('Data Source=localhost');$d=$s.Databases.FindByName('P4_RLS_Demo_Build')
foreach($r in $d.Model.Roles){if(!$r.Annotations.Contains('PBI_Id')){$a=New-Object Microsoft.AnalysisServices.Tabular.Annotation;$a.Name='PBI_Id';$a.Value=[Guid]::NewGuid().ToString();$r.Annotations.Add($a)};Write-Output "$($r.Name) $($r.Annotations['PBI_Id'].Value)"}
$d.Model.SaveChanges() | Out-Null
$d.Backup('C:\ProgramData\P4RlsDemo\DataModel.abf',$true)
$s.Disconnect()
