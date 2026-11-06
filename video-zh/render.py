import json,math,re,subprocess,shutil,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
import imageio_ffmpeg
ROOT=Path(__file__).parent;OUT=ROOT/'output';FF=imageio_ffmpeg.get_ffmpeg_exe();W,H=1920,1080;FPS=24
INK='#082E5C';TEAL='#00A996';BLUE='#1B64AF';MUTED='#5D748E';BG='#F4F7FB';PALE='#E4EDF7';WHITE='#FFFFFF'
FONT='/System/Library/Fonts/STHeiti Medium.ttc';LIGHT='/System/Library/Fonts/STHeiti Light.ttc'
fonts={}
def font(n,bold=False):
 k=(n,bold)
 if k not in fonts:fonts[k]=ImageFont.truetype(FONT if bold else LIGHT,n)
 return fonts[k]
def txt(d,xy,s,size=34,fill=INK,bold=False,anchor=None):d.text(xy,s,font=font(size,bold),fill=fill,anchor=anchor,spacing=15)
def centered(d,box,s,size=34,color=INK):
 lines=s.split('\n');step=size*1.4;cy=(box[1]+box[3])/2-(len(lines)-1)*step/2
 for j,line in enumerate(lines):txt(d,((box[0]+box[2])/2,cy+j*step),line,size,color,True,'mm')
def wrap(s,n):return '\n'.join(s[i:i+n] for i in range(0,len(s),n))
def box(d,b,label,active=False,size=34):
 d.rounded_rectangle(b,18,fill=INK if active else WHITE,outline=TEAL if active else '#C4D5E7',width=3)
 centered(d,b,label,size,WHITE if active else INK)
def arrow(d,a,b,active=False,progress=1):
 color=TEAL if active else '#AFC4DA';x=a[0]+(b[0]-a[0])*progress;y=a[1]+(b[1]-a[1])*progress
 d.line([a,(x,y)],fill=color,width=6)
 if progress>=.99:
  ang=math.atan2(b[1]-a[1],b[0]-a[0]);d.polygon([b,(b[0]-20*math.cos(ang-.45),b[1]-20*math.sin(ang-.45)),(b[0]-20*math.cos(ang+.45),b[1]-20*math.sin(ang+.45))],fill=color)
def duration(p):
 r=subprocess.run([FF,'-i',str(p)],capture_output=True,text=True);m=re.search(r'Duration: (\d+):(\d+):([\d.]+)',r.stderr);return int(m[1])*3600+int(m[2])*60+float(m[3])
def subtitle_parts(s):
 parts=[]
 for x in re.findall(r'[^，。；！？]+[，。；！？]?',s):
  while len(x)>42:parts.append(x[:36]);x=x[36:]
  if x:parts.append(x)
 return parts
scenes=json.loads((ROOT/'script.json').read_text());timeline=[];time=0
for i,s in enumerate(scenes):
 s['audio_duration']=duration(ROOT/'audio'/f'{i:02}.mp3');s['duration']=math.ceil((s['audio_duration']+.9)*FPS)/FPS;s['start']=time;time+=s['duration'];timeline.append(s)
(ROOT/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2))
assets={}
for name in ['login','users','report','access','rls','portal']:
 im=Image.open(ROOT/'assets'/f'{name}.png').convert('RGB');assets[name]=im

def base(i,s):
 im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
 d.rectangle((0,0,W,13),fill=TEAL);txt(d,(76,43),'P6  /  POWER BI REPORT SERVER',24,MUTED)
 txt(d,(76,100),s['title'],58,INK,True);txt(d,(1836,52),f'{i+1:02} / {len(scenes):02}',24,MUTED,anchor='ra')
 txt(d,(78,186),s['section'],25,BLUE,True)
 d.line((78,230,1842,230),fill='#D8E3EF',width=2)
 return im

