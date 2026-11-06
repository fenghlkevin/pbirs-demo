"""P4 system identities authenticated by signed one-use tickets in PBIRS."""
import os
import gzip
import socket
import base64
import json
import hashlib
import hmac
import secrets
import threading
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
import re
import copy
import requests
from ticket_auth import establish,issue_ticket,KEY,BASE
from rls_admin import RlsAdmin
from demo_admin import (AdminError, MUTATION_LOCK, Policies, atomic_json, load_accounts,
                        is_admin, public_user, password_record, grants_for, bootstrap,
                        ACCOUNTS_PATH, selection_for, effective_ids, under, reconcile_permissions)

UPSTREAM=BASE
HOST=os.environ.get('P4_PUBLIC_URL','http://127.0.0.1:8765')
BIND=os.environ.get('P4_BIND','127.0.0.1')
AUTH_NONCES={}
AUTH_ATTEMPTS={}
SESSIONS={}
LOCK=threading.RLock()
ASSETS={}
ENCODED_ASSETS={}
LOCAL=threading.local()
TTL=3600
UI_TRANSLATIONS=json.loads(Path(__file__).with_name('bilingual').joinpath('translations.json').read_text(encoding='utf-8'))

def connection(token, identity):
    if not hasattr(LOCAL,'connections'): LOCAL.connections={}
    if token not in LOCAL.connections:
        s=requests.Session();s.trust_env=False
        s.cookies.update(identity['cookies'])
        LOCAL.connections[token]=s
    return LOCAL.connections[token]

