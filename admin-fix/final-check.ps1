$ErrorActionPreference='Stop';$base='E:\PowerBI\PBIRS\ReportServer'
$expected=@{'rssrvpolicy.config'='30B031FFB1EF2465B6BE45EFCA461C6C8B498F1021CF2A148A2B87EE23978432';'web.config'='DFD1980F7FBD41DF290627C1BC70DC3C1E291F66221E3013BA98A70CCEEA230B';'rsreportserver.config'='C32E492BA55FAA45E82D8E40962590070F31D2EBC7108BBA112E8738014749CC'}
foreach($name in $expected.Keys){$hash=(Get-FileHash "$base\$name" -Algorithm SHA256).Hash;if($hash -ne $expected[$name]){throw "Configuration changed: $name"};Write-Output ($name+': unchanged')}
[xml]$policy=Get-Content "$base\rssrvpolicy.config"
Write-Output ('P4 FullTrust grant count: '+$policy.SelectNodes("//CodeGroup[@Name='P4SecurityExtension' or @Name='P4SignedExtensionOnly']").Count)
Get-Service PowerBIReportServer | Select Name,Status | ConvertTo-Json
