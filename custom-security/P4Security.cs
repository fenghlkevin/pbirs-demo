using System;
using System.IO;
using System.Text;
using System.Xml;
using System.Collections;
using System.Collections.Generic;
using System.Collections.Specialized;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text.RegularExpressions;
using System.Web;
using System.Web.Script.Serialization;
using Microsoft.ReportingServices.Interfaces;

[assembly: System.Reflection.AssemblyVersion("1.0.0.0")]
// Match the report server legacy CAS host without granting additional permissions.
[assembly: System.Security.SecurityRules(System.Security.SecurityRuleSet.Level1)]
namespace P4.Reporting {
 public static class Tickets { public static bool Principal(string name) { return name != null && Regex.IsMatch(name,@"\Ap4:[A-Za-z0-9_-]{1,64}\z"); } }

 public class Authentication : IAuthenticationExtension2 {
  public string LocalizedName {  get { return "P4 signed identity tickets"; } }

  public void SetConfiguration(string configuration) { }

  public bool IsValidPrincipalName(string name) { return Tickets.Principal(name); }

  public bool LogonUser(string user,string ticket,string authority) { return false; /* Only the signed-ticket Forms login page can authenticate. */ }

  public void GetUserInfo(out IIdentity identity,out IntPtr userId) {
   identity=HttpContext.Current==null||HttpContext.Current.User==null?null:HttpContext.Current.User.Identity;
   userId=IntPtr.Zero;
  }

  public void GetUserInfo(IRSRequestContext context,out IIdentity identity,out IntPtr userId) {
   identity=context==null?null:context.User;userId=IntPtr.Zero;
  }
 }
 public class Authorization : IAuthorizationExtension {
  public string LocalizedName {  get { return "P4 catalog role authorization"; } }

  public void SetConfiguration(string configuration) { }

  public byte[] CreateSecurityDescriptor(AceCollection acl,SecurityItemType itemType,out string description) {
   XmlDocument doc=new XmlDocument();doc.XmlResolver=null;XmlElement root=doc.CreateElement("P4Acl");doc.AppendChild(root);
   foreach(AceStruct ace in acl) {
    XmlElement entry=doc.CreateElement("Entry");entry.SetAttribute("user",ace.PrincipalName);root.AppendChild(entry);
    // Preserve every operation category, including future enum fields, without BinaryFormatter.
    foreach(System.Reflection.FieldInfo field in typeof(AceStruct).GetFields()) {
     IEnumerable values=field.GetValue(ace) as IEnumerable; if(values==null||field.FieldType==typeof(string))continue;
     foreach(object value in values) {
      if(value==null||!value.GetType().IsEnum)continue;
      XmlElement op=doc.CreateElement("Op");op.SetAttribute("type",value.GetType().Name);op.InnerText=value.ToString();entry.AppendChild(op);
     }
    }
   }
   description="P4 role ACL";return Encoding.UTF8.GetBytes(doc.OuterXml);
  }
  static XmlDocument Read(byte[] descriptor) {
   XmlDocument doc=new XmlDocument();doc.XmlResolver=null;
   if(descriptor==null||descriptor.Length==0)return doc;
   try { using(XmlReader reader=XmlReader.Create(new MemoryStream(descriptor),new XmlReaderSettings { DtdProcessing=DtdProcessing.Prohibit,XmlResolver=null }))doc.Load(reader); } catch { return new XmlDocument(); }
   return doc;
  }
  bool Check(string user,byte[] descriptor,Enum operation) {
   if(!Tickets.Principal(user))return false;
   if(user=="p4:maintenance"||user=="p4:portaladmin")return true; // Separate deployment-maintenance and explicitly provisioned system-administrator identities.
   foreach(XmlNode entry in Read(descriptor).SelectNodes("/P4Acl/Entry")) {
    if(entry.Attributes["user"].Value!=user)continue;
    foreach(XmlNode op in entry.ChildNodes)if(op.Attributes["type"].Value==operation.GetType().Name&&op.InnerText==operation.ToString())return true;
   }
   return false;
  }

  public bool CheckAccess(string u,IntPtr t,byte[] d,CatalogOperation o){return Check(u,d,o);}

  public bool CheckAccess(string u,IntPtr t,byte[] d,CatalogOperation[] ops){foreach(CatalogOperation o in ops)if(!Check(u,d,o))return false;return true;}

  public bool CheckAccess(string u,IntPtr t,byte[] d,ReportOperation o){return Check(u,d,o);}

  public bool CheckAccess(string u,IntPtr t,byte[] d,FolderOperation o){return Check(u,d,o);}

  public bool CheckAccess(string u,IntPtr t,byte[] d,FolderOperation[] ops){foreach(FolderOperation o in ops)if(!Check(u,d,o))return false;return true;}

  public bool CheckAccess(string u,IntPtr t,byte[] d,ResourceOperation o){return Check(u,d,o);}

  public bool CheckAccess(string u,IntPtr t,byte[] d,ResourceOperation[] ops){foreach(ResourceOperation o in ops)if(!Check(u,d,o))return false;return true;}

  public bool CheckAccess(string u,IntPtr t,byte[] d,DatasourceOperation o){return Check(u,d,o);}

  public bool CheckAccess(string u,IntPtr t,byte[] d,ModelOperation o){return Check(u,d,o);}

  public bool CheckAccess(string u,IntPtr t,byte[] d,ModelItemOperation o){return Check(u,d,o);}
  static StringCollection ExpandNames(StringCollection values) {
   StringCollection result=new StringCollection();
   foreach(string name in values) {
    if(!result.Contains(name))result.Add(name);
    string display=Regex.Replace(name,"([a-z])([A-Z])","$1 $2").Replace(" And "," and ");
    if(!result.Contains(display))result.Add(display);
   }
   return result;
  }

  public StringCollection GetPermissions(string user,IntPtr token,SecurityItemType itemType,byte[] descriptor) {
   StringCollection result=new StringCollection();
   if(user=="p4:maintenance"||user=="p4:portaladmin") {
    foreach(Type type in new Type[]{typeof(CatalogOperation),typeof(ReportOperation),typeof(FolderOperation),typeof(ResourceOperation),typeof(DatasourceOperation),typeof(ModelOperation),typeof(ModelItemOperation)})foreach(string name in Enum.GetNames(type))if(!result.Contains(name))result.Add(name);
    return ExpandNames(result);
   }
   foreach(XmlNode entry in Read(descriptor).SelectNodes("/P4Acl/Entry"))if(entry.Attributes["user"].Value==user)foreach(XmlNode op in entry.ChildNodes)if(!result.Contains(op.InnerText))result.Add(op.InnerText);
   return ExpandNames(result);
  }
 }
}