def diagram(i,s,t):
 im=base(i,s);d=ImageDraw.Draw(im);kind=s['kind'];stage=min(4,int(t*4.6));p=(t*4.6)%1
 if kind in ('intro','flow','architecture','permissions'):
  if kind=='intro':
   txt(d,(104,306),'使用自己的账号',62,INK,True);txt(d,(104,396),'访问自己的报表与数据',62,INK,True)
   txt(d,(108,525),'系统账号登录    iframe 内嵌    目录授权    RLS',31,MUTED)
   labels=['业务系统','身份与权限接口','PBIRS'];y=715;bh=120
  else:
   labels={'flow':['报表作者\n制作并发布','PBIRS\n报表与数据模型','业务用户\n浏览与交互'], 'architecture':['Demo 后端\n账号与授权接口','稳定用户标识\n身份票据','PBIRS 扩展\n认证与访问检查'], 'permissions':['当前用户','资源权限\n能否打开报表','行级权限\n能看到哪些数据']}[kind];y=390;bh=185
  rects=[(105,y,565,y+bh),(730,y,1190,y+bh),(1355,y,1815,y+bh)]
  active=min(2,int(t*3.4));
  for j,r in enumerate(rects):box(d,r,labels[j],j==active,38)
  for j in range(2):arrow(d,(rects[j][2]+12,y+bh/2),(rects[j+1][0]-12,y+bh/2),active>j,min(1,max(0,t*3.4-j-.35)))
  if kind!='intro':
   notes={'flow':['P6 管理业务入口和用户','PBIRS 负责报表运行与查询'], 'architecture':['当前同机部署，服务各自运行','普通报表请求使用当前用户身份'], 'permissions':['查看报表的权限单独授予','模型角色控制报表内的数据范围']}[kind]
   for j,n in enumerate(notes):txt(d,(145,688+j*72),n,37,INK,j==0)
 elif kind=='compare':
  txt(d,(110,290),'Windows 集成认证',40,INK,True);txt(d,(1100,290),'自定义认证 · 本次选择',40,TEAL,True)
  for x,lines in [(110,['身份来源：AD 域账号','需要维护系统用户与域账号的同步','账号变更涉及两套管理']), (1100,['身份来源：业务系统账号','认证接口确认当前用户','新增用户无需创建域账号'])]:
   for j,line in enumerate(lines):
    if t>.08+j*.12:txt(d,(x,410+j*100),line,35,INK)
  d.line((970,300,970,780),fill='#D1DEEB',width=3)
  d.rounded_rectangle((1075,370,1825,755),20,outline=TEAL,width=4)
 elif kind=='sequence':
  labels=['登录业务系统','签发短时票据','PBIRS 验证票据','建立用户会话','查询与权限检查'];active=min(4,int(t*5.1));coords=[]
  for j,label in enumerate(labels):
   x=80+j*375;b=(x,375,x+330,555);coords.append(b);box(d,b,f'{j+1:02}\n{label}',j==active,32)
   if j:arrow(d,(coords[j-1][2]+6,465),(x-6,465),active>=j)
  txt(d,(120,675),['用户身份来自系统账号','票据短时有效，只消费一次','验证签名、有效期与重放','两个系统分别持有自己的会话','后续请求复用会话，无需再次输入密码'][active],40,INK,True)
  txt(d,(120,763),'SSO 统一身份，报表服务器仍按当前用户检查访问',31,MUTED)
 elif kind=='rules':
  txt(d,(110,292),'模型角色：Province_A',42,INK,True);d.rounded_rectangle((108,380,1010,560),16,fill=INK)
  txt(d,(155,430),'[Province] = "A"',55,WHITE,True)
  rows=[('A','100'),('B','500'),('A','200'),('B','600'),('A','300'),('B','400')]
  for j,(region,amount) in enumerate(rows):
   yy=315+j*78;active=region=='A';d.rounded_rectangle((1190,yy,1780,yy+62),9,fill='#DDF3ED' if active else '#E6EBF1');txt(d,(1230,yy+9),f'区域 {region}                  {amount}',30,TEAL if active else '#8E9CAA')
  txt(d,(112,654),'规则按模型维护',42,INK,True);txt(d,(112,730),'多个用户可以复用同一角色',35,MUTED)
 elif kind=='results':
  vals=[('demo1','Province_A','A 区 3 条',600),('demo2','Province_B','B 区 3 条',1500),('demo3','A + B','全部 6 条',2100)]
  for j,(name,role,scope,value) in enumerate(vals):
   yy=310+j*174;txt(d,(110,yy),name,40,INK,True);txt(d,(350,yy+5),role,30,MUTED);txt(d,(730,yy+5),scope,32,INK)
   end=1120+value/2100*550;pr=min(1,max(0,t*3.2-j*.28));d.rounded_rectangle((1110,yy+62,1110+(end-1110)*pr,yy+98),10,fill=TEAL);txt(d,(1750,yy),f'{round(value*pr):,}',42,INK,True)
  txt(d,(110,877),'Import 模型 / 六条合成测试数据 / 多角色范围叠加',27,MUTED)
 elif kind=='roles':
  box(d,(110,325,610,510),'业务角色\nA 区业务员',True,40);box(d,(775,325,1275,510),'角色成员\ndemo1、demo2',False,38);box(d,(1435,325,1820,510),'报表模型角色\nProvince_A',False,34)
  arrow(d,(625,418),(760,418),True);arrow(d,(1290,418),(1420,418),True)
  txt(d,(115,640),'后台展开具体用户，再写回成员分配',43,INK,True);txt(d,(115,730),'成员或角色绑定变化时，重新计算有效授权',34,MUTED);txt(d,(115,812),'后续设计，尚未实现业务角色自动展开',32,'#A76719',True)
 elif kind=='changes':
  labels=['新增自定义安全扩展','新增自定义登录页','配置系统认证入口','通过接口维护权限'];
  for j,l in enumerate(labels):
   yy=304+j*120;txt(d,(130,yy),f'{j+1:02}',35,TEAL,True);txt(d,(240,yy),l,42,INK,True)
   if t>j*.17:d.line((240,yy+72,1550,yy+72),fill=TEAL,width=4)
  txt(d,(240,836),'保留原有报表引擎和门户，FullTrust 配置未修改',32,MUTED)
 return im

