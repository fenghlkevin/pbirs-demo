<%@ Page Language="C#" CodePage="65001" %>
<%@ Import Namespace="System" %>
<script runat="server">
protected void Page_Load(object sender,EventArgs e) {
 Response.Cache.SetCacheability(System.Web.HttpCacheability.NoCache);Response.Cache.SetNoStore();
 string target=Request.QueryString["ReturnUrl"]??Request.QueryString["returnUrl"]??"/Reports";
 string language=Request.QueryString["lang"]=="zh-CN"?"zh-CN":(Request.QueryString["lang"]=="pt-AO"?"pt-AO":(Request.Cookies["P4DemoLang"]==null?"pt-AO":Request.Cookies["P4DemoLang"].Value=="zh-CN"?"zh-CN":"pt-AO"));
 Response.Redirect("/ReportServer/P4Login.aspx?lang="+language+"&returnUrl="+Server.UrlEncode(target),false);Context.ApplicationInstance.CompleteRequest();
}
</script>