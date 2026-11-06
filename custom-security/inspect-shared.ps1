$ErrorActionPreference='Stop'
Get-Command python,py -ErrorAction SilentlyContinue | Select Name,Source | ConvertTo-Json
Get-NetTCPConnection -State Listen | Where LocalPort -In 8765,8766 | Select LocalAddress,LocalPort | ConvertTo-Json
Get-NetConnectionProfile | Select InterfaceAlias,NetworkCategory | ConvertTo-Json
