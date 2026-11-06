from pathlib import Path
import json,re,shutil,asyncio,edge_tts
R=Path(__file__).parent;Z=R.parent/'video-zh'
PRON={'行级':'杭级','行过滤':'杭过滤','数据行':'数据杭','每一行':'每一杭'}
async def main():
 for lang,voice in [('zh','zh-CN-XiaoxiaoNeural'),('pt','pt-PT-RaquelNeural'),('en','en-GB-SoniaNeural')]:
  root=R/lang
  if lang=='zh':scenes=json.loads((Z/'script.json').read_text())
  else:scenes=[dict(zip(['section','title','kind','text'],row.split('\t'))) for row in (R/(lang+'.tsv')).read_text().splitlines()]
  (root/'script.json').write_text(json.dumps(scenes,ensure_ascii=False,indent=2))
  for i,s in enumerate(scenes):
   text=s['text']
   if lang=='zh':
    for old,new in PRON.items():text=text.replace(old,new)
   assert not re.search(r'https?://|Hlkj|Admin!|172\.26\.',text)
   path=root/'audio'/f'{i:02}.mp3'
   if lang=='zh' and text==s['text'] and not path.exists():shutil.copy(Z/'audio'/f'{i:02}.mp3',path)
   if path.exists() and path.stat().st_size>1000:continue
   await edge_tts.Communicate(text,voice,rate='+3%' if lang=='zh' else '+0%').save(str(path))
   print(lang,i+1,'/15',flush=True)
  (root/'pronunciation.json').write_text(json.dumps(PRON if lang=='zh' else {'voice':voice,'locale':'pt-AO wording, pt-PT voice' if lang=='pt' else 'en-GB'},ensure_ascii=False,indent=2))
asyncio.run(main())
