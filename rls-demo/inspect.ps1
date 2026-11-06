Get-ChildItem 'C:\Program Files','E:\' -Directory | Select-Object -ExpandProperty FullName
Get-CimInstance Win32_Process | Where-Object {$_.Name -match 'PBIDesktop|msmdsrv|sqlservr'} | Select-Object Name,ProcessId,CommandLine | Format-List
Get-ChildItem 'E:\PowerBI' -Directory | Select-Object -ExpandProperty FullName
Get-ChildItem 'E:\PowerBI\PBIRS' -Filter '*Tabular*.dll' -Recurse | Select-Object -First 8 -ExpandProperty FullName
