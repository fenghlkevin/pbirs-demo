$asm=[Reflection.Assembly]::LoadFrom('E:\PowerBI\PBIRS\ReportServer\bin\Microsoft.ReportingServices.Interfaces.dll')
$items=@()
foreach($name in @('IAuthenticationExtension2','IAuthorizationExtension')) {
 $type=$asm.GetType('Microsoft.ReportingServices.Interfaces.'+$name)
 foreach($method in $type.GetMethods()){$items += [PSCustomObject]@{Type=$name;Method=$method.ToString();Critical=$method.IsSecurityCritical;SafeCritical=$method.IsSecuritySafeCritical;Transparent=$method.IsSecurityTransparent}}
}
$items | ConvertTo-Json
[xml]$web=Get-Content 'E:\PowerBI\PBIRS\ReportServer\web.config';$web.configuration.'system.web'.trust.OuterXml
