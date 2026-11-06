Get-Content 'E:\PowerBI\PBIRS\LogFiles\RSPowerBI_2026_11_04_19_51_25.log' -Tail 350 | Select-String 'role|security|rls|Imperson|Effective|p4:|EnsureDbLoaded|modelId|Session' | Select-Object -Last 45
