<%@ Page Language="C#" CodePage="65001" %>
<%@ Assembly Name="System.Web.Extensions" %>
<%@ Import Namespace="System" %>
<%@ Import Namespace="System.IO" %>
<%@ Import Namespace="System.Text" %>
<%@ Import Namespace="System.Collections.Generic" %>
<%@ Import Namespace="System.Collections.Concurrent" %>
<%@ Import Namespace="System.Security.Cryptography" %>
<%@ Import Namespace="System.Text.RegularExpressions" %>
<%@ Import Namespace="System.Web.Script.Serialization" %>
<%@ Import Namespace="System.Web.Security" %>
<script runat="server">
 public static class LoginTickets {
  static string Home { get { return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData),"P4PbirsDemo"); } }
  public static bool Principal(string name) { return name != null && Regex.IsMatch(name,@"\Ap4:[A-Za-z0-9_-]{1,64}\z"); }
  static byte[] Decode(string value) { string s=value.Replace('-','+').Replace('_','/'); return Convert.FromBase64String(s.PadRight((s.Length+3)/4*4,'=')); }
  static string Fail(string reason) { try { File.WriteAllText(Path.Combine(Home,"used","last-failure.txt"),reason); } catch {} return null; }
  public static string Consume(string token) {
   if(String.IsNullOrEmpty(token)||token.Length>4096) return Fail("validation-1");
   try {
    string[] parts=token.Split('.'); if(parts.Length!=2)return Fail("validation-2");
    byte[] key=Convert.FromBase64String(File.ReadAllText(Path.Combine(Home,"ticket-key.txt")).Trim());
    byte[] expected; using(HMACSHA256 h=new HMACSHA256(key))expected=h.ComputeHash(Encoding.ASCII.GetBytes(parts[0]));
    byte[] actual=Decode(parts[1]); int diff=actual.Length^expected.Length;
    for(int i=0;i<expected.Length;i++)diff|=expected[i]^(i<actual.Length?actual[i]:0);
    if(diff!=0)return Fail("validation-3");
    Dictionary<string,object> data=new JavaScriptSerializer().Deserialize<Dictionary<string,object>>(Encoding.UTF8.GetString(Decode(parts[0])));
    string user=Convert.ToString(data["sub"]), nonce=Convert.ToString(data["jti"]);
    long now=DateTimeOffset.UtcNow.ToUnixTimeSeconds(), exp=Convert.ToInt64(data["exp"]), issued=Convert.ToInt64(data["iat"]);
    if(!Principal(user)||Convert.ToString(data["iss"])!="p4-demo"||Convert.ToString(data["aud"])!="pbirs-demo"||issued>now+10||now>exp||exp-issued>60||issued<now-70||!Regex.IsMatch(nonce,@"\A[a-f0-9]{32}\z"))return Fail("validation-4");
    // CreateNew is atomic across report-server processes. Used tickets cannot be replayed.
    string used=Path.Combine(Home,"used");
    using(FileStream file=new FileStream(Path.Combine(used,nonce),FileMode.CreateNew,FileAccess.Write,FileShare.None))file.WriteByte(1);
    return user;
   } catch(Exception error) { return Fail(error.GetType().Name+":"+error.Message); }
  }
 }
public static class PortalNavigation {
 public static string SafeReturn(string input) {
  string value=String.IsNullOrEmpty(input)?"/Reports":input;
  for(int count=0;count<3;count++) {
   if(value.StartsWith("/ReportServer/localredirect",StringComparison.OrdinalIgnoreCase)) {
    int query=value.IndexOf('?'); value=query<0?"/Reports":HttpUtility.ParseQueryString(value.Substring(query+1))["url"]??"/Reports";
   } else if(value.StartsWith("%2f",StringComparison.OrdinalIgnoreCase)) value=HttpUtility.UrlDecode(value);
   else break;
  }
  if(value.IndexOfAny(new char[]{'\\','\r','\n'})>=0||value.StartsWith("//"))return "/Reports";
  string path=value.Split('?')[0];string decoded=Uri.UnescapeDataString(path);
  if(decoded.IndexOf('\\')>=0||decoded.Contains("..")||decoded.Contains("//"))return "/Reports";
  if(!(path.Equals("/Reports",StringComparison.OrdinalIgnoreCase)||path.StartsWith("/Reports/",StringComparison.OrdinalIgnoreCase)))return "/Reports";
  return value;
 }
 public static string ForUser(string user,string input) {
  string value=SafeReturn(input);
  if(user!="p4:portaladmin"&&user!="p4:maintenance"&&(value.Equals("/Reports",StringComparison.OrdinalIgnoreCase)||value.Equals("/Reports/",StringComparison.OrdinalIgnoreCase)))return "/Reports/browse/P4_Identity_Demo";
  return value;
 }
}

