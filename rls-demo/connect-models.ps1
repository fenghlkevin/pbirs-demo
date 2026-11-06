$ErrorActionPreference='Stop'
$lib='C:\Program Files\Microsoft SQL Server\170\DTS\Binn'
[Reflection.Assembly]::LoadFrom("$lib\Microsoft.AnalysisServices.Core.dll") | Out-Null
[Reflection.Assembly]::LoadFrom("$lib\Microsoft.AnalysisServices.Tabular.dll") | Out-Null
foreach($target in @('localhost','localhost:60452')) {
 try {$s=New-Object Microsoft.AnalysisServices.Tabular.Server;$s.Connect("Data Source=$target");Write-Output "Server $target $($s.Version)"; foreach($d in $s.Databases){Write-Output "$($d.ID) $($d.Name) Compatibility=$($d.CompatibilityLevel)";foreach($t in $d.Model.Tables){Write-Output "Table $($t.Name)"}};$s.Disconnect()}catch{$_.Exception.ToString()}
}
