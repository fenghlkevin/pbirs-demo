$ErrorActionPreference='Stop'
$lib='C:\Program Files\Microsoft SQL Server\170\DTS\Binn'
[Reflection.Assembly]::LoadFrom("$lib\Microsoft.AnalysisServices.Core.dll") | Out-Null
[Reflection.Assembly]::LoadFrom("$lib\Microsoft.AnalysisServices.Tabular.dll") | Out-Null
$s=New-Object Microsoft.AnalysisServices.Tabular.Server;$s.Connect('Data Source=localhost')
$r=$s.Execute([IO.File]::ReadAllText('C:\ProgramData\P4RlsDemo\create-model.json'))
$r | Format-List *
foreach($x in $r){$x.Messages | Format-List *}
$s.Databases | Select-Object Name,ID
