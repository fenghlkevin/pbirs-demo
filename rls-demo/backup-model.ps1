$ErrorActionPreference='Stop'
$lib='C:\Program Files\Microsoft SQL Server\170\DTS\Binn'
[Reflection.Assembly]::LoadFrom("$lib\Microsoft.AnalysisServices.Core.dll") | Out-Null
[Reflection.Assembly]::LoadFrom("$lib\Microsoft.AnalysisServices.Tabular.dll") | Out-Null
$s=New-Object Microsoft.AnalysisServices.Tabular.Server;$s.Connect('Data Source=localhost')
$r=$s.Execute('{"refresh":{"type":"full","objects":[{"database":"P4_RLS_Demo_Build"}]}}');foreach($x in $r){$x.Messages | Format-List *}
$s.Databases.Refresh();$d=$s.Databases.FindByName('P4_RLS_Demo_Build')
Write-Output "Model=$($d.Name) tables=$($d.Model.Tables.Count) roles=$($d.Model.Roles.Count)"
$d.Backup('C:\ProgramData\P4RlsDemo\DataModel.abf',$true)
Get-Item C:\ProgramData\P4RlsDemo\DataModel.abf | Select-Object Length
$s.Disconnect()
