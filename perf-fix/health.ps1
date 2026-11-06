Get-Content 'C:\ProgramData\P4DemoApp\data\service.log' -Tail 8
Get-FileHash 'E:\PowerBI\PBIRS\ReportServer\rssrvpolicy.config','E:\PowerBI\PBIRS\ReportServer\web.config','E:\PowerBI\PBIRS\ReportServer\rsreportserver.config' | ForEach-Object {$_.Path+' '+$_.Hash}
