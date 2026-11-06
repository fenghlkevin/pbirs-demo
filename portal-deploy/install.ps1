$ErrorActionPreference='Stop'
$base='E:\PowerBI\PBIRS';$work='C:\ProgramData\P4PbirsDemo'
& C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /nologo /target:library /out:"$work\P4.Reporting.dll" /reference:"$base\ReportServer\bin\Microsoft.ReportingServices.Interfaces.dll" /reference:System.Web.dll /reference:System.Web.Extensions.dll "$work\P4Security.cs"
if($LASTEXITCODE -ne 0){throw 'Build failed'}
$backup=Join-Path $work ('portal-backup-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory $backup | Out-Null
Copy-Item "$base\ReportServer\web.config" "$backup\web.config"
Copy-Item "$base\ReportServer\P4Login.aspx" "$backup\P4Login.aspx"
Copy-Item "$base\ReportServer\bin\P4.Reporting.dll" "$backup\P4.Reporting.dll"
[IO.File]::WriteAllText("$work\portal-backup-path.txt",$backup)
Stop-Service PowerBIReportServer -Force
try {
 foreach($target in @('ReportServer\bin','Portal','PowerBI')){Copy-Item "$work\P4.Reporting.dll" "$base\$target\P4.Reporting.dll" -Force}
 Copy-Item "$work\P4Login.aspx" "$base\ReportServer\P4Login.aspx" -Force
 Copy-Item "$work\P4Portal.aspx" "$base\ReportServer\P4Portal.aspx" -Force
 [xml]$web=Get-Content "$base\ReportServer\web.config"
 $location=$web.configuration.SelectSingleNode("location[@path='P4Portal.aspx']")
 if(!$location){$location=$web.CreateElement('location');$location.SetAttribute('path','P4Portal.aspx');[void]$web.configuration.AppendChild($location)}
 $location.InnerXml='<system.web><authorization><allow users="*" /></authorization></system.web>'
 $web.Save("$base\ReportServer\web.config")
 Start-Service PowerBIReportServer
 Write-Output "Shared login installed on existing HTTP site. Backup: $backup"
} catch {
 Copy-Item "$backup\web.config" "$base\ReportServer\web.config" -Force
 Copy-Item "$backup\P4Login.aspx" "$base\ReportServer\P4Login.aspx" -Force
 foreach($target in @('ReportServer\bin','Portal','PowerBI')){Copy-Item "$backup\P4.Reporting.dll" "$base\$target\P4.Reporting.dll" -Force}
 Start-Service PowerBIReportServer
 throw
}
