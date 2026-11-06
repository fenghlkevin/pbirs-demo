$ErrorActionPreference='Stop'
$build='C:\ProgramData\P4PbirsSignedBuild';$work='C:\ProgramData\P4PbirsDemo';$base='E:\PowerBI\PBIRS'
New-Item -ItemType Directory $build -Force | Out-Null
& icacls $build /inheritance:r /grant:r 'BUILTIN\Administrators:(OI)(CI)F' 'NT AUTHORITY\SYSTEM:(OI)(CI)F' | Out-Null
$parameters=New-Object Security.Cryptography.CspParameters
$parameters.ProviderType=24;$parameters.KeyNumber=2;$parameters.Flags=[Security.Cryptography.CspProviderFlags]::UseMachineKeyStore
$rsa=New-Object Security.Cryptography.RSACryptoServiceProvider(2048,$parameters)
$rsa.PersistKeyInCsp=$false
[IO.File]::WriteAllBytes("$build\P4.Reporting.snk",$rsa.ExportCspBlob($true));$rsa.Dispose()
$source=Get-Content "$work\P4Security.cs" -Raw -Encoding UTF8
if($source -notmatch 'AssemblyVersion'){$source=$source.Replace('namespace P4.Reporting {','[assembly: System.Reflection.AssemblyVersion("1.0.0.0")]'+[Environment]::NewLine+'namespace P4.Reporting {')}
[IO.File]::WriteAllText("$build\P4Security.cs",$source)
& C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /nologo /target:library /keyfile:"$build\P4.Reporting.snk" /out:"$build\P4.Reporting.dll" /reference:"$base\ReportServer\bin\Microsoft.ReportingServices.Interfaces.dll" /reference:System.Web.dll /reference:System.Web.Extensions.dll "$build\P4Security.cs"
if($LASTEXITCODE -ne 0){throw 'Signed build failed'}
$assembly=[Reflection.AssemblyName]::GetAssemblyName("$build\P4.Reporting.dll")
$publicKey=([BitConverter]::ToString($assembly.GetPublicKey())).Replace('-','')
$grant='<CodeGroup class="UnionCodeGroup" version="1" Name="P4SignedExtensionOnly" PermissionSetName="FullTrust"><IMembershipCondition class="StrongNameMembershipCondition" version="1" PublicKeyBlob="'+$publicKey+'" Name="P4.Reporting" AssemblyVersion="1.0.0.0" /></CodeGroup>'
[IO.File]::WriteAllText("$build\proposed-trust.xml",$grant)
Write-Output ('Prepared only; not installed: '+$assembly.FullName)
Write-Output 'Trust proposal matches only this signing key + P4.Reporting + version 1.0.0.0. Existing trust configuration unchanged.'
