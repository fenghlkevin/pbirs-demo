$ErrorActionPreference='Stop';$work='C:\ProgramData\P4PbirsDemo';$base='E:\PowerBI\PBIRS'
& C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /nologo /target:library /out:"$work\P4.Reporting.dll" /reference:"$base\ReportServer\bin\Microsoft.ReportingServices.Interfaces.dll" /reference:System.Web.dll /reference:System.Web.Extensions.dll "$work\P4Security.cs"
if($LASTEXITCODE -ne 0){throw 'Build failed'}
Stop-Service PowerBIReportServer -Force
foreach($target in @('ReportServer\bin','Portal','PowerBI')){Copy-Item "$work\P4.Reporting.dll" "$base\$target\P4.Reporting.dll" -Force}
Start-Service PowerBIReportServer
Write-Output 'Updated extension loaded'
