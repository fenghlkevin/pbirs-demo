param([string]$Root='C:\ProgramData\P6WindowsDemo')
$ErrorActionPreference='Stop'
. (Join-Path $Root 'environment.local.ps1')
$port=if($env:P6_BACKEND_PORT){[int]$env:P6_BACKEND_PORT}else{8766}
Stop-ScheduledTask -TaskName P6WindowsGateway
Stop-ScheduledTask -TaskName P6WindowsBackend
# Stopping PowerShell's scheduled task can leave its Python child running.
$owners=@(Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique)
foreach($ownerId in $owners){
 $process=Get-CimInstance Win32_Process -Filter "ProcessId=$ownerId"
 if($process.Name -ne 'python.exe' -or $process.CommandLine -notmatch '(?i)\bad_server\.py\b'){
  throw "Port $port is owned by an unexpected process; refusing to terminate it"
 }
 Stop-Process -Id $ownerId -Force
}
Start-ScheduledTask -TaskName P6WindowsBackend
for($i=0;$i -lt 20;$i++){
 Start-Sleep -Milliseconds 500
 $owners=@(Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique)
 if($owners.Count -eq 1){break}
}
if($owners.Count -ne 1){throw 'Demo backend did not start with exactly one listening process'}
Start-ScheduledTask -TaskName P6WindowsGateway
Write-Output ('Demo restarted; single backend process: '+$owners[0])
