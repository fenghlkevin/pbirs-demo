$ErrorActionPreference='Stop'
Add-Type @'
using System;using System.Runtime.InteropServices;
public static class P4SignatureCheck {
[DllImport("mscoree.dll",CharSet=CharSet.Unicode)]
public static extern bool StrongNameSignatureVerificationEx(string path,bool forceVerification,out bool wasVerified);
}
'@
$p='C:\ProgramData\P4PbirsSignedBuild\P4.Reporting.dll'
$verified=$false;$valid=[P4SignatureCheck]::StrongNameSignatureVerificationEx($p,$true,[ref]$verified)
if(!$valid -or !$verified){throw 'Strong-name signature verification failed'}
[PSCustomObject]@{Assembly=[Reflection.AssemblyName]::GetAssemblyName($p).FullName;SHA256=(Get-FileHash $p -Algorithm SHA256).Hash;SignatureValid=$valid;Verified=$verified} | ConvertTo-Json
