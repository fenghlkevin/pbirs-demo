Get-Process PBIDesktop | Select-Object Id,SessionId,MainWindowTitle
quser
Get-ChildItem E:\PowerDestop\bin -Filter '*AnalysisServices*' | Select-Object -ExpandProperty Name
Get-ChildItem 'C:\Users\Administrator\AppData\Local\Microsoft\Power BI Desktop SSRS\AnalysisServicesWorkspaces' -Filter msmdsrv.port.txt -Recurse | ForEach-Object { $_.FullName; Get-Content $_.FullName }
Get-ChildItem E:\PowerBI\PBIRS\ASEngine\workspaces -Filter msmdsrv.port.txt -Recurse | ForEach-Object { $_.FullName; Get-Content $_.FullName }
