import subprocess,json,re
from pathlib import Path
import imageio_ffmpeg
R=Path(__file__).parent;O=R/'output';f=imageio_ffmpeg.get_ffmpeg_exe();scenes=json.loads((R/'timeline.json').read_text());source=O/'P6与PBIRS集成方案_中文讲解.mp4';dest=O/'P6与PBIRS集成方案_中文版.mp4'
meta=[';FFMETADATA1','title=P6 与 Power BI Report Server 集成方案','comment=中文合成语音讲解，实际页面与动态原理示意','artist=项目演示']
for s in scenes:
 meta+=['[CHAPTER]','TIMEBASE=1/1000',f'START={round(s["start"]*1000)}',f'END={round((s["start"]+s["duration"])*1000)}','title='+s['title']]
(O/'chapters.ffmeta').write_text('\n'.join(meta))
with (O/'finalize.log').open('w') as log:
 subprocess.run([f,'-y','-i',str(source),'-f','ffmetadata','-i',str(O/'chapters.ffmeta'),'-map','0','-map_metadata','1','-map_chapters','1','-c:v','copy','-c:a','aac','-b:a','160k','-af','loudnorm=I=-16:TP=-1.5:LRA=11','-metadata:s:a:0','language=zho','-movflags','+faststart',str(dest)],stderr=log,stdout=log,check=True)
# Decode the complete final deliverable to detect corrupt frames/audio packets.
r=subprocess.run([f,'-v','error','-i',str(dest),'-f','null','-'],capture_output=True,text=True);assert r.returncode==0 and not r.stderr,r.stderr
for sec,name in [(10,'cover'),(148,'portal'),(325,'rls'),(393,'roles')]:
 subprocess.run([f,'-y','-ss',str(sec),'-i',str(dest),'-frames:v','1',str(O/(name+'-check.jpg'))],capture_output=True,check=True)
probe=subprocess.run([f,'-i',str(dest)],capture_output=True,text=True).stderr
assert '1920x1080' in probe and 'Audio: aac' in probe and 'Video: h264' in probe
(O/'validation.json').write_text(json.dumps({'file':str(dest.resolve()),'bytes':dest.stat().st_size,'durationSeconds':round(sum(s['duration'] for s in scenes),3),'resolution':'1920x1080','fps':24,'chapters':len(scenes),'fullDecode':'passed','audio':'AAC Chinese synthetic narration','source':'actual application screenshots and explanatory animation'},ensure_ascii=False,indent=2))
print(dest.resolve());print('Size MiB',round(dest.stat().st_size/1024**2,1));print('Full decode passed')
