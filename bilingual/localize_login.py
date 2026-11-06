from pathlib import Path
p=Path('custom-security/P4Login.aspx');s=p.read_text(encoding='utf-8-sig')
a=s.index('void RenderLogin(');b=s.index('protected void Page_Load(',a)
s=s[:a]+'''string Language {
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
''' +s[b:]
s=s.replace(' Response.ContentEncoding=Encoding.UTF8;', ''' HttpCookie languageCookie=new HttpCookie("P4DemoLang",Language);languageCookie.Path="/";languageCookie.Expires=DateTime.UtcNow.AddYears(1);languageCookie.SameSite=SameSiteMode.Lax;languageCookie.Secure=Request.IsSecureConnection;Response.Cookies.Add(languageCookie);
 Response.AddHeader("Content-Language",Language);
 Response.ContentEncoding=Encoding.UTF8;''')
for zh,pt in [('登录请求已失效，请重试。','O pedido de início de sessão expirou. Tente novamente.'),('登录服务暂不可用，请稍后重试。','O serviço de autenticação está indisponível. Tente novamente mais tarde.'),('账号或密码错误，或尝试次数过多。','Utilizador ou palavra-passe incorrectos, ou demasiadas tentativas.')]:
 s=s.replace('RenderLogin(target,"'+zh+'")','RenderLogin(target,L("'+zh+'","'+pt+'"))')
s=s.replace("<html lang='zh-CN'><meta charset='utf-8'><title>正在打开报表门户</title>","<html lang='\"+Language+\"'><meta charset='utf-8'><title>\"+L(\"正在打开报表门户\",\"A abrir o portal de relatórios\")+\"</title>")
s=s.replace('<body><p>已登录，正在打开报表门户…</p>', '<body><p>"+L("已登录，正在打开报表门户…","Sessão iniciada. A abrir o portal de relatórios…")+"</p>')
s=s.replace("<button type='submit'>继续打开门户</button>","<button type='submit'>\"+L(\"继续打开门户\",\"Continuar para o portal\")+\"</button>")
p.write_text(s,encoding='utf-8-sig')
# Legacy bookmarks use the same active account service and bilingual login.
Path('custom-security/P4Portal.aspx').write_text('''<%@ Page Language="C#" CodePage="65001" %>
<%@ Import Namespace="System" %>
<script runat="server">
protected void Page_Load(object sender,EventArgs e) {
 Response.Cache.SetCacheability(System.Web.HttpCacheability.NoCache);Response.Cache.SetNoStore();
 string target=Request.QueryString["ReturnUrl"]??Request.QueryString["returnUrl"]??"/Reports";
 string language=Request.QueryString["lang"]=="zh-CN"?"zh-CN":(Request.QueryString["lang"]=="pt-AO"?"pt-AO":(Request.Cookies["P4DemoLang"]==null?"pt-AO":Request.Cookies["P4DemoLang"].Value=="zh-CN"?"zh-CN":"pt-AO"));
 Response.Redirect("/ReportServer/P4Login.aspx?lang="+language+"&returnUrl="+Server.UrlEncode(target),false);Context.ApplicationInstance.CompleteRequest();
}
</script>''',encoding='utf-8-sig')
