$ErrorActionPreference='Stop'
# Run under a dedicated Windows service account. HTTPS binding and URL ACL are
# installed by the operator; Demo authenticates requests with its own session cookie. PBIRS stays Windows authenticated.
$prefix=$env:P6_PUBLIC_URL.TrimEnd('/')+'/'
$listener=New-Object Net.HttpListener
$listener.Prefixes.Add($prefix)
$listener.AuthenticationSchemes=[Net.AuthenticationSchemes]::Anonymous
$listener.Start()
try {
 while($listener.IsListening) {
  $context=$listener.GetContext()
  try {
   $request=$context.Request
   if($request.ContentLength64 -gt 16777216){$context.Response.StatusCode=413;continue}
   $buffer=New-Object IO.MemoryStream
   $request.InputStream.CopyTo($buffer)
   $body=$buffer.ToArray()
   if($body.Length -gt 16777216){$context.Response.StatusCode=413;continue}
   $port=if($env:P6_BACKEND_PORT){$env:P6_BACKEND_PORT}else{'8766'}
   $upstream=[Net.HttpWebRequest]::Create('http://127.0.0.1:'+$port+$request.RawUrl)
   $upstream.Method=$request.HttpMethod
   $upstream.Timeout=180000
   $upstream.Proxy=$null
   $upstream.AllowAutoRedirect=$false
   if($request.Headers['Cookie']){$upstream.Headers['Cookie']=$request.Headers['Cookie']}
   if($request.Headers['Accept-Encoding']){$upstream.Headers['Accept-Encoding']=$request.Headers['Accept-Encoding']}
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
    $context.Response.Headers['Cache-Control']=if($response.Headers['Cache-Control']){$response.Headers['Cache-Control']}else{'no-store'}
    foreach($cookie in $response.Headers.GetValues('Set-Cookie')){if($cookie){$context.Response.Headers.Add('Set-Cookie',$cookie)}}
    if($response.Headers['Content-Disposition']){$context.Response.Headers['Content-Disposition']=$response.Headers['Content-Disposition']}
    if($response.Headers['Content-Encoding']){$context.Response.Headers['Content-Encoding']=$response.Headers['Content-Encoding']}
    if($response.Headers['Location']){$context.Response.Headers['Location']=$response.Headers['Location']}
    $context.Response.Headers['X-Content-Type-Options']='nosniff'
    $context.Response.Headers['Content-Security-Policy']="frame-ancestors 'self'; object-src 'none'; base-uri 'self'"
    $response.GetResponseStream().CopyTo($context.Response.OutputStream)
   } finally {$response.Close()}
  } catch {$context.Response.StatusCode=502}
  finally {$context.Response.Close()}
 }
} finally {$listener.Stop();$listener.Close()}
