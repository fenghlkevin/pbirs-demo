$lib='C:\Program Files\Microsoft SQL Server\170\DTS\Binn'
[Reflection.Assembly]::LoadFrom("$lib\Microsoft.AnalysisServices.Core.dll") | Out-Null
[Reflection.Assembly]::LoadFrom("$lib\Microsoft.AnalysisServices.Tabular.dll") | Out-Null
$s=New-Object Microsoft.AnalysisServices.Tabular.Server;$s.Connect('Data Source=localhost:5132')
$s.Databases.Refresh();Write-Output "Databases=$($s.Databases.Count)";foreach($d in $s.Databases){Write-Output $d.Name;if($d.Name -like 'f81aad00*'){Write-Output "Database $($d.ID) $($d.CompatibilityLevel)"; $d.Model.Tables | Select-Object Name,State;$d.Model.Roles | Select-Object Name,ModelPermission}}
$s.Disconnect()
