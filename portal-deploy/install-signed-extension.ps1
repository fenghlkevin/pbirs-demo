$ErrorActionPreference='Stop'
$base='E:\PowerBI\PBIRS';$build='C:\ProgramData\P4PbirsSignedBuild';$work='C:\ProgramData\P4PbirsDemo'
$assembly=[Reflection.AssemblyName]::GetAssemblyName("$build\P4.Reporting.dll")
$token=([BitConverter]::ToString($assembly.GetPublicKeyToken())).Replace('-','').ToLowerInvariant()
if($assembly.Name -ne 'P4.Reporting' -or $assembly.Version.ToString() -ne '1.0.0.0' -or $token -ne '898175a7425b79c6'){throw 'Unexpected signed assembly identity'}
[xml]$proposal=Get-Content "$build\proposed-trust.xml" -Raw
$membership=$proposal.CodeGroup.IMembershipCondition
$publicKey=([BitConverter]::ToString($assembly.GetPublicKey())).Replace('-','')
if($membership.class -ne 'StrongNameMembershipCondition' -or $membership.Name -ne 'P4.Reporting' -or $membership.AssemblyVersion -ne '1.0.0.0' -or $membership.PublicKeyBlob -ne $publicKey){throw 'Trust proposal does not match the reviewed signed assembly'}
$backup=Join-Path $work ('signed-backup-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory $backup | Out-Null
Copy-Item "$base\ReportServer\rssrvpolicy.config" "$backup\rssrvpolicy.config"
Copy-Item "$base\ReportServer\bin\P4.Reporting.dll" "$backup\P4.Reporting.dll"
[IO.File]::WriteAllText("$work\signed-backup-path.txt",$backup)
Stop-Service PowerBIReportServer -Force
try {
 [xml]$policy=Get-Content "$base\ReportServer\rssrvpolicy.config"
 if($policy.SelectSingleNode("//CodeGroup[@Name='P4SignedExtensionOnly']")){throw 'Scoped grant already exists; refusing to replace it'}
 $parent=$policy.SelectSingleNode('//PolicyLevel/CodeGroup')
 if(!$parent){throw 'Code policy parent missing'}
 $rule=$policy.ImportNode($proposal.DocumentElement,$true);[void]$parent.AppendChild($rule)
 $policy.Save("$base\ReportServer\rssrvpolicy.config")
 foreach($target in @('ReportServer\bin','Portal','PowerBI')){Copy-Item "$build\P4.Reporting.dll" "$base\$target\P4.Reporting.dll" -Force}
 Start-Service PowerBIReportServer
 Write-Output ('Installed only the reviewed signed extension: '+$assembly.FullName)
 Write-Output ('Backup: '+$backup)
} catch {
 Copy-Item "$backup\rssrvpolicy.config" "$base\ReportServer\rssrvpolicy.config" -Force
 foreach($target in @('ReportServer\bin','Portal','PowerBI')){Copy-Item "$backup\P4.Reporting.dll" "$base\$target\P4.Reporting.dll" -Force}
 Start-Service PowerBIReportServer
 throw
}
