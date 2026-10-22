import argparse,json,subprocess,os,math
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--ffmpeg',default=os.environ.get('FFMPEG_PATH','ffmpeg'));args=p.parse_args()
root=Path(__file__).resolve().parent
timeline=json.loads((root/'timeline.json').read_text(encoding='utf-8'))
video=root/'previews'/timeline.get('output','double11-full-edit-v1.mp4')
ffprobe=str(Path(args.ffmpeg).with_name('ffprobe.exe' if args.ffmpeg.endswith('.exe') else 'ffprobe'))
info=json.loads(subprocess.check_output([ffprobe,'-v','error','-show_streams','-show_format','-of','json',str(video)]))
v=next(s for s in info['streams'] if s['codec_type']=='video');a=next(s for s in info['streams'] if s['codec_type']=='audio')
expected=json.loads((root/'edit-map.json').read_text(encoding='utf-8'))['duration']
assert (v['width'],v['height'],v['r_frame_rate'])==(1080,2376,'30/1')
assert a['channels']==2 and int(a['sample_rate'])==48000
assert abs(float(info['format']['duration'])-expected)<1/30
subprocess.run([args.ffmpeg,'-v','error','-i',str(video),'-f','null','-'],check=True)
last=subprocess.check_output([args.ffmpeg,'-v','error','-i',str(video),'-vf',f"select=eq(n\\,{int(v['nb_frames'])-1})",'-frames:v','1','-pix_fmt','rgb24','-f','rawvideo','pipe:1'])
# H.264 chroma prediction can leave a few code values after the fade; verify visual black.
assert last and max(last)<=3,'Ending must reach black within 8-bit codec tolerance'
frames=timeline.get('reviewFrames',[537,546,1176,1236,1260,1356,1444,1890])
select='+'.join(f'eq(n\\,{n})' for n in frames)
subprocess.run([args.ffmpeg,'-hide_banner','-loglevel','error','-y','-i',str(video),'-vf',f'select={select},scale=270:594,tile=4x2','-frames:v','1',str(root/'previews'/timeline.get('reviewImage','transitions-review.jpg'))],check=True)
state=json.loads((root/'source/part02/preview-state.json').read_text(encoding='utf-8'))
assert len(state['courses'])==11 and sum(c['credits'] for c in state['courses'])==35 and sum(c['sleep'] for c in state['courses'])==20
assert state['sleepBalance']==6
report={'video':video.name,'duration':float(info['format']['duration']),'frames':int(v['nb_frames']),'dimensions':[v['width'],v['height']],'fps':30,'audio':{'codec':a['codec_name'],'channels':2,'sampleRate':48000},'completeDecode':True,'lastFrameMaxRGB':max(last),'order':{'courses':11,'credits':35,'estimatedSleep':20,'sleepBalanceBeforeReceipts':6,'sleepLedger':[6,5,4,3,1],'pendingLedger':[11,10,9,8,7],'failedCost':2,'failedAttemptDeducts':False},'reviewFrames':frames,'byteSize':video.stat().st_size}
if timeline['version']=='full-edit-v2':
 boundary=round(timeline['parts'][0]['ranges'][0][1]*30)
 pair=subprocess.check_output([args.ffmpeg,'-v','error','-i',str(video),'-vf',f'select=eq(n\\,{boundary-1})+eq(n\\,{boundary})','-frames:v','2','-pix_fmt','rgb24','-f','rawvideo','pipe:1'])
 size=1080*2376*3
 assert len(pair)==size*2
 mad=sum(abs(x-y) for x,y in zip(pair[:size],pair[size:]))/size
 assert mad<3,'Card landing differs visibly from Part02 first frame'
 report['cardToList']={'boundaryFrame':boundary,'meanAbsolutePixelDifference':round(mad,6),'cartCountAtEntry':state['initialCount']}
 subprocess.run([args.ffmpeg,'-hide_banner','-loglevel','error','-y','-ss','15.2','-i',str(video),'-t','6.4','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart',str(root/'previews/card-to-list-preview-v2.mp4')],check=True)
(root/'qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
