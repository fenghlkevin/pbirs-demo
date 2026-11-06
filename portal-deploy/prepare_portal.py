import hashlib,json,os,secrets
from pathlib import Path
root=Path(__file__).resolve().parents[1]
accounts_path=root/'app-accounts.local.json';accounts=json.loads(accounts_path.read_text())
if 'p4admin' not in accounts:
 password='P4Admin!'+secrets.token_urlsafe(16)+'9a';salt=secrets.token_hex(16)
 accounts['p4admin']={'salt':salt,'iterations':600000,'passwordHash':hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),600000).hex(),'principal':'p4:portaladmin'}
 fd=os.open(root/'admin-login.local.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'w') as f:json.dump({'username':'p4admin','password':password,'principal':'p4:portaladmin'},f,indent=2)
 accounts_path.write_text(json.dumps(accounts,indent=2))
source=root/'custom-security'/'P4Security.cs';code=source.read_text().replace('if(user=="p4:maintenance")','if(user=="p4:maintenance"||user=="p4:portaladmin")')
source.write_text(code)
nav=(root/'portal-deploy'/'PortalNavigation.cs.txt').read_text()
page=root/'custom-security'/'P4Login.aspx';code=page.read_text();marker='protected void Page_Load';start=code.index(marker)
# Preserve the working signature and anti-replay validator; add browser flow only after Consume succeeds.
code=code[:start]+nav+'''\nprotected void Page_Load(object sender, EventArgs e) {
 Response.SuppressFormsAuthenticationRedirect=true;
 Response.Cache.SetCacheability(HttpCacheability.NoCache);Response.Cache.SetNoStore();
 Response.AddHeader("Referrer-Policy","no-referrer");
 if(Request.HttpMethod=="GET") {
  string target=PortalNavigation.SafeReturn(Request.QueryString["ReturnUrl"]);
  Response.Redirect("/ReportServer/P4Portal.aspx?returnUrl="+HttpUtility.UrlEncode(target),false);Context.ApplicationInstance.CompleteRequest();return;
 }
 Response.ContentType="application/json";
 if(Request.HttpMethod!="POST") { Response.StatusCode=405;Response.Write("{\\"error\\":\\"Method not allowed\\"}");return; }
 string ticket=Request.Form["ticket"];string user=LoginTickets.Consume(ticket);
 if(user==null) { Response.StatusCode=401;Response.Write("{\\"error\\":\\"Invalid, expired or used identity ticket\\"}");return; }
 FormsAuthentication.SetAuthCookie(user,false);
 string part=ticket.Split('.')[0].Replace('-','+').Replace('_','/');part=part.PadRight((part.Length+3)/4*4,'=');
 Dictionary<string,object> claims=new JavaScriptSerializer().Deserialize<Dictionary<string,object>>(Encoding.UTF8.GetString(Convert.FromBase64String(part)));
 if(claims.ContainsKey("flow")&&Convert.ToString(claims["flow"])=="browser") {
  string target=PortalNavigation.ForUser(user,claims.ContainsKey("returnUrl")?Convert.ToString(claims["returnUrl"]):"/Reports");
  Response.StatusCode=303;Response.RedirectLocation=target;Context.ApplicationInstance.CompleteRequest();return;
 }
 Response.Write("{\\"authenticated\\":true}");
}
</script>
'''
page.write_text(code)
print('Prepared browser callback and separate p4admin account; no credentials printed')
