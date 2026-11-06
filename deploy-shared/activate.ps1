$ErrorActionPreference='Stop'
$root='C:\ProgramData\P4DemoApp'
$backup="$root\backup-$(Get-Date -Format yyyyMMdd-HHmmss)"
New-Item -ItemType Directory -Force $backup,"$root\data" | Out-Null
Copy-Item 'E:\PowerBI\PBIRS\ReportServer\P4Login.aspx' "$backup\P4Login.aspx"
Get-FileHash 'E:\PowerBI\PBIRS\ReportServer\rssrvpolicy.config','E:\PowerBI\PBIRS\ReportServer\web.config','E:\PowerBI\PBIRS\ReportServer\rsreportserver.config' | Select-Object Path,Hash | ConvertTo-Json | Set-Content "$backup\config-hashes.json"
Expand-Archive "$root\package.zip" "$root\app" -Force
if (!(Test-Path "$root\data\app-accounts.local.json")) { Copy-Item "$root\app\app-accounts.local.json" "$root\data\app-accounts.local.json" }
Remove-Item "$root\app\app-accounts.local.json"
icacls $root /inheritance:r /grant:r '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' '*S-1-5-20:(OI)(CI)RX' | Out-Null
icacls "$root\data" /grant '*S-1-5-20:(OI)(CI)M' | Out-Null
Add-Content "$root\runtime\python313._pth" "`n..\app"
@'
@echo off
set P4_PUBLIC_URL=http://pbirs.example.internal:8765
set P4_BIND=0.0.0.0
set P4_ACCOUNTS_PATH=C:\ProgramData\P4DemoApp\data\app-accounts.local.json
C:\ProgramData\P4DemoApp\runtime\python.exe -u C:\ProgramData\P4DemoApp\app\server.py >> C:\ProgramData\P4DemoApp\data\service.log 2>&1
'@ | Set-Content "$root\run.cmd" -Encoding ASCII
$action=New-ScheduledTaskAction -Execute 'C:\Windows\System32\cmd.exe' -Argument '/c C:\ProgramData\P4DemoApp\run.cmd' -WorkingDirectory "$root\app"
$principal=New-ScheduledTaskPrincipal -UserId 'NT AUTHORITY\NETWORK SERVICE' -LogonType ServiceAccount
$trigger=New-ScheduledTaskTrigger -AtStartup
$settings=New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName P4DemoApp -Action $action -Principal $principal -Trigger $trigger -Settings $settings -Force | Out-Null
New-NetFirewallRule -DisplayName 'P4 Demo 8765 LAN' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8765 -RemoteAddress LocalSubnet -ErrorAction SilentlyContinue | Out-Null
Start-ScheduledTask P4DemoApp
Start-Sleep -Seconds 3
Get-Content "$root\data\service.log" -Tail 10
(Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8765/).StatusCode
Copy-Item "$root\app\custom-security\P4Login.aspx" 'E:\PowerBI\PBIRS\ReportServer\P4Login.aspx' -Force
Write-Output "Backup: $backup"
