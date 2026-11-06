$root='C:\ProgramData\P4RlsDemo'
New-Item -ItemType Directory -Force $root | Out-Null
icacls $root /inheritance:r /grant:r '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' 'NT SERVICE\MSSQLServerOLAPService:(OI)(CI)M' | Out-Null
