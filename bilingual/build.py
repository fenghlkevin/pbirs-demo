import json,re,html
from pathlib import Path
root=Path(__file__).resolve().parent.parent
mapping={}
for line in (root/'bilingual/pt.tsv').read_text().splitlines():
 if line: a,b=line.split('\t',1);mapping[a]=b
s=(root/'index.html').read_text();head,js=s.split('<script>',1);js,tail=js.split('</script>',1)
# Explicit translation calls retain model IDs, usernames and paths as data.
js=re.sub(r"'([^'\n]*[\u4e00-\u9fff][^'\n]*)'",lambda m:'t('+json.dumps(m[1],ensure_ascii=False)+')',js)
# Polish concatenated counters and punctuation in Portuguese.
js=js.replace("+'（'+", "+(lang==='zh-CN'?'（':' (')+")
js=js.replace("+'）'", "+(lang==='zh-CN'?'）':')')")
js=js.replace("?'（'+changed.length", "?(lang==='zh-CN'?'（':' (')+changed.length")
js=js.replace("+'&formatLocale=zh-CN'", "+'&formatLocale='+encodeURIComponent(lang)")
js=js.replace("const e=Error(data.error||t(\"请求失败\"))", "const e=Error(t(data.error||'请求失败'))")
# Translate static text, without placing spans inside option or title elements.
def textnode(m):
 tag,txt=m.group(1),m.group(2)
 if not re.search('[\u4e00-\u9fff]',txt):return m[0]
 key=txt.strip();mapping.setdefault(key,key)
 if tag.startswith('<option') or tag.startswith('<title'):
  return tag[:-1]+' data-i18n="'+html.escape(key,quote=True)+'">'+txt+'<'
 return tag+'<span data-i18n="'+html.escape(key,quote=True)+'">'+txt+'</span><'
head=re.sub(r'(<[^>]+>)([^<>]+)<',textnode,head)
for attr in ['placeholder','aria-label','title']:
 head=re.sub(r'(?<![\w-])'+attr+r'="([^"\n]*[\u4e00-\u9fff][^"\n]*)"',lambda m:attr+'="'+m[1]+'" data-i18n-'+attr+'="'+html.escape(m[1],quote=True)+'"',head)
head=head.replace('<html lang="zh-CN">','<html lang="pt-AO">')
head=head.replace('<div id="session-info"', '<label class="language-control"><span class="sr-only">Idioma / 语言</span><select id="language" aria-label="Idioma / 语言"><option value="pt-AO">Português (Angola)</option><option value="zh-CN">中文</option></select></label><div id="session-info"')
head=head.replace('</style>', '.language-control{margin-left:auto}.language-control select{max-width:220px}.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}#rls-panel .toolbar{align-items:flex-start;flex-wrap:wrap}#rls-panel .actions{flex-shrink:0}table{white-space:normal}td{overflow-wrap:anywhere}td .actions{flex-wrap:wrap}header{flex-wrap:wrap}#session-info{flex-wrap:wrap}</style>')
i18n='''const PT = DICT;
function initialLanguage(){const query=new URLSearchParams(location.search).get('lang');const cookie=document.cookie.match(/(?:^|; )P4DemoLang=([^;]+)/)?.[1];return (query||cookie)==='zh-CN'?'zh-CN':'pt-AO'}
let lang=initialLanguage();
function t(value){if(lang==='zh-CN'||typeof value!=='string')return value;if(Object.prototype.hasOwnProperty.call(PT,value))return PT[value];if(value.startsWith('PBIRS 授权操作失败（HTTP '))return PT['PBIRS 授权操作失败（HTTP ']+value.slice('PBIRS 授权操作失败（HTTP '.length).replace('）',')');return value}
function applyLanguage(){document.documentElement.lang=lang;document.cookie='P4DemoLang='+lang+'; Path=/; Max-Age=31536000; SameSite=Lax';document.getElementById('language').value=lang;for(const node of document.querySelectorAll('[data-i18n]'))node.textContent=t(node.dataset.i18n);for(const attr of ['placeholder','aria-label','title'])for(const node of document.querySelectorAll('[data-i18n-'+attr+']'))node.setAttribute(attr,t(node.getAttribute('data-i18n-'+attr)));document.title=t('P4 Demo · 用户与报表')}
'''.replace('DICT',json.dumps(mapping,ensure_ascii=False))
js=i18n+js
js=js.replace("api('/api/me').then(enter).catch(()=>{});",'''$('language').onchange=async()=>{lang=$('language').value;applyLanguage();notify('');if(me){$('current-user').textContent=(me.displayName||me.username)+' · '+t(me.role==='admin'?'管理员':'普通用户');const active=document.querySelector('[data-tab][aria-selected=true]')?.dataset.tab;if(active==='reports')renderReports();if(active==='users')await loadUsers();if(active==='access'){renderAccess();if($('access-user').value){const u=users.find(u=>u.username===$('access-user').value);$('access-title').textContent=(u?.displayName||$('access-user').value)+t(' · 目录与报表授权')}}if(active==='rls'){for(const o of $('rls-user').options){if(!o.value)o.textContent=t('请选择普通用户')}renderRlsUser()}if(!$('viewer').hidden&&$('frame').src.includes('formatLocale=')){const u=new URL($('frame').src);u.searchParams.set('formatLocale',lang);$('frame').src=u.href}}$('reset-title').textContent=t('重置 ')+$('reset-form').elements.username.value+t(' 的密码')};
applyLanguage();api('/api/me').then(enter).catch(()=>{});''')
(root/'index.html').write_text(head+'<script>'+js+'</script>'+tail)
(root/'bilingual/translations.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2))
missing=[x for x in json.loads((root/'bilingual/strings.json').read_text()) if x not in mapping];print('Missing translations:',missing)
