[Console]::OutputEncoding=New-Object Text.UTF8Encoding($false)
$ErrorActionPreference='Stop'
$machine=$env:COMPUTERNAME
$groups=@{}
foreach($group in Get-LocalGroup) {
 foreach($member in @(Get-LocalGroupMember -SID $group.SID -ErrorAction Stop)) {
  $sid=$member.SID.Value
  if(!$groups.ContainsKey($sid)){$groups[$sid]=@()}
  $groups[$sid]+=$machine+'\'+$group.Name
  if($group.SID.Value -like 'S-1-5-32-*'){$groups[$sid]+='BUILTIN\'+$group.Name}
 }
}
$users=@(foreach($user in Get-LocalUser){
 $sid=$user.SID.Value
 @{id=$sid;sid=$sid;principal=$machine+'\'+$user.Name;upn='';
   displayName=if($user.FullName){$user.FullName}else{$user.Name};
   enabled=[bool]$user.Enabled;groups=@('Everyone','NT AUTHORITY\Authenticated Users')+@($groups[$sid] | Where-Object {$_});
   groupSids=@();source='LOCAL'}
})
@{machine=$machine;users=$users} | ConvertTo-Json -Depth 8 -Compress
