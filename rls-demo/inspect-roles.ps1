$lib='C:\Program Files\Microsoft SQL Server\170\DTS\Binn'
[Reflection.Assembly]::LoadFrom("$lib\Microsoft.AnalysisServices.Core.dll") | Out-Null
[Reflection.Assembly]::LoadFrom("$lib\Microsoft.AnalysisServices.Tabular.dll") | Out-Null
$s=New-Object Microsoft.AnalysisServices.Tabular.Server;$s.Connect('Data Source=localhost:5132');$s.Databases.Refresh()
foreach($d in $s.Databases){if($d.Name -like 'f81aad00*'){
Write-Output "DB=$($d.Name)";foreach($r in $d.Model.Roles){Write-Output "Role=$($r.Name) Permission=$($r.ModelPermission)";foreach($a in $r.Annotations){Write-Output "Annotation $($a.Name)=$($a.Value)"};foreach($t in $r.TablePermissions){Write-Output "Table=$($t.Name) Filter=$($t.FilterExpression)"};foreach($m in $r.Members){Write-Output "Member=$($m.MemberName)"}}
}}
