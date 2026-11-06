from pathlib import Path
root=Path(__file__).resolve().parents[1]
login=(root/'custom-security/P4Login.aspx').read_text();portal=(root/'custom-security/P4Portal.aspx').read_text()
validator=login[login.index(' public static class LoginTickets'):login.index('public static class PortalNavigation')]
prefix=portal[:portal.index('<script runat="server">')+len('<script runat="server">')]
helpers=portal[portal.index('public static class PortalNavigation'):portal.index('protected void Page_Load')]
helpers=helpers.replace('/ReportServer/P4Portal.aspx','/ReportServer/P4Login.aspx')
event='''protected void Page_Load(object sender,EventArgs e) {
 Response.SuppressFormsAuthenticationRedirect=true;Response.Cache.SetCacheability(HttpCacheability.NoCache);Response.Cache.SetNoStore();Response.AddHeader("Referrer-Policy","no-referrer");Response.AddHeader("X-Content-Type-Options","nosniff");
 // Ticket POSTs remain compatible with the third-party backend session bridge.
 if(Request.HttpMethod=="POST"&&!String.IsNullOrEmpty(Request.Form["ticket"])) {
  Response.ContentType="application/json";string ticket=Request.Form["ticket"];string user=LoginTickets.Consume(ticket);
  if(user==null){Response.StatusCode=401;Response.Write("{\\"error\\":\\"Invalid, expired or used identity ticket\\"}");return;}
  FormsAuthentication.SetAuthCookie(user,false);
  string part=ticket.Split('.')[0].Replace('-','+').Replace('_','/');part=part.PadRight((part.Length+3)/4*4,'=');
  Dictionary<string,object> claims=new JavaScriptSerializer().Deserialize<Dictionary<string,object>>(Encoding.UTF8.GetString(Convert.FromBase64String(part)));
  if(claims.ContainsKey("flow")&&Convert.ToString(claims["flow"])=="browser") {
   string destination=PortalNavigation.ForUser(user,claims.ContainsKey("returnUrl")?Convert.ToString(claims["returnUrl"]):"/Reports");
   Response.StatusCode=303;Response.RedirectLocation=destination;Context.ApplicationInstance.CompleteRequest();return;
  }
  Response.Write("{\\"authenticated\\":true}");return;
 }
 Response.AddHeader("X-Frame-Options","DENY");
 string target=PortalNavigation.SafeReturn(Request.HttpMethod=="POST"?Request.Form["returnUrl"]:(Request.QueryString["ReturnUrl"]??Request.QueryString["returnUrl"]));
 if(Request.HttpMethod=="GET"){RenderLogin(target,null);return;}
 if(Request.HttpMethod!="POST"){Response.StatusCode=405;return;}
 HttpCookie csrf=Request.Cookies["P4PortalCsrf"];
 if(csrf==null||!Equal(csrf.Value,Request.Form["csrf"])) {Response.StatusCode=403;RenderLogin(target,"登录请求已失效，请重试。");return;}
 string principal;
 try { principal=Verify(Request.Form["username"],Request.Form["password"]); }
 catch {Response.StatusCode=503;RenderLogin(target,"登录服务暂不可用，请稍后重试。");return;}
 if(principal==null){Response.StatusCode=401;RenderLogin(target,"账号或密码错误，或尝试次数过多。");return;}
 string ticketForBrowser=Issue(principal,PortalNavigation.ForUser(principal,target));
 Response.ContentType="text/html; charset=utf-8";
 Response.Write("<!doctype html><html lang='zh-CN'><meta charset='utf-8'><title>正在打开报表门户</title><meta name='referrer' content='no-referrer'><body><p>已登录，正在打开报表门户…</p><form id='bridge' method='post' action='/ReportServer/P4Login.aspx'><input type='hidden' name='ticket' value='"+HttpUtility.HtmlAttributeEncode(ticketForBrowser)+"'><button type='submit'>继续打开门户</button></form><script>document.getElementById('bridge').submit();</script></body></html>");
}
'''
(root/'custom-security/P4Login.aspx').write_text(prefix+'\n'+validator+helpers+event+'\n</script>\n')
print('Unified system login and ticket callback at the configured anonymous login endpoint')
