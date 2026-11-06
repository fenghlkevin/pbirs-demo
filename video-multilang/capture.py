import subprocess,json,sys
from pathlib import Path
R=Path(__file__).resolve().parent
D={
'P4 Demo · Utilizadores e relatórios':'P4 Demo · Users and reports','Gestão de utilizadores e permissões de relatórios':'User management and report permissions','Idioma / 语言':'Language','Administrador do Demo · Administrador':'Demo administrator · Administrator','Abrir portal PBIRS':'Open PBIRS portal','Terminar sessão':'Sign out','Os meus relatórios':'My reports','Utilizadores':'Users','Permissões de acesso':'Resource access','Segurança ao nível da linha':'Row-level security','Os novos utilizadores não têm acesso a relatórios até receberem permissões.':'New users have no report access until permission is granted.','Novo utilizador':'New user','Utilizador':'User','Nome':'Name','Perfil':'Role','Estado':'Status','Relatórios acessíveis':'Accessible reports','Acções':'Actions','Activo':'Active','Desactivar':'Disable','Repor palavra-passe':'Reset password','Administrador':'Administrator','Administrador do Demo':'Demo administrator','Conta de administrador protegida':'Protected administrator account','Seleccionar utilizador':'Select a user','Guardar':'Save','Actualizar':'Refresh','Pasta / Relatório':'Folder / Report','Caminho':'Path','Tipo':'Type','Pasta':'Folder','Relatório':'Report','Permissões actuais':'Current permissions','Guardar permissões':'Save permissions','Todas as pastas':'All folders','Abrir pasta':'Open folder','Abrir relatório':'Open report','Fechar relatório':'Close report','授权验证用户':'Verification user','张三':'Example user','Idioma':'Language','Português (Angola)':'English preview','Palavra-passe':'Password','Entrar':'Sign in','Entrar no Demo':'Sign in to Demo','O administrador utiliza admin. Os restantes utilizadores entram com a sua conta.':'Administrators use admin. Other users use their application accounts.'}
D.update(json.loads((R/'extra_ui.json').read_text()))
# Exact text swaps are confined to this browser tab; no server/account data is changed.
def call(*args,input=None):
 p=subprocess.run(['browser-act','--session','p4-video-last',*args],input=input,text=True,capture_output=True)
 if p.returncode:raise RuntimeError(p.stderr+p.stdout)
 return p.stdout
name=sys.argv[1];mode=sys.argv[2]
if mode=='en':
 code='''(()=>{const m=MAP;const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;while(n=w.nextNode()){const s=n.textContent.trim();if(m[s])n.textContent=n.textContent.replace(s,m[s]);else for(const [a,b] of Object.entries(m).sort((a,b)=>b[0].length-a[0].length)){if((a.length>20 || ['Permissão individual','Herdado de /TEST','Todas as pastas (raiz)'].includes(a)) && s.includes(a))n.textContent=n.textContent.replace(a,b);} }for(const e of document.querySelectorAll('[placeholder]')){if(m[e.placeholder])e.placeholder=m[e.placeholder];}return 'local preview translated';})()'''.replace('MAP',json.dumps(D,ensure_ascii=False))
 call('eval','--stdin',input=code)
call('screenshot',str(R/mode/'assets'/f'{name}.png'),'--full')
print(name,mode,'captured')
