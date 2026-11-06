$ErrorActionPreference='Stop'
Copy-Item 'C:\ProgramData\P4CompatibilityProbe\LegacyCompatibility.cs' 'C:\ProgramData\P4PbirsDemo\P4Security.cs' -Force
Write-Output 'Canonical build source synchronized with deployed compatibility DLL'