caption={'login':'实际页面 · 自定义登录页调用 Demo 账号验证接口','users':'实际页面 · 新用户默认没有报表查看权限','report':'实际页面 · 外层业务平台，内层 PBIRS 报表查看器','access':'实际页面 · 目录与单报表授权分别保存','rls':'实际页面 · 跨报表勾选角色，一次提交'}
shots={}
for kind in list(caption)+["portal"]:
 source=assets[kind];
 if kind in ('login','portal'):source=source.crop((0,0,source.width,min(source.height,850)))
 elif kind=='access':source=source.crop((280,145,min(source.width,1640),source.height))
 elif kind=='report':source=source.copy()
 else:source=source.crop((180,110,min(source.width,1740),min(source.height,950)))
 # Store zoom phases before encoding; this avoids expensive resizing every frame.
 phases=[]
 for step in range(25):
  z=1+step/24*.035;sw=int(source.width/z);sh=int(source.height/z);cy=(source.height-sh)/2
  crop=source.crop(((source.width-sw)/2,cy,(source.width+sw)/2,cy+sh))
  if kind=='access':
   vh=min(570,source.height);yy=(source.height-vh)*step/24;crop=source.crop((0,yy,source.width,yy+vh))
  phases.append(ImageOps.contain(crop,(1760,670),Image.Resampling.LANCZOS))
 shots[kind]=phases

