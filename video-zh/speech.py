import asyncio,json,re
from pathlib import Path
import edge_tts
ROOT=Path(__file__).parent
async def main():
 scenes=[]
 for row in (ROOT/'script.tsv').read_text().splitlines():
  section,title,kind,text=row.split('\t');scenes.append(dict(section=section,title=title,kind=kind,text=text))
 (ROOT/'script.json').write_text(json.dumps(scenes,ensure_ascii=False,indent=2))
 for i,s in enumerate(scenes):
  assert not re.search(r'https?://|Hlkj|P4!|Admin!|172\.26\.',s['text'])
  path=ROOT/'audio'/f'{i:02}.mp3'
  if path.exists() and path.stat().st_size>1000:continue
  await edge_tts.Communicate(s['text'],'zh-CN-XiaoxiaoNeural',rate='+3%').save(str(path))
  print(i+1,'/',len(scenes),flush=True)
asyncio.run(main())
