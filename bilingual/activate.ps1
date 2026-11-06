$ErrorActionPreference='Stop'
$root='C:\ProgramData\P4DemoApp';$base='E:\PowerBI\PBIRS\ReportServer';$stamp=Get-Date -Format yyyyMMdd-HHmmss
$backup="$root\bilingual-backup-$stamp";$stage="$root\bilingual-stage-$stamp"
New-Item -ItemType Directory "$backup\app","$backup\pbirs",$stage | Out-Null
Copy-Item "$root\app\server.py","$root\app\index.html" "$backup\app"
Copy-Item "$base\P4Login.aspx" "$backup\pbirs"
if(Test-Path "$root\app\bilingual"){Copy-Item "$root\app\bilingual" "$backup\app" -Recurse}
$before=@{};foreach($name in @('rssrvpolicy.config','web.config','rsreportserver.config')){$before[$name]=(Get-FileHash "$base\$name").Hash}
Expand-Archive "$root\bilingual-update.zip" $stage -Force
Stop-ScheduledTask P4DemoApp
Start-Sleep -Seconds 1
Get-CimInstance Win32_Process | Where-Object {$_.Name -eq 'python.exe' -and $_.CommandLine -like '*P4DemoApp*server.py*'} | ForEach-Object {Stop-Process -Id $_.ProcessId -Force}
try {
 Copy-Item "$stage\app\*" "$root\app" -Recurse -Force
 Copy-Item "$stage\pbirs\P4Login.aspx" $base -Force
 Start-ScheduledTask P4DemoApp
 Start-Sleep -Seconds 2
 foreach($url in @('http://127.0.0.1:8765/','http://pbirs.example.internal/ReportServer/P4Login.aspx?lang=pt-AO','http://pbirs.example.internal/ReportServer/P4Login.aspx?lang=zh-CN')){Write-Output "$url $((Invoke-WebRequest -UseBasicParsing $url -TimeoutSec 40).StatusCode)"}
 foreach($name in $before.Keys){if($before[$name] -ne (Get-FileHash "$base\$name").Hash){throw "Configuration changed: $name"}}
 Write-Output "CONFIGURATION_HASHES_UNCHANGED; Backup=$backup"
} catch {
 Copy-Item "$backup\app\*" "$root\app" -Recurse -Force
 Copy-Item "$backup\pbirs\*" $base -Force
 Start-ScheduledTask P4DemoApp
 throw
}
