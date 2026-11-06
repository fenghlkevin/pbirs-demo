using System;using Microsoft.ReportingServices.Interfaces;using System.IO;using System.Reflection;using System.Security;using System.Security.Policy;using System.Security.Permissions;
[assembly: System.Security.SecurityRules(System.Security.SecurityRuleSet.Level1)]
public class Loader:MarshalByRefObject {
 public string Test(string path) {
  try { Assembly a=Assembly.LoadFrom(path);object instance=a.CreateInstance("P4.Reporting.Authentication");
   IAuthorizationExtension authorization=(IAuthorizationExtension)a.CreateInstance("P4.Reporting.Authorization"); bool allowed=authorization.CheckAccess("p4:portaladmin",IntPtr.Zero,new byte[0],ReportOperation.ExecuteAndView);
   string denied;try{File.ReadAllText(@"C:\Windows\System32\config\SAM");denied="UNEXPECTED_FILE_READ";}catch(Exception e){denied=e.GetType().Name;}
   return "LOADED; FullyTrusted="+a.IsFullyTrusted+"; Authorized="+allowed+"; IOProbe="+denied;
  } catch(Exception e) {return e.GetType().Name+": "+e.Message;}
 }
}
class CasProbe {
 static void Main(string[] args) {
  string root=Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
  Assembly interfaces=Assembly.LoadFrom(@"E:\PowerBI\PBIRS\ReportServer\bin\Microsoft.ReportingServices.Interfaces.dll");
  StrongName microsoft=interfaces.Evidence.GetHostEvidence<StrongName>();
  foreach(string variant in args) {
   PermissionSet permissions=new PermissionSet(PermissionState.None);permissions.AddPermission(new SecurityPermission(SecurityPermissionFlag.Execution));permissions.AddPermission(new FileIOPermission(FileIOPermissionAccess.Read|FileIOPermissionAccess.PathDiscovery,new string[]{root,@"E:\PowerBI\PBIRS\ReportServer\bin"}));
   AppDomainSetup setup=new AppDomainSetup();setup.ApplicationBase=root;
   AppDomain domain=AppDomain.CreateDomain("probe-"+Path.GetFileName(variant),null,setup,permissions,microsoft);
   try {Loader loader=(Loader)domain.CreateInstanceFromAndUnwrap(Assembly.GetExecutingAssembly().Location,typeof(Loader).FullName);Console.WriteLine(Path.GetFileName(variant)+": "+loader.Test(variant));}
   catch(Exception e){Console.WriteLine(Path.GetFileName(variant)+": "+e.GetType().Name+" "+e.Message);}
   finally{AppDomain.Unload(domain);}
  }
 }
}
