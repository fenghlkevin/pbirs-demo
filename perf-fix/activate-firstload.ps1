$ErrorActionPreference='Stop'
$root='C:\ProgramData\P4DemoApp';$backup="$root\firstload-backup-$(Get-Date -Format yyyyMMdd-HHmmss)"
New-Item -ItemType Directory $backup | Out-Null
Copy-Item "$root\app\server.py","$root\app\index.html" $backup
Stop-ScheduledTask P4DemoApp
Start-Sleep -Seconds 1
Get-CimInstance Win32_Process | Where-Object {$_.Name -eq 'python.exe' -and $_.CommandLine -like '*P4DemoApp*server.py*'} | ForEach-Object {Stop-Process -Id $_.ProcessId -Force}
Expand-Archive "$root\firstload-update.zip" "$root\app" -Force
Start-ScheduledTask P4DemoApp
Start-Sleep -Seconds 2
(Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8765/).StatusCode
Write-Output "Backup=$backup"
