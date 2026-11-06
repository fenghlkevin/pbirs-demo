$ErrorActionPreference='Stop';$base='E:\PowerBI\PBIRS\ReportServer'
Copy-Item 'C:\ProgramData\P4PbirsDemo\P4Login.aspx' "$base\P4Login.aspx" -Force
[xml]$web=Get-Content "$base\web.config"
$node=$web.configuration.SelectSingleNode("location[@path='P4Portal.aspx']")
if($node){[void]$node.ParentNode.RemoveChild($node);$web.Save("$base\web.config")}
Remove-Item "$base\P4Portal.aspx" -ErrorAction SilentlyContinue
Write-Output 'Shared system login active at configured P4Login.aspx; extra anonymous page removed'
