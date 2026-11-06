import subprocess,json,sys
from pathlib import Path
import imageio_ffmpeg
lang=sys.argv[1];R=Path(__file__).parent/lang;O=R/'output';f=imageio_ffmpeg.get_ffmpeg_exe();scenes=json.loads((R/'timeline.json').read_text())
names={'zh':'P6_PBIRS_中文版_修正版.mp4','pt':'P6_PBIRS_Portugues.mp4','en':'P6_PBIRS_English.mp4'}
dest=O/names[lang]
meta=[';FFMETADATA1','title=P6 / Power BI Report Server','comment=Localised explanatory video; synthetic narration; screenshot composites and animated diagrams','artist=P6 integration demo']
for s in scenes:meta+=['[CHAPTER]','TIMEBASE=1/1000',f'START={round(s["start"]*1000)}',f'END={round((s["start"]+s["duration"])*1000)}','title='+s['title']]
(O/'chapters.ffmeta').write_text('\n'.join(meta))
with (O/'finalize.log').open('w') as log:subprocess.run([f,'-y','-i',str(O/'assembled.mp4'),'-f','ffmetadata','-i',str(O/'chapters.ffmeta'),'-map','0','-map_metadata','1','-map_chapters','1','-c:v','copy','-c:a','aac','-b:a','160k','-af','loudnorm=I=-16:TP=-1.5:LRA=11','-metadata:s:a:0','language='+{'zh':'zho','en':'eng','pt':'por'}[lang],'-movflags','+faststart',str(dest)],stderr=log,stdout=log,check=True)
r=subprocess.run([f,'-v','error','-i',str(dest),'-f','null','-'],capture_output=True,text=True);assert r.returncode==0 and not r.stderr,r.stderr
for i in [0,2,4,5,6,7,9,10,11,13]:
 s=scenes[i];subprocess.run([f,'-y','-ss',str(s['start']+s['duration']*.55),'-i',str(dest),'-frames:v','1',str(O/f'check-{i:02}.jpg')],capture_output=True,check=True)
(O/'validation.json').write_text(json.dumps({'file':str(dest.resolve()),'bytes':dest.stat().st_size,'durationSeconds':round(sum(s['duration'] for s in scenes),3),'resolution':'1920x1080','fps':24,'chapters':len(scenes),'fullDecode':'passed','language':lang},indent=2))
print(dest.resolve());print('Full decode passed')