class Handler(BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    def setup(self):
        super().setup()
        self.connection.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        self.connection.setsockopt(socket.SOL_SOCKET,socket.SO_SNDBUF,1024*1024)
        self.connection.settimeout(150)
    def log_message(self,*args): pass
    def ui_language(self):
        cookies=SimpleCookie(self.headers.get('Cookie',''))
        value=cookies['P4DemoLang'].value if 'P4DemoLang' in cookies else self.headers.get('Accept-Language','pt-AO').split(',')[0]
        return 'zh-CN' if value.startswith('zh') else 'pt-AO'
    def reply(self,status,body,kind='application/json',cookie=None,*,static=False,upstream_ms=None):
        if isinstance(body,dict) and isinstance(body.get('error'),str) and self.ui_language()=='pt-AO':
            body={**body,'error':UI_TRANSLATIONS.get(body['error'],body['error'])}
        if isinstance(body,(dict,list)):body=json.dumps(body,ensure_ascii=False).encode()
        compressible=any(value in kind.lower() for value in ('text/','javascript','json','svg','xml'))
        encoding=None
        accepts_gzip=any(part.strip().split(';')[0]=='gzip' and ';q=0' not in part.replace(' ','')
                         for part in self.headers.get('Accept-Encoding','').split(','))
        etag='"'+hashlib.sha256(body).hexdigest()[:24]+'"' if static else None
        if static and self.headers.get('If-None-Match')==etag:
            status=304;body=b''
        elif len(body)>512 and compressible and accepts_gzip:
            if static:
                with LOCK:encoded=ENCODED_ASSETS.get(etag)
                if encoded is None:
                    encoded=gzip.compress(body,compresslevel=6,mtime=0)
                    with LOCK:ENCODED_ASSETS[etag]=encoded
                body=encoded
            else:body=gzip.compress(body,compresslevel=6,mtime=0)
            encoding='gzip'
        self.send_response(status)
        self.send_header('Content-Type',kind)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','private, max-age=3600' if static else 'no-store')
        self.send_header('Vary','Accept-Encoding')
        self.send_header('X-Content-Type-Options','nosniff')
        if encoding:self.send_header('Content-Encoding',encoding)
        if etag:self.send_header('ETag',etag)
        if upstream_ms is not None:self.send_header('Server-Timing','upstream;dur='+str(round(upstream_ms,1)))
        if cookie:self.send_header('Set-Cookie',cookie)
        self.end_headers()
        try:self.wfile.write(body)
        except (BrokenPipeError,ConnectionResetError):pass
    def do_GET(self):self.handle_request()
    def do_POST(self):self.handle_request()
    def body(self):
        if hasattr(self,'_request_body'):return self._request_body
        size=int(self.headers.get('Content-Length','0'))
        if size>16*1024*1024:raise ValueError('Request too large')
        self._request_body=self.rfile.read(size) if size else None
        return self._request_body
    def identity(self):
        cookies=SimpleCookie(self.headers.get('Cookie',''))
        token=cookies['demo_session'].value if 'demo_session' in cookies else ''
        with LOCK:
            entry=SESSIONS.get(token)
            account=load_accounts().get(entry['name']) if entry else None
            if (entry and account and account.get('enabled',True)
                    and entry.get('version',0)==account.get('version',0)
                    and entry['principal']==account['principal'] and entry['expires']>time.time()):
                return token,{**entry,'role':account.get('role','viewer'),
                              'displayName':account.get('displayName',entry['name'])}
            SESSIONS.pop(token,None)
        return '',None
    def handle_request(self):
        if hasattr(self,'_request_body'):del self._request_body
        try:
            # Drain once before routing so early returns cannot corrupt the next
            # request on a persistent HTTP connection. Handlers read the saved body.
            self.body()
            self.route()
        except AdminError as error:self.reply(error.status,{'error':str(error)})
        except (requests.RequestException,ValueError,KeyError):self.reply(502,{'error':'上游请求失败，请稍后重试'})
    def admin_route(self, path):
        with MUTATION_LOCK:
            accounts=load_accounts()
            if path=='/api/admin/rls/user' and self.command=='GET':
                username=parse_qs(urlsplit(self.path).query).get('username',[''])[0]
                return self.reply(200,RlsAdmin().user_inventory(username,accounts))
            if path=='/api/admin/rls/batch' and self.command=='POST':
                return self.reply(200,RlsAdmin().save_many(json.loads(self.body() or b'{}'),accounts))
            if path=='/api/admin/rls/catalog' and self.command=='GET':
                return self.reply(200,RlsAdmin().inventory(accounts))
            if path=='/api/admin/rls/reports' and self.command=='GET':
                return self.reply(200,{'reports':RlsAdmin().reports()})
            if path=='/api/admin/rls' and self.command=='GET':
                report_id=parse_qs(urlsplit(self.path).query).get('reportId',[''])[0]
                return self.reply(200,RlsAdmin().view(report_id,accounts))
            if path=='/api/admin/rls' and self.command=='POST':
                return self.reply(200,RlsAdmin().save(json.loads(self.body() or b'{}'),accounts))
            if path=='/api/admin/users' and self.command=='GET':
                reports=Policies().matrix()
                users=[]
                for name,account in accounts.items():
                    user=public_user(name,account)
                    user['reportCount']=len(grants_for(account,reports)) if user['enabled'] else 0
                    users.append(user)
                return self.reply(200,{'users':users})
            if path=='/api/admin/users' and self.command=='POST':
                data=json.loads(self.body() or b'{}');name=data.get('username','')
                if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{2,39}',name):
                    raise AdminError(400,'账号须为 3～40 位字母、数字、下划线或短横线，以字母开头')
                if name in accounts:raise AdminError(409,'该账号已存在')
                display=data.get('displayName',name)
                if not isinstance(display,str) or not 1<=len(display)<=80:raise AdminError(400,'姓名长度为 1～80 个字符')
                accounts[name]={**password_record(data.get('password')),'displayName':display,
                                'principal':'p4:u_'+secrets.token_hex(12),'enabled':True,
                                'role':'viewer','version':1}
                atomic_json(ACCOUNTS_PATH,accounts)
                return self.reply(201,{'user':public_user(name,accounts[name])})
            match=re.fullmatch(r'/api/admin/users/([A-Za-z0-9_-]+)/(status|password)',path)
            if match and self.command=='POST':
                name,action=match.groups();account=accounts.get(name)
                if not account:raise AdminError(404,'用户不存在')
                if is_admin(account):raise AdminError(400,'此演示不允许修改管理员的启停状态或密码')
                data=json.loads(self.body() or b'{}')
                updated=copy.deepcopy(accounts)
                if action=='password':
                    updated[name].update(password_record(data.get('password')))
                    updated[name]['version']=account.get('version',0)+1
                    atomic_json(ACCOUNTS_PATH,updated)
                    return self.reply(200,{'ok':True})
                enabled=data.get('enabled')
                if not isinstance(enabled,bool):raise AdminError(400,'enabled 必须为布尔值')
                if enabled==account.get('enabled',True):return self.reply(200,{'ok':True})
                policies=Policies();reports=policies.matrix()
                selection=selection_for(account,reports)
                updated[name].update(enabled=enabled,version=account.get('version',0)+1,
                                     accessSelection=selection)
                policies.replace_selection(account['principal'],selection['folderIds'],selection['reportIds'],enabled,
                                           lambda:atomic_json(ACCOUNTS_PATH,updated))
                return self.reply(200,{'ok':True})
            if path=='/api/admin/access' and self.command=='GET':
                name=parse_qs(urlsplit(self.path).query).get('username',[''])[0]
                account=accounts.get(name)
                if not account:raise AdminError(404,'用户不存在')
                items=Policies().matrix();selection=selection_for(account,items)
                effective=effective_ids(selection,items)
                return self.reply(200,{'user':public_user(name,account),'selection':selection,
                    'items':[{k:item[k] for k in ('Id','Name','Path','Type')}|
                             {'effective':item['Id'] in effective,'inherits':item['inherits']}
                             for item in items]})
            if path=='/api/admin/access' and self.command=='POST':
                data=json.loads(self.body() or b'{}');name=data.get('username','');account=accounts.get(name)
                if not account:raise AdminError(404,'用户不存在')
                if is_admin(account):raise AdminError(400,'管理员的资源权限由初始化配置管理')
                if not account.get('enabled',True):raise AdminError(400,'请先启用用户再修改授权')
                selection={'folderIds':data.get('folderIds',[]),'reportIds':data.get('reportIds',[])}
                for values in selection.values():
                    if not isinstance(values,list) or len(values)>1000 or any(not isinstance(v,str) for v in values):
                        raise AdminError(400,'目录或报表列表不正确')
                selection={k:list(dict.fromkeys(v)) for k,v in selection.items()}
                updated=copy.deepcopy(accounts);updated[name]['accessSelection']=selection
                Policies().replace_selection(account['principal'],selection['folderIds'],selection['reportIds'],True,
                                             lambda:atomic_json(ACCOUNTS_PATH,updated))
                return self.reply(200,{'ok':True})
            return self.reply(404,{'error':'管理接口不存在'})
    def internal_authenticate(self):
        # Loopback-only, authenticated service-to-service API; never returns password hashes.
        if self.client_address[0] not in ('127.0.0.1','::1'):
            return self.reply(403,{'error':'Loopback only'})
        raw=self.body() or b''
        stamp=self.headers.get('X-P4-Time','');nonce=self.headers.get('X-P4-Nonce','')
        signature=self.headers.get('X-P4-Signature','')
        expected=hmac.new(KEY,stamp.encode()+b'\n'+nonce.encode()+b'\n'+raw,hashlib.sha256).hexdigest()
        if (not stamp.isdigit() or abs(time.time()-int(stamp))>30
                or not re.fullmatch(r'[a-f0-9]{32}',nonce) or not hmac.compare_digest(expected,signature)):
            return self.reply(401,{'error':'Invalid service request'})
        with LOCK:
            for old in list(AUTH_NONCES):
                if AUTH_NONCES[old]<time.time()-60:AUTH_NONCES.pop(old,None)
            if nonce in AUTH_NONCES:return self.reply(401,{'error':'Replayed request'})
            AUTH_NONCES[nonce]=time.time()
        data=json.loads(raw);name=data.get('username','');password=data.get('password','')
        if not isinstance(name,str) or not isinstance(password,str) or len(name)>64 or len(password)>512:
            return self.reply(401,{'error':'Invalid credentials'})
        with LOCK:
            started,count=AUTH_ATTEMPTS.get(name,(time.time(),0))
            if started<time.time()-300:started,count=time.time(),0
            if count>=10:return self.reply(429,{'error':'Too many attempts'})
            AUTH_ATTEMPTS[name]=(started,count+1)
        account=load_accounts().get(name)
        salt=account['salt'] if account else '0'*32
        digest=hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),600000).hex()
        if not account or not account.get('enabled',True) or not hmac.compare_digest(digest,account['passwordHash']):
            return self.reply(401,{'error':'Invalid credentials'})
        with LOCK:AUTH_ATTEMPTS.pop(name,None)
        return self.reply(200,{'principal':account['principal']})

    def route(self):
        path=urlsplit(self.path).path
        if path=='/internal/authenticate' and self.command=='POST':
            return self.internal_authenticate()
        if self.command=='POST' and self.headers.get('Origin') not in (None,HOST):
            return self.reply(403,{'error':'Origin rejected'})
        if path=='/' and self.command=='GET':
            return self.reply(200,Path(__file__).with_name('index.html').read_bytes(),'text/html; charset=utf-8')
        if path=='/api/login' and self.command=='POST':
            data=json.loads(self.body() or b'{}');name=data.get('username','');password=data.get('password','')
            account=load_accounts().get(name) if isinstance(name,str) else None
            if not account or not account.get('enabled',True) or not isinstance(password,str) or not password:
                return self.reply(401,{'error':'系统账号或密码错误'})
            password_hash=hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(account['salt']),account['iterations']).hex()
            if not hmac.compare_digest(password_hash,account['passwordHash']):
                return self.reply(401,{'error':'系统账号或密码错误'})
            principal=account['principal']
            upstream,remote_identity=establish(principal)
            token=secrets.token_urlsafe(32)
            old,_=self.identity()
            with LOCK:
                SESSIONS.pop(old,None)
                SESSIONS[token]={'name':name,'principal':principal,'cookies':upstream.cookies.get_dict(),
                                 'version':account.get('version',0),'expires':time.time()+TTL}
            return self.reply(200,{**public_user(name,account),'pbirsIdentity':remote_identity},cookie=f'demo_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age={TTL}')
        token,identity=self.identity()
        if not identity:return self.reply(401,{'error':'请先登录第三方演示页面'})
        if path=='/api/logout' and self.command=='POST':
            with LOCK:SESSIONS.pop(token,None)
            return self.reply(200,{'ok':True},cookie='demo_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0')
        if path=='/api/me':return self.reply(200,public_user(identity['name'],load_accounts()[identity['name']]))
        if path.startswith('/api/admin/'):
            if identity['role']!='admin':return self.reply(403,{'error':'需要 Demo 管理员权限'})
            return self.admin_route(path)
        if path=='/api/browser-ticket' and self.command=='POST':
            return self.reply(200,{'ticket':issue_ticket(identity['principal'],browser=True),'url':UPSTREAM+'/ReportServer/P4Login.aspx'})
        if path in ('/api/catalog','/api/reports'):
            # Use the service identity for catalog metadata only. Every returned resource
            # is individually checked with the current user's PBIRS session.
            visible=[];catalog=Policies().catalog();viewer=connection(token,identity)
            for item in catalog:
                if item['Path']=='/':continue
                endpoint=Policies.policy_path(item).removesuffix('/Policies')
                response=viewer.get(UPSTREAM+'/Reports/api/v2.0'+endpoint,timeout=35,allow_redirects=False)
                if response.status_code==200:visible.append(item)
                elif response.status_code not in (401,403,404):
                    raise AdminError(502,'目录读取失败，请稍后重试')
            # Virtual ancestors allow navigation to individually granted reports without
            # granting Browser on their parents (which could expose sibling reports).
            by_path={item['Path']:item for item in catalog};shown={i['Id']:i for i in visible}
            for item in list(visible):
                parent=item['Path'].rsplit('/',1)[0]
                while parent:
                    folder=by_path.get(parent)
                    if folder and folder['Id'] not in shown:shown[folder['Id']]={**folder,'navigationOnly':True}
                    parent=parent.rsplit('/',1)[0]
            result=list(shown.values())
            if path=='/api/reports':result=[i for i in result if i['Type']!='Folder']
            return self.reply(200,{'value':result,'principal':identity['principal']})
        target=self.path
        if not path.lower().startswith(('/reports/','/powerbi/','/reportserver/')):
            return self.reply(404,{'error':'Not found'})
        if self.command=='POST' and not (path.lower().startswith('/powerbi/api/explore/') and path.lower().endswith(('/querydata','/conceptualschema'))):
            return self.reply(403,{'error':'演示仅允许读取报表与查询数据'})
        static=self.command=='GET' and path.lower().startswith(('/reports/assets/','/powerbi/libs/','/powerbi/assets/'))
        cache_key=(target,self.ui_language())
        with LOCK:cached=ASSETS.get(cache_key) if static else None
        if cached:return self.reply(200,cached[0],cached[1],static=True,upstream_ms=0)
        headers={k:v for k,v in self.headers.items() if k.lower() in ('content-type','accept','accept-language','x-requested-with','requestverificationtoken','activityid','requestid') or k.lower().startswith('x-powerbi-')}
        # Native PBIRS ships pt-BR UI resources; report formatting remains pt-AO.
        headers['Accept-Language']='zh-CN' if self.ui_language()=='zh-CN' else 'pt-BR,pt;q=0.9'
        started=time.perf_counter()
        r=connection(token,identity).request(self.command,UPSTREAM+target,headers=headers,data=self.body(),timeout=120,allow_redirects=False)
        if path=='/api/reports' and r.status_code==403:
            return self.reply(200,{'value':[],'principal':identity['principal']})
        if path=='/api/reports' and r.ok:
            items=[{'Id':x['Id'],'Name':x['Name'],'Path':x['Path'],'Type':x['Type']} for x in r.json().get('value',[]) if x.get('Type') in ('PowerBIReport','Report')]
            return self.reply(200,{'value':items,'principal':identity['principal']})
        if r.status_code in (401,403):return self.reply(403,{'error':'当前 PBIRS 用户无权访问此资源','principal':identity['principal']})
        body=r.content;kind=r.headers.get('Content-Type','application/octet-stream')
        if any(t in kind.lower() for t in ('text/','javascript','json')):body=body.replace(UPSTREAM.encode(),HOST.encode())
        if static and r.ok:
            with LOCK:ASSETS[cache_key]=(body,kind)
        if r.is_redirect:
            destination=r.headers.get('Location','').replace(UPSTREAM,HOST)
            if not destination.startswith(('/',HOST+'/')):return self.reply(502,{'error':'Unexpected upstream redirect'})
            self.send_response(r.status_code);self.send_header('Location',destination);self.send_header('Content-Length','0');self.end_headers();return
        self.reply(r.status_code,body,kind,static=static and r.ok,upstream_ms=(time.perf_counter()-started)*1000)

class DemoHTTPServer(ThreadingHTTPServer):
    request_queue_size=128
    daemon_threads=True

if __name__=='__main__':
    bootstrap()
    threading.Thread(target=reconcile_permissions,daemon=True).start()
    print('Per-user demo: '+HOST,flush=True)
    DemoHTTPServer((BIND,8765),Handler).serve_forever()
