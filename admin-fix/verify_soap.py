import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ticket_auth import establish,BASE
endpoint=BASE+'/ReportServer/ReportService2010.asmx'
namespace='http://schemas.microsoft.com/sqlserver/reporting/2010/03/01/ReportServer'
soap='''<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><GetItemType xmlns="%s"><ItemPath>%s</ItemPath></GetItemType></soap:Body></soap:Envelope>'''
for principal,path,allowed in [('p4:portaladmin','/P4_Identity_Demo/Report_A',True),('p4:demo1','/P4_Identity_Demo/Report_A',True),('p4:demo1','/P4_Identity_Demo/Report_B',False)]:
 s,me=establish(principal)
 r=s.post(endpoint,data=(soap%(namespace,path)).encode(),headers={'Content-Type':'text/xml; charset=utf-8','SOAPAction':'"'+namespace+'/GetItemType"'},timeout=30)
 if allowed:assert r.status_code==200 and 'GetItemTypeResponse' in r.text,(principal,r.status_code,r.text[:200])
 else:assert not r.ok and ('rsAccessDenied' in r.text or 'AccessDenied' in r.text),(principal,r.status_code,r.text[:200])
 print(principal,path,'SOAP access',r.status_code,'allowed' if allowed else 'denied')
print('Native ReportServer SOAP identity and permission checks passed')
