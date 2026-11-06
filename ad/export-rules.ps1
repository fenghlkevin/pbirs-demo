param([string]$BindingsPath,
      [Parameter(Mandatory=$true)][string]$OutputPath,
      [Parameter(Mandatory=$true)][string]$TomLibrary)
$ErrorActionPreference='Stop'
# Explicit report -> live model mapping. Never enumerate unrelated models or change them.
[void][Reflection.Assembly]::LoadFrom((Join-Path $TomLibrary 'Microsoft.AnalysisServices.Core.dll'))
[void][Reflection.Assembly]::LoadFrom((Join-Path $TomLibrary 'Microsoft.AnalysisServices.Tabular.dll'))
$api=$env:P4_PBIRS_URL.TrimEnd('/')+'/Reports/api/v2.0'
if($BindingsPath){$bindings=Get-Content $BindingsPath -Raw | ConvertFrom-Json}
else {
 $catalog=Invoke-RestMethod ($api+'/PowerBIReports') -UseDefaultCredentials
 $port=(Get-Content $env:P6_ENGINE_PORT_FILE -Encoding Unicode -Raw).Trim()
 if($port -notmatch '^\d+$'){throw 'Invalid embedded engine port'}
 $bindings=@($catalog.value | ForEach-Object {@{reportId=$_.Id;connectionString='Data Source=localhost:'+$port;database='@runtime'}})
}
$reports=@{}
foreach($binding in $bindings) {
 $id=([guid]$binding.reportId).ToString()
 $url=$env:P4_PBIRS_URL.TrimEnd('/')+'/Reports/api/v2.0/PowerBIReports('+$id+')'
 try {
 $modelRoles=Invoke-RestMethod ($url+'/DataModelRoles') -UseDefaultCredentials
 if(!@($modelRoles.value).Count){continue}
 $before=Invoke-RestMethod $url -UseDefaultCredentials
 $runtime=Invoke-RestMethod ($env:P4_PBIRS_URL.TrimEnd('/')+'/powerbi/api/explore/reports/'+$id+'/modelsAndExploration?preferReadOnlySession=true') -UseDefaultCredentials
 $s=New-Object Microsoft.AnalysisServices.Tabular.Server
 try {
  $s.Connect([string]$binding.connectionString)
  $db=if($binding.database -eq '@runtime'){$s.Databases.Find([string]$runtime.models[0].id)}else{$s.Databases.FindByName([string]$binding.database)}
  if(!$db){throw "Configured model unavailable for report $id"}
  $roles=@{}
  foreach($r in $db.Model.Roles) {
   $annotation=$r.Annotations.Find('PBI_Id')
   if(!$annotation -and $r.Name -eq 'RSReaderRole'){continue}
   if(!$annotation){throw "Missing model role identifier for report $id"}
   $rid=([guid]$annotation.Value).ToString()
   $rules=@(foreach($t in $r.TablePermissions){
    @{table=[string]$t.Name; expression=[string]$t.FilterExpression}
   })
   $roles[$rid]=@{name=[string]$r.Name;rules=$rules}
  }
  $after=Invoke-RestMethod $url -UseDefaultCredentials
  if($before.ModifiedDate -ne $after.ModifiedDate){throw 'Report changed during rule collection'}
  $reports[$id]=@{modifiedDate=$after.ModifiedDate;capturedAt=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds();roles=$roles}
 } finally {$s.Disconnect();$s.Dispose()}
 } catch {Write-Warning ('Rules unavailable for report '+$id)}
}
# All-or-nothing snapshot. File lives in the protected backend data directory.
$temp=$OutputPath+'.'+[guid]::NewGuid().ToString()+'.tmp'
try {
 @{reports=$reports} | ConvertTo-Json -Depth 15 | Set-Content $temp -Encoding UTF8
 Move-Item $temp $OutputPath -Force
} finally {if(Test-Path $temp){Remove-Item $temp}}
Write-Output ('Collected rules for '+$reports.Count+' reports')
