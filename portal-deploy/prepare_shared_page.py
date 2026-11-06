from pathlib import Path
root=Path(__file__).resolve().parents[1]
imports=['System','System.IO','System.Text','System.Collections.Generic','System.Collections.Concurrent','System.Security.Cryptography','System.Text.RegularExpressions','System.Web.Script.Serialization','System.Web.Security']
source='''
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
 if(current!=null&&Regex.IsMatch(current.Value,@"\\A[a-f0-9]{64}\\z"))return current.Value;
 byte[] bytes=new byte[32];using(RandomNumberGenerator random=RandomNumberGenerator.Create())random.GetBytes(bytes);
 string value=BitConverter.ToString(bytes).Replace("-","").ToLowerInvariant();
 HttpCookie cookie=new HttpCookie("P4PortalCsrf",value);cookie.HttpOnly=true;cookie.Secure=Request.IsSecureConnection;cookie.Path="/ReportServer/P4Portal.aspx";cookie.SameSite=SameSiteMode.Lax;Response.Cookies.Add(cookie);return value;
}
string Verify(string username,string password) {
 if(username==null||password==null||username.Length>64||password.Length>512)return null;
 string bucket=Request.UserHostAddress+"|"+username;
 Tuple<DateTime,int> old;Attempts.TryGetValue(bucket,out old);
 if(old!=null&&old.Item1>DateTime.UtcNow.AddMinutes(-5)&&old.Item2>=10)return null;
 Dictionary<string,object> all=new JavaScriptSerializer().Deserialize<Dictionary<string,object>>(File.ReadAllText(Path.Combine(Home,"system-users.json")));
 object raw;Dictionary<string,object> account=all.TryGetValue(username,out raw)?raw as Dictionary<string,object>:null;
 string salt=account==null?"00000000000000000000000000000000":Convert.ToString(account["salt"]);
 byte[] saltBytes=new byte[salt.Length/2];for(int i=0;i<saltBytes.Length;i++)saltBytes[i]=Convert.ToByte(salt.Substring(i*2,2),16);
 int iterations=account==null?600000:Convert.ToInt32(account["iterations"]);
 string digest;using(Rfc2898DeriveBytes derive=new Rfc2898DeriveBytes(password,saltBytes,iterations,HashAlgorithmName.SHA256))digest=BitConverter.ToString(derive.GetBytes(32)).Replace("-","").ToLowerInvariant();
 if(account!=null&&Equal(digest,Convert.ToString(account["passwordHash"]))) {
  Attempts.TryRemove(bucket,out old);string principal=Convert.ToString(account["principal"]);
  return Regex.IsMatch(principal,@"\\Ap4:[A-Za-z0-9_-]{1,64}\\z")?principal:null;
 }
 Attempts.AddOrUpdate(bucket,new Tuple<DateTime,int>(DateTime.UtcNow,1),(k,previous)=>previous.Item1<DateTime.UtcNow.AddMinutes(-5)?new Tuple<DateTime,int>(DateTime.UtcNow,1):new Tuple<DateTime,int>(previous.Item1,previous.Item2+1));return null;
}
void RenderLogin(string target,string error) {
 string csrf=Csrf();
 Response.ContentType="text/html; charset=utf-8";
 Response.Write("<!doctype html><html lang='zh-CN'><meta charset='utf-8'><title>P4 系统登录 · 报表门户</title><style>body{margin:0;background:#f1f5fa;color:#17304c;font:16px system-ui}header{background:#082e5c;color:white;padding:24px 36px}main{max-width:440px;margin:60px auto;background:white;padding:32px;border-radius:14px;box-shadow:0 8px 32px #17304c16}h1{font-size:23px;margin:0}h2{font-size:22px}p{line-height:1.6;color:#53677f}label{display:block;margin-top:18px}input{box-sizing:border-box;width:100%;padding:12px;margin-top:8px;border:1px solid #c7d4e3;border-radius:7px}button{margin-top:24px;padding:12px;width:100%;background:#0b4c91;color:white;border:0;border-radius:7px;font-size:16px;cursor:pointer}.error{color:#ae2525}a{color:#0b4c91}</style><header><h1>P4 · 报表门户统一登录</h1></header><main><h2>登录系统账号</h2><p>使用 P4 系统账号进入 Power BI 报表门户，无需 Windows 账号。</p>");
 if(!String.IsNullOrEmpty(error))Response.Write("<p class='error' role='alert'>"+HttpUtility.HtmlEncode(error)+"</p>");
 if(User!=null&&User.Identity.IsAuthenticated)Response.Write("<p>当前报表身份："+HttpUtility.HtmlEncode(User.Identity.Name)+" · <a href='"+HttpUtility.HtmlAttributeEncode(PortalNavigation.ForUser(User.Identity.Name,target))+"'>继续访问门户</a></p>");
 Response.Write("<form method='post' action='/ReportServer/P4Portal.aspx'><input type='hidden' name='csrf' value='"+csrf+"'><input type='hidden' name='returnUrl' value='"+HttpUtility.HtmlAttributeEncode(target)+"'><label>系统账号<input name='username' autocomplete='username' maxlength='64' required></label><label>密码<input name='password' type='password' autocomplete='current-password' maxlength='512' required></label><button type='submit'>登录并打开门户</button></form><p>普通用户查看已授权报表；管理账号进入报表管理门户。</p></main></html>");
}
protected void Page_Load(object sender,EventArgs e) {
 Response.SuppressFormsAuthenticationRedirect=true;Response.Cache.SetCacheability(HttpCacheability.NoCache);Response.Cache.SetNoStore();Response.AddHeader("Referrer-Policy","no-referrer");Response.AddHeader("X-Frame-Options","DENY");Response.AddHeader("X-Content-Type-Options","nosniff");
 string target=PortalNavigation.SafeReturn(Request.HttpMethod=="POST"?Request.Form["returnUrl"]:Request.QueryString["returnUrl"]);
 if(Request.HttpMethod=="GET"){RenderLogin(target,null);return;}
 if(Request.HttpMethod!="POST"){Response.StatusCode=405;return;}
 HttpCookie csrf=Request.Cookies["P4PortalCsrf"];
 if(csrf==null||!Equal(csrf.Value,Request.Form["csrf"])) {Response.StatusCode=403;RenderLogin(target,"登录请求已失效，请重试。");return;}
 string principal;
 try { principal=Verify(Request.Form["username"],Request.Form["password"]); }
 catch {Response.StatusCode=503;RenderLogin(target,"登录服务暂不可用，请稍后重试。");return;}
 if(principal==null){Response.StatusCode=401;RenderLogin(target,"账号或密码错误，或尝试次数过多。");return;}
 string ticket=Issue(principal,PortalNavigation.ForUser(principal,target));
 Response.ContentType="text/html; charset=utf-8";
 Response.Write("<!doctype html><html lang='zh-CN'><meta charset='utf-8'><title>正在打开报表门户</title><meta name='referrer' content='no-referrer'><body><p>已登录，正在打开报表门户…</p><form id='bridge' method='post' action='/ReportServer/P4Login.aspx'><input type='hidden' name='ticket' value='"+HttpUtility.HtmlAttributeEncode(ticket)+"'><button type='submit'>继续打开门户</button></form><script>document.getElementById('bridge').submit();</script></body></html>");
}
'''
nav=(root/'portal-deploy'/'PortalNavigation.cs.txt').read_text()
page='<%@ Page Language="C#" %>\n<%@ Assembly Name="System.Web.Extensions" %>\n'+''.join('<%@ Import Namespace="'+n+'" %>\n' for n in imports)+'<script runat="server">\n'+nav+source+'\n</script>\n'
(root/'custom-security'/'P4Portal.aspx').write_text(page)
print('Prepared shared system-login page')
