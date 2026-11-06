$ErrorActionPreference='Stop'
foreach($p in @('E:\PowerBI\PBIRS\ReportServer\P4Login.aspx','C:\ProgramData\P4PbirsDemo\P4Login.aspx')) {
 $s=Get-Content $p -Raw
 $s=$s.Replace('</script></body></html>','</scr"+"ipt></body></html>')
 [IO.File]::WriteAllText($p,$s)
}
Write-Output 'Escaped generated browser script end tag in ASPX source'
