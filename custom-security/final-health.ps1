$ErrorActionPreference='Stop'
[xml]$rs=Get-Content 'E:\PowerBI\PBIRS\ReportServer\rsreportserver.config'
Write-Output ('Authentication: '+$rs.Configuration.Authentication.AuthenticationTypes.InnerXml)
[xml]$policy=Get-Content 'E:\PowerBI\PBIRS\ReportServer\rssrvpolicy.config'
Write-Output ('Extra P4 FullTrust groups: '+$policy.SelectNodes("//CodeGroup[@Name='P4SecurityExtension']").Count)
Get-Service PowerBIReportServer | Select Name,Status | ConvertTo-Json
Get-Content 'C:\ProgramData\P4PbirsDemo\backup-path.txt'
Get-ChildItem 'C:\ProgramData\P4PbirsDemo\used' | Where-Object {$_.Name -like 'diag-*' -or $_.Name -eq 'last-failure.txt'} | Remove-Item