def screen(i,s,t):
 im=base(i,s);d=ImageDraw.Draw(im);kind=s['kind'];show='portal' if kind=='login' and t>.58 else kind;shot=shots[show][min(24,int(t*24))];x=(W-shot.width)//2;y=250+(670-shot.height)//2;im.paste(shot,(x,y));d=ImageDraw.Draw(im)
 d.rectangle((x-2,y-2,x+shot.width+2,y+shot.height+2),outline='#CAD8E8',width=2)
 txt(d,(80,919),('PBIRS 原生门户 · 登录后按当前用户列出可浏览的目录' if show=='portal' else caption[kind]),24,BLUE)
 # Progress marker and moving spotlight are explanatory overlays, not fake clicks.
 phase=min(2,int(t*3));
 if kind in ['rls','access','users']:
  labels={'rls':['选择用户','勾选模型角色','统一保存并回读'], 'access':['选择用户','选择目录或报表','写入 PBIRS 策略'], 'users':['创建系统账号','管理用户状态','另行分配报表权限']}[kind]
  txt(d,(1780,204),labels[phase],27,TEAL,True,anchor='ra')
 return im

subs=[];global_time=0
for i,s in enumerate(scenes):
 stem=OUT/f'part-{i:02}';output=stem.with_suffix('.mp4')
 parts=subtitle_parts(s['text']);weights=[len(x) for x in parts];total=sum(weights);bounds=[];at=.12
 for text,w in zip(parts,weights):
  end=at+(s['audio_duration']-.12)*w/total;bounds.append((at,end,text));subs.append((s['start']+at,s['start']+end,text));at=end
 if len(sys.argv)>1 and i not in {int(x) for x in sys.argv[1:]}:continue
 frames=int(round(s['duration']*FPS));cached={};subtitle_cache={}
 cmd=[FF,'-y','-f','rawvideo','-vcodec','rawvideo','-s',f'{W}x{H}','-pix_fmt','rgb24','-r',str(FPS),'-i','-','-i',str(ROOT/'audio'/f'{i:02}.mp3'),'-af','apad','-t',str(s['duration']),'-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart',str(output)]
 log=open(OUT/f'part-{i:02}.log','w');proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log,stdout=log)
 for frame in range(frames):
  sec=frame/FPS;t=sec/s['duration'];phase=int(t*100)
  if phase not in cached:
   cached[phase]=screen(i,s,t) if s['kind'] in caption else diagram(i,s,t)
  im=cached[phase].copy();d=ImageDraw.Draw(im)
  d.rectangle((0,962,W,H),fill=INK)
  sub=next((x for a,b,x in bounds if a<=sec<b),'')
  if sub:txt(d,(W/2,1017),sub,33,WHITE,False,'mm')
  d.rectangle((0,1074,int(W*(s['start']+sec)/time),1079),fill=TEAL)
  # Very short fade keeps cuts gentle while retaining crisp screenshots.
  opacity=min(1,sec/.35,(s['duration']-sec)/.35)
  if opacity<1:im=Image.blend(Image.new('RGB',(W,H),INK),im,max(0,opacity))
  proc.stdin.write(im.tobytes())
 proc.stdin.close();rc=proc.wait();log.close()
 if rc:raise RuntimeError(f'Encoding {i} failed')
 print(f'Rendered {i+1}/{len(scenes)} {s["duration"]:.1f}s',flush=True)
 # Save a representative frame for each scene for visual QA.
 preview=screen(i,s,.55) if s['kind'] in caption else diagram(i,s,.55)
 preview.save(OUT/f'preview-{i:02}.jpg',quality=90)

def stamp(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
(OUT/'中文字幕.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(a)} --> {stamp(b)}\n{s}' for i,(a,b,s) in enumerate(subs)))
(OUT/'concat.txt').write_text('\n'.join("file '"+str((OUT/f'part-{i:02}.mp4').resolve())+"'" for i in range(len(scenes))))
final=OUT/'P6与PBIRS集成方案_中文讲解.mp4'
subprocess.run([FF,'-y','-f','concat','-safe','0','-i',str(OUT/'concat.txt'),'-c','copy','-movflags','+faststart',str(final)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
print('FINAL',final,'duration',time,flush=True)
