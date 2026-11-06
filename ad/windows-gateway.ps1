$ErrorActionPreference='Stop'
# Run under a dedicated Windows service account. HTTPS binding and URL ACL are
# installed by the operator; this gateway never enables anonymous authentication.
$prefix=$env:P6_PUBLIC_URL.TrimEnd('/')+'/'
$key=[Convert]::FromBase64String($env:P6_GATEWAY_KEY)
if($key.Length -lt 32){throw 'Gateway key must be at least 32 random bytes'}
$listener=New-Object Net.HttpListener
$listener.Prefixes.Add($prefix)
$listener.AuthenticationSchemes=[Net.AuthenticationSchemes]::Negotiate -bor [Net.AuthenticationSchemes]::Ntlm
$listener.Start()
try {
 while($listener.IsListening) {
  $context=$listener.GetContext()
  try {
   $request=$context.Request
   if(!$context.User.Identity.IsAuthenticated){$context.Response.StatusCode=401;continue}
   if($request.ContentLength64 -gt 1048576){$context.Response.StatusCode=413;continue}
   $buffer=New-Object IO.MemoryStream
   $request.InputStream.CopyTo($buffer)
   $body=$buffer.ToArray()
   if($body.Length -gt 1048576){$context.Response.StatusCode=413;continue}
   $user=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($context.User.Identity.Name))
   $stamp=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds().ToString()
   $nonce=[guid]::NewGuid().ToString('N')
   $sha=[Security.Cryptography.SHA256]::Create()
   $digest=([BitConverter]::ToString($sha.ComputeHash($body))).Replace('-','').ToLowerInvariant()
   $sha.Dispose()
   $message=@($request.HttpMethod,$request.RawUrl,$stamp,$nonce,$user,$digest) -join "`n"
   $hmac=New-Object Security.Cryptography.HMACSHA256
   $hmac.Key=$key
   $signature=([BitConverter]::ToString($hmac.ComputeHash([Text.Encoding]::UTF8.GetBytes($message)))).Replace('-','').ToLowerInvariant()
   $hmac.Dispose()
   $port=if($env:P6_BACKEND_PORT){$env:P6_BACKEND_PORT}else{'8766'}
   $upstream=[Net.HttpWebRequest]::Create('http://127.0.0.1:'+$port+$request.RawUrl)
   $upstream.Method=$request.HttpMethod
   $upstream.Timeout=180000
   $upstream.Proxy=$null
   $upstream.AllowAutoRedirect=$false
   $upstream.Headers['X-P6-User']=$user
   $upstream.Headers['X-P6-Time']=$stamp
   $upstream.Headers['X-P6-Nonce']=$nonce
   $upstream.Headers['X-P6-Signature']=$signature
   if($request.Headers['Origin']){$upstream.Headers['Origin']=$request.Headers['Origin']}
   if($request.ContentType){$upstream.ContentType=$request.ContentType}
   if($body.Length){$upstream.ContentLength=$body.Length;$stream=$upstream.GetRequestStream();$stream.Write($body,0,$body.Length);$stream.Close()}
   try {$response=$upstream.GetResponse()}catch [Net.WebException]{
    $response=$_.Exception.Response
    if(!$response){throw}
   }
   try {
    $context.Response.StatusCode=[int]$response.StatusCode
    $context.Response.ContentType=$response.ContentType
    $context.Response.Headers['Cache-Control']='no-store'
    $context.Response.Headers['X-Content-Type-Options']='nosniff'
    $context.Response.Headers['Content-Security-Policy']="frame-ancestors 'self'; object-src 'none'; base-uri 'self'"
    $response.GetResponseStream().CopyTo($context.Response.OutputStream)
   } finally {$response.Close()}
  } catch {$context.Response.StatusCode=502}
  finally {$context.Response.Close()}
 }
} finally {$listener.Stop();$listener.Close()}
