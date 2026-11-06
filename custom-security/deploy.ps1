$ErrorActionPreference='Stop'
$base='E:\PowerBI\PBIRS'
$work='C:\ProgramData\P4PbirsDemo'
$backup=Join-Path $work ('backup-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory $backup | Out-Null
foreach($name in @('rsreportserver.config','web.config','rssrvpolicy.config')){Copy-Item "$base\ReportServer\$name" "$backup\$name"}
[IO.File]::WriteAllText("$work\backup-path.txt",$backup)
$rollback=@'
$ErrorActionPreference='Stop'
$base='E:\PowerBI\PBIRS'
$backup=(Get-Content 'C:\ProgramData\P4PbirsDemo\backup-path.txt' -Raw).Trim()
Stop-Service PowerBIReportServer -Force
foreach($name in @('rsreportserver.config','web.config','rssrvpolicy.config')){Copy-Item "$backup\$name" "$base\ReportServer\$name" -Force}
Start-Service PowerBIReportServer
Write-Output 'Original NTLM configuration restored. Restore demo policies using original-policies.json.'
'@
[IO.File]::WriteAllText("$work\rollback.ps1",$rollback)
Stop-Service PowerBIReportServer -Force
try {
 foreach($target in @('ReportServer\bin','Portal','PowerBI')){Copy-Item "$work\P4.Reporting.dll" "$base\$target\P4.Reporting.dll" -Force}
 Copy-Item "$work\P4Login.aspx" "$base\ReportServer\P4Login.aspx" -Force
 [xml]$config=Get-Content "$base\ReportServer\rsreportserver.config"
 $config.Configuration.Authentication.AuthenticationTypes.InnerXml='<Custom />'
 $config.Configuration.Extensions.Security.InnerXml='<Extension Name="Forms" Type="P4.Reporting.Authorization, P4.Reporting" />'
 $config.Configuration.Extensions.Authentication.InnerXml='<Extension Name="Forms" Type="P4.Reporting.Authentication, P4.Reporting" />'
 $rng=[Security.Cryptography.RandomNumberGenerator]::Create()
 $validation=New-Object byte[] 64; $decryption=New-Object byte[] 32
 $rng.GetBytes($validation);$rng.GetBytes($decryption)
 $vk=([BitConverter]::ToString($validation)).Replace('-','');$dk=([BitConverter]::ToString($decryption)).Replace('-','')
 $machine=$config.Configuration.SelectSingleNode('MachineKey')
 if(!$machine){$machine=$config.CreateElement('MachineKey');[void]$config.Configuration.AppendChild($machine)}
 $machine.SetAttribute('ValidationKey',$vk);$machine.SetAttribute('DecryptionKey',$dk);$machine.SetAttribute('Validation','AES');$machine.SetAttribute('Decryption','AES')
 $ui=$config.Configuration.UI
 if(!$ui){$ui=$config.CreateElement('UI');[void]$config.Configuration.AppendChild($ui)}
 $custom=$ui.SelectSingleNode('CustomAuthenticationUI')
 if(!$custom){$custom=$config.CreateElement('CustomAuthenticationUI');[void]$ui.AppendChild($custom)}
 $custom.InnerXml='<PassThroughCookies><PassThroughCookie>P4AuthCookie</PassThroughCookie></PassThroughCookies>'
 $config.Save("$base\ReportServer\rsreportserver.config")
 [xml]$web=Get-Content "$base\ReportServer\web.config"
 $system=$web.configuration.'system.web'
 $system.identity.SetAttribute('impersonate','false')
 $system.authentication.SetAttribute('mode','Forms')
 $system.authentication.InnerXml='<forms loginUrl="P4Login.aspx" name="P4AuthCookie" timeout="60" path="/" protection="All" requireSSL="false" slidingExpiration="false" />'
 $auth=$system.SelectSingleNode('authorization')
 if(!$auth){$auth=$web.CreateElement('authorization');[void]$system.AppendChild($auth)}
 $auth.InnerXml='<deny users="?" />'
 $mk=$system.SelectSingleNode('machineKey')
 if(!$mk){$mk=$web.CreateElement('machineKey');[void]$system.AppendChild($mk)}
 $mk.SetAttribute('validationKey',$vk);$mk.SetAttribute('decryptionKey',$dk);$mk.SetAttribute('validation','AES');$mk.SetAttribute('decryption','AES')
 $web.Save("$base\ReportServer\web.config")
 Start-Service PowerBIReportServer
 Write-Output "DEPLOYED; configuration backup: $backup"
} catch {
 foreach($name in @('rsreportserver.config','web.config','rssrvpolicy.config')){Copy-Item "$backup\$name" "$base\ReportServer\$name" -Force}
 Start-Service PowerBIReportServer
 throw
}
