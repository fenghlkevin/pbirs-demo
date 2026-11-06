from pathlib import Path
p=Path('video-zh/render.py').read_text()
p=p.replace("ROOT=Path(__file__).parent;OUT=", "LANG=sys.argv.pop(1);ROOT=Path(__file__).parent/LANG;OUT=")
p=p.replace("fonts={} ","fonts={}")
start=p.index('fonts={}')
end=p.index('def box(')
p=p[:start]+'''if LANG!='zh':
 FONT='/System/Library/Fonts/Supplemental/Arial Bold.ttf';LIGHT='/System/Library/Fonts/Supplemental/Arial.ttf'
LABELS={}
if LANG!='zh':
 for row in (Path(__file__).parent/'labels.tsv').read_text().splitlines():
  cols=row.split('\\t');LABELS[cols[0].replace('\\\\n','\\n')]=cols[1 if LANG=='en' else 2].replace('\\\\n','\\n')
def L(s):
 if LANG=='zh':return s
 if s in LABELS:return LABELS[s]
 if s.startswith('区域 '):return s.replace('区域 ', 'Region ' if LANG=='en' else 'Região ')
 for a,b in LABELS.items():
  if s.endswith(a) and s.startswith(('01','02','03','04','05')):return s[:3]+b
 return s
fonts={}
def font(n,bold=False):
 k=(n,bold)
 if k not in fonts:fonts[k]=ImageFont.truetype(FONT if bold else LIGHT,n)
 return fonts[k]
def txt(d,xy,s,size=34,fill=INK,bold=False,anchor=None):
 s=L(s);limit=1750 if xy[0]<300 else (740 if xy[0]==1100 else 1720)
 if anchor in ('mm','ra'):limit=1750
 while size>20 and max((d.textlength(line,font=font(size,bold)) for line in s.split('\\n')),default=0)>limit:size-=1
 d.text(xy,s,font=font(size,bold),fill=fill,anchor=anchor,spacing=10)
def centered(d,b,s,size=34,color=INK):
 s=L(s);limit=b[2]-b[0]-34
 while size>21 and max(d.textlength(x,font=font(size,True)) for x in s.split('\\n'))>limit:size-=1
 lines=s.split('\\n');step=size*1.4;cy=(b[1]+b[3])/2-(len(lines)-1)*step/2
 for j,line in enumerate(lines):txt(d,((b[0]+b[2])/2,cy+j*step),line,size,color,True,'mm')
def wrap(s,n):return '\\n'.join(s[i:i+n] for i in range(0,len(s),n))
''' +p[end:]
start=p.index('def subtitle_parts(');end=p.index('scenes=json',start)
p=p[:start]+'''def subtitle_parts(s):
 if LANG=='zh':
  parts=[]
  for x in re.findall(r'[^，。；！？]+[，。；！？]?',s):
   while len(x)>42:parts.append(x[:36]);x=x[36:]
   if x:parts.append(x)
  return parts
 import textwrap
 return textwrap.wrap(s,width=96,break_long_words=False,break_on_hyphens=False)
''' + p[end:]
p=p.replace("'中文字幕.srt'","'subtitles.srt'")
p=p.replace("'P6与PBIRS集成方案_中文讲解.mp4'","'assembled.mp4'")
Path('video-multilang/render.py').write_text(p)