static string Home { get { return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData),"P4PbirsDemo"); } }
static ConcurrentDictionary<string,Tuple<DateTime,int>> Attempts=new ConcurrentDictionary<string,Tuple<DateTime,int>>();
static string B64(byte[] bytes) { return Convert.ToBase64String(bytes).TrimEnd('=').Replace('+','-').Replace('/','_'); }
static bool Equal(string left,string right) { if(left==null||right==null)return false;int diff=left.Length^right.Length;for(int i=0;i<left.Length;i++)diff|=left[i]^(i<right.Length?right[i]:0);return diff==0; }
static string Issue(string principal,string target) {
 long now=DateTimeOffset.UtcNow.ToUnixTimeSeconds();
 byte[] nonce=new byte[16];using(RandomNumberGenerator random=RandomNumberGenerator.Create())random.GetBytes(nonce);
 Dictionary<string,object> claims=new Dictionary<string,object>{{"iss","p4-demo"},{"aud","pbirs-demo"},{"sub",principal},{"iat",now},{"exp",now+30},{"jti",BitConverter.ToString(nonce).Replace("-","").ToLowerInvariant()},{"flow","browser"},{"returnUrl",target}};
 string body=B64(Encoding.UTF8.GetBytes(new JavaScriptSerializer().Serialize(claims)));
 byte[] key=Convert.FromBase64String(File.ReadAllText(Path.Combine(Home,"ticket-key.txt")).Trim());
 using(HMACSHA256 hmac=new HMACSHA256(key))return body+"."+B64(hmac.ComputeHash(Encoding.ASCII.GetBytes(body)));
}
string Csrf() {
 HttpCookie current=Request.Cookies["P4PortalCsrf"];
 if(current!=null&&Regex.IsMatch(current.Value,@"\A[a-f0-9]{64}\z"))return current.Value;
 byte[] bytes=new byte[32];using(RandomNumberGenerator random=RandomNumberGenerator.Create())random.GetBytes(bytes);
 string value=BitConverter.ToString(bytes).Replace("-","").ToLowerInvariant();
 HttpCookie cookie=new HttpCookie("P4PortalCsrf",value);cookie.HttpOnly=true;cookie.Secure=Request.IsSecureConnection;cookie.Path="/ReportServer/P4Login.aspx";cookie.SameSite=SameSiteMode.Lax;Response.Cookies.Add(cookie);return value;
}
string Verify(string username,string password) {
 if(username==null||password==null||username.Length>64||password.Length>512)return null;
 string bucket=Request.UserHostAddress+"|"+username;
 Tuple<DateTime,int> old;Attempts.TryGetValue(bucket,out old);
 if(old!=null&&old.Item1>DateTime.UtcNow.AddMinutes(-5)&&old.Item2>=10)return null;
 string requestBody=new JavaScriptSerializer().Serialize(new Dictionary<string,object>{{"username",username},{"password",password}});
 string stamp=DateTimeOffset.UtcNow.ToUnixTimeSeconds().ToString();
 string nonce=Guid.NewGuid().ToString("N");
 byte[] key=Convert.FromBase64String(File.ReadAllText(Path.Combine(Home,"ticket-key.txt")).Trim());
 string signature;using(HMACSHA256 hmac=new HMACSHA256(key))signature=BitConverter.ToString(hmac.ComputeHash(Encoding.UTF8.GetBytes(stamp+"\n"+nonce+"\n"+requestBody))).Replace("-","").ToLowerInvariant();
 System.Net.HttpWebRequest request=(System.Net.HttpWebRequest)System.Net.WebRequest.Create("http://127.0.0.1:8765/internal/authenticate");
 request.Proxy=null;request.Method="POST";request.ContentType="application/json; charset=utf-8";request.Timeout=10000;
 request.Headers["X-P4-Time"]=stamp;request.Headers["X-P4-Nonce"]=nonce;request.Headers["X-P4-Signature"]=signature;
 byte[] body=Encoding.UTF8.GetBytes(requestBody);request.ContentLength=body.Length;
 using(Stream stream=request.GetRequestStream())stream.Write(body,0,body.Length);
 try {
  using(System.Net.HttpWebResponse response=(System.Net.HttpWebResponse)request.GetResponse())
  using(StreamReader reader=new StreamReader(response.GetResponseStream(),Encoding.UTF8)) {
   Dictionary<string,object> result=new JavaScriptSerializer().Deserialize<Dictionary<string,object>>(reader.ReadToEnd());
   string principal=Convert.ToString(result["principal"]);
   if(LoginTickets.Principal(principal)){Attempts.TryRemove(bucket,out old);return principal;}
  }
 } catch(System.Net.WebException error) {
  System.Net.HttpWebResponse response=error.Response as System.Net.HttpWebResponse;
  if(response==null||((int)response.StatusCode!=401&&(int)response.StatusCode!=429))throw;
  response.Close();
 }
 Attempts.AddOrUpdate(bucket,new Tuple<DateTime,int>(DateTime.UtcNow,1),(k,previous)=>previous.Item1<DateTime.UtcNow.AddMinutes(-5)?new Tuple<DateTime,int>(DateTime.UtcNow,1):new Tuple<DateTime,int>(previous.Item1,previous.Item2+1));return null;
}
string Language {
 get { string value=Request.Form["lang"]??Request.QueryString["lang"];
  if(String.IsNullOrEmpty(value)&&Request.Cookies["P4DemoLang"]!=null)value=Request.Cookies["P4DemoLang"].Value;
  return value=="zh-CN"?"zh-CN":"pt-AO";
 }
}
string L(string zh,string pt) { return Language=="zh-CN"?zh:pt; }
void RenderLogin(string target,string error) {
 string csrf=Csrf();
 Response.ContentType="text/html; charset=utf-8";
 Response.Write("<!doctype html><html lang='"+Language+"'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>"+L("P4 系统登录 · 报表门户","P4 · Acesso ao portal de relatórios")+"</title><style>body{margin:0;background:#f1f5fa;color:#17304c;font:16px system-ui}header{background:#082e5c;color:white;padding:24px 36px;display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap}header a{color:white;padding:8px}main{max-width:440px;margin:60px auto;background:white;padding:32px;border-radius:14px;box-shadow:0 8px 32px #17304c16}h1{font-size:23px;margin:0}h2{font-size:22px}p{line-height:1.6;color:#53677f}label{display:block;margin-top:18px}input{box-sizing:border-box;width:100%;padding:12px;margin-top:8px;border:1px solid #c7d4e3;border-radius:7px}button{margin-top:24px;padding:12px;width:100%;background:#0b4c91;color:white;border:0;border-radius:7px;font-size:16px;cursor:pointer}.error{color:#ae2525}a{color:#0b4c91}@media(max-width:560px){main{margin:24px 16px;padding:24px}header{padding:20px}}</style><header><h1>"+L("P4 · 报表门户统一登录","P4 · Portal de relatórios")+"</h1><nav aria-label='Idioma / 语言'><a href='?lang=pt-AO&amp;returnUrl="+HttpUtility.UrlEncode(target)+"' lang='pt-AO'>Português (Angola)</a><a href='?lang=zh-CN&amp;returnUrl="+HttpUtility.UrlEncode(target)+"' lang='zh-CN'>中文</a></nav></header><main><h2>"+L("登录系统账号","Entrar com a sua conta")+"</h2><p>"+L("使用 P4 系统账号进入 Power BI 报表门户，无需 Windows 账号。","Utilize a sua conta P4 para entrar no portal Power BI. Não é necessária uma conta Windows.")+"</p>");
 if(!String.IsNullOrEmpty(error))Response.Write("<p class='error' role='alert'>"+HttpUtility.HtmlEncode(error)+"</p>");
 if(User!=null&&User.Identity.IsAuthenticated)Response.Write("<p>"+L("当前报表身份：","Identidade actual: ")+HttpUtility.HtmlEncode(User.Identity.Name)+" · <a href='"+HttpUtility.HtmlAttributeEncode(PortalNavigation.ForUser(User.Identity.Name,target))+"'>"+L("继续访问门户","Continuar para o portal")+"</a></p>");
 Response.Write("<form method='post' action='/ReportServer/P4Login.aspx'><input type='hidden' name='csrf' value='"+csrf+"'><input type='hidden' name='returnUrl' value='"+HttpUtility.HtmlAttributeEncode(target)+"'><input type='hidden' name='lang' value='"+Language+"'><label>"+L("系统账号","Utilizador")+"<input name='username' autocomplete='username' maxlength='64' required></label><label>"+L("密码","Palavra-passe")+"<input name='password' type='password' autocomplete='current-password' maxlength='512' required></label><button type='submit'>"+L("登录并打开门户","Entrar no portal")+"</button></form><p>"+L("普通用户查看已授权报表；管理账号进入报表管理门户。","Os utilizadores consultam os relatórios autorizados. Os administradores podem gerir o portal.")+"</p></main></html>");
}
protected void Page_Load(object sender,EventArgs e) {
 HttpCookie languageCookie=new HttpCookie("P4DemoLang",Language);languageCookie.Path="/";languageCookie.Expires=DateTime.UtcNow.AddYears(1);languageCookie.SameSite=SameSiteMode.Lax;languageCookie.Secure=Request.IsSecureConnection;Response.Cookies.Add(languageCookie);
 Response.AddHeader("Content-Language",Language);
 Response.ContentEncoding=Encoding.UTF8;Response.Charset="utf-8";Response.SuppressFormsAuthenticationRedirect=true;Response.Cache.SetCacheability(HttpCacheability.NoCache);Response.Cache.SetNoStore();Response.AddHeader("Referrer-Policy","no-referrer");Response.AddHeader("X-Content-Type-Options","nosniff");
 // Ticket POSTs remain compatible with the third-party backend session bridge.
 if(Request.HttpMethod=="POST"&&!String.IsNullOrEmpty(Request.Form["ticket"])) {
  Response.ContentType="application/json";string ticket=Request.Form["ticket"];string user=LoginTickets.Consume(ticket);
  if(user==null){Response.StatusCode=401;Response.Write("{\"error\":\"Invalid, expired or used identity ticket\"}");return;}
  FormsAuthentication.SetAuthCookie(user,false);
  string part=ticket.Split('.')[0].Replace('-','+').Replace('_','/');part=part.PadRight((part.Length+3)/4*4,'=');
  Dictionary<string,object> claims=new JavaScriptSerializer().Deserialize<Dictionary<string,object>>(Encoding.UTF8.GetString(Convert.FromBase64String(part)));
  if(claims.ContainsKey("flow")&&Convert.ToString(claims["flow"])=="browser") {
   string destination=PortalNavigation.ForUser(user,claims.ContainsKey("returnUrl")?Convert.ToString(claims["returnUrl"]):"/Reports");
   Response.StatusCode=303;Response.RedirectLocation=destination;Context.ApplicationInstance.CompleteRequest();return;
  }
  Response.Write("{\"authenticated\":true}");return;
 }
 Response.AddHeader("X-Frame-Options","DENY");
 string target=PortalNavigation.SafeReturn(Request.HttpMethod=="POST"?Request.Form["returnUrl"]:(Request.QueryString["ReturnUrl"]??Request.QueryString["returnUrl"]));
 if(Request.HttpMethod=="GET"){RenderLogin(target,null);return;}
 if(Request.HttpMethod!="POST"){Response.StatusCode=405;return;}
 HttpCookie csrf=Request.Cookies["P4PortalCsrf"];
 if(csrf==null||!Equal(csrf.Value,Request.Form["csrf"])) {Response.StatusCode=403;RenderLogin(target,L("登录请求已失效，请重试。","O pedido de início de sessão expirou. Tente novamente."));return;}
 string principal;
 try { principal=Verify(Request.Form["username"],Request.Form["password"]); }
 catch {Response.StatusCode=503;RenderLogin(target,L("登录服务暂不可用，请稍后重试。","O serviço de autenticação está indisponível. Tente novamente mais tarde."));return;}
 if(principal==null){Response.StatusCode=401;RenderLogin(target,L("账号或密码错误，或尝试次数过多。","Utilizador ou palavra-passe incorrectos, ou demasiadas tentativas."));return;}
 string ticketForBrowser=Issue(principal,PortalNavigation.ForUser(principal,target));
 Response.ContentType="text/html; charset=utf-8";
 Response.Write("<!doctype html><html lang='"+Language+"'><meta charset='utf-8'><title>"+L("正在打开报表门户","A abrir o portal de relatórios")+"</title><meta name='referrer' content='no-referrer'><body><p>"+L("已登录，正在打开报表门户…","Sessão iniciada. A abrir o portal de relatórios…")+"</p><form id='bridge' method='post' action='/ReportServer/P4Login.aspx'><input type='hidden' name='ticket' value='"+HttpUtility.HtmlAttributeEncode(ticketForBrowser)+"'><button type='submit'>"+L("继续打开门户","Continuar para o portal")+"</button></form><script>document.getElementById('bridge').submit();</scr"+"ipt></body></html>");
}

</script>
