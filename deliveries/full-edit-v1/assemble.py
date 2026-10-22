"""Rebuild the edit from explicit source ranges; no source projects are overwritten."""
import argparse,json,os,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--ffmpeg',default=os.environ.get('FFMPEG_PATH','ffmpeg'));args=p.parse_args()
root=Path(__file__).resolve().parent
timeline=json.loads((root/'timeline.json').read_text(encoding='utf-8'))
out=root/'exports';out.mkdir(exist_ok=True)
preview=root/'previews';preview.mkdir(exist_ok=True)
filters=[];inputs=[];concat=[];segments=[];position=0
for index,part in enumerate(timeline['parts']):
 source=root/part['input']
 if not source.exists():raise SystemExit('Missing input: '+str(source))
 inputs+=['-i',str(source)]
 for j,(start,end) in enumerate(part['ranges']):
  v=f'v{index}_{j}';a=f'a{index}_{j}'
  filters+=[f'[{index}:v]trim=start={start}:end={end},setpts=PTS-STARTPTS,fps=30,setsar=1[{v}]',f'[{index}:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,afade=t=in:d=0.006,afade=t=out:st={end-start-.008}:d=0.008[{a}]']
  concat.append(f'[{v}][{a}]');segments.append({'part':part['id'],'sourceIn':start,'sourceOut':end,'masterIn':round(position,6),'masterOut':round(position+end-start,6)});position+=end-start
filters+=[''.join(concat)+f'concat=n={len(concat)}:v=1:a=1[v][a]']
filters+=['[a]alimiter=limit=.95:level=0:latency=1[am]']
script=out/'filters.txt';script.write_text(';\n'.join(filters),encoding='utf-8')
video=preview/timeline.get('output','double11-full-edit-v1.mp4')
subprocess.run([args.ffmpeg,'-hide_banner','-loglevel','warning','-y',*inputs,'-filter_complex',';'.join(filters),'-map','[v]','-map','[am]','-threads','4','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-ac','2','-b:a','160k','-movflags','+faststart',str(video)],check=True)
(root/'edit-map.json').write_text(json.dumps({'duration':round(position,6),'segments':segments},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'video':str(video),'expectedDuration':position},ensure_ascii=False))
