$ErrorActionPreference='Stop'
foreach($p in @('E:\PowerBI\PBIRS\ReportServer\P4Login.aspx','C:\ProgramData\P4PbirsDemo\P4Login.aspx')) {
 $b=[IO.File]::ReadAllBytes($p)
 if(!($b.Length -ge 3 -and $b[0] -eq 239 -and $b[1] -eq 187 -and $b[2] -eq 191)) {[IO.File]::WriteAllBytes($p,([byte[]]@(239,187,191)+$b))}
}
Write-Output 'Added explicit UTF-8 BOM to login page source'
