import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
const DIR=path.dirname(fileURLToPath(import.meta.url));
const require=createRequire(import.meta.url);
let lib;try{lib=require('@napi-rs/canvas');}catch{lib=createRequire(path.join(process.env.CANVAS_MODULE_ROOT||'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules','package.json'))('@napi-rs/canvas');}
const {createCanvas,loadImage,GlobalFonts}=lib;
GlobalFonts.registerFromPath(process.env.FONT_REGULAR||'C:/Windows/Fonts/msyh.ttc','Assembly');
const ffmpeg=process.env.FFMPEG_PATH||'ffmpeg';
const W=1080,H=2376,FPS=30,D=30;
const out=path.join(DIR,'exports');fs.mkdirSync(out,{recursive:true});
const november=await loadImage(path.join(DIR,'source/part03/assets/lockscreen-v2-nov02.png'));
const ui=JSON.parse(fs.readFileSync(path.join(DIR,'source/part03/source/ui-v2.json'),'utf8'));
const chat=await loadImage(Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#121020" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${ui.icons.chat}</svg>`));
const canvas=createCanvas(W,H),c=canvas.getContext('2d');
const layer=createCanvas(W,H),p=layer.getContext('2d');
const clamp=x=>Math.max(0,Math.min(1,x)),ease=x=>1-(1-clamp(x))**3;
const ramp=(t,a,b)=>clamp((t-a)/(b-a));
function rr(ctx,x,y,w,h,r,color){ctx.fillStyle=color;ctx.beginPath();ctx.roundRect(x,y,w,h,r);ctx.fill();}
function text(ctx,value,x,y,size,color,align='left'){ctx.fillStyle=color;ctx.font=`${size}px Assembly`;ctx.textBaseline='top';ctx.textAlign=align;ctx.fillText(value,x,y);}
function arrivalPatch(){c.drawImage(november,840,828,205,72,840,828,205,72);text(c,'待签收 11',1006,860,27,'#fff','right');}
function appPatch(t,transition=false){
 p.clearRect(0,0,W,H);p.save();
 if(transition){const progress=ease((t-6.1)/.75);p.beginPath();p.roundRect(64*(1-progress),912*(1-progress),952+128*progress,198+(H-198)*progress,30*(1-progress));p.clip();}
 const signed=[9.3,10.8,12.1,13.25].filter(start=>t>=start+.13).length;
 rr(p,374,554,50,38,19,'#8600ca');text(p,String(11-signed),399,553,24,'#fff','center');
 rr(p,432,2160,216,146,0,'#fff');p.strokeStyle='#E5DFED';p.lineWidth=1;p.beginPath();p.moveTo(432,2160);p.lineTo(648,2160);p.stroke();
 p.drawImage(chat,508,2178,64,64);text(p,'消息',540,2248,32,'#121020','center');
 let dim=0;
 if(t>=14.78&&t<16.45)dim=Math.min(ramp(t,14.78,14.98),1-ramp(t,16.22,16.45));
 if(t>=16.96)dim=ramp(t,16.96,17.18);
 if(dim>0){p.globalCompositeOperation='source-atop';p.fillStyle=`rgba(25,11,40,${.43*dim})`;p.fillRect(0,0,W,H);p.globalCompositeOperation='source-over';}
 p.restore();c.save();c.globalAlpha=transition?1:1-ease((t-19.55)/.65);c.drawImage(layer,0,0);c.restore();
}
function draw(t){
 c.clearRect(0,0,W,H);
 if(t>=4.35&&t<6.1)arrivalPatch();
 if(t>=6.1&&t<6.85){
  const progress=ease((t-6.1)/.75);c.save();c.beginPath();c.rect(0,0,W,H);c.roundRect(64*(1-progress),912*(1-progress),952+128*progress,198+(H-198)*progress,30*(1-progress));c.clip('evenodd');arrivalPatch();c.restore();appPatch(t,true);
 }else if(t>=6.85&&t<20.2)appPatch(t);
}
// The extra order coalesces into the notification stack; existing receipt costs stay intact.
const sr=48000,pcm=Buffer.alloc(D*sr*4);
for(let i=0;i<.85*sr;i++){
 const t=i/sr;let v=.2*Math.min(1,t/.008)*Math.exp(-5*t/.75)*Math.sin(2*Math.PI*880*t);
 const z=t-.055;if(z>=0)v+=.08*Math.min(1,z/.008)*Math.exp(-6*z/.65)*Math.sin(2*Math.PI*1320*z);
 const val=Math.round(v*32767),pos=(Math.round(4.35*sr)+i)*4;pcm.writeInt16LE(val,pos);pcm.writeInt16LE(val,pos+2);
}
const hdr=Buffer.alloc(44);hdr.write('RIFF');hdr.writeUInt32LE(36+pcm.length,4);hdr.write('WAVE',8);hdr.write('fmt ',12);hdr.writeUInt32LE(16,16);hdr.writeUInt16LE(1,20);hdr.writeUInt16LE(2,22);hdr.writeUInt32LE(sr,24);hdr.writeUInt32LE(sr*4,28);hdr.writeUInt16LE(4,32);hdr.writeUInt16LE(16,34);hdr.write('data',36);hdr.writeUInt32LE(pcm.length,40);
const extra=path.join(out,'extra-arrival.wav');fs.writeFileSync(extra,Buffer.concat([hdr,pcm]));
const args=['-y','-hide_banner','-loglevel','error','-i',path.join(DIR,'source/part03/previews/part03-animation-v3.mp4'),'-f','rawvideo','-pixel_format','rgba','-video_size',`${W}x${H}`,'-framerate',String(FPS),'-i','pipe:0','-i',extra,'-filter_complex','[0:v][1:v]overlay=shortest=1[v];[0:a][2:a]amix=inputs=2:normalize=0,alimiter=limit=.85[a]','-map','[v]','-map','[a]','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-t',String(D),'-movflags','+faststart',path.join(out,'part03-continuity.mp4')];
args.splice(args.indexOf('-c:v'),0,'-threads','4');
const proc=spawn(ffmpeg,args,{stdio:['pipe','ignore','pipe'],windowsHide:true});let tail='';proc.stderr.on('data',b=>tail=(tail+b).slice(-5000));const done=once(proc,'close');let error;proc.stdin.on('error',e=>error=e);
for(let i=0;i<D*FPS;i++){draw(i/FPS);if(error)throw error;if(!proc.stdin.write(Buffer.from(c.getImageData(0,0,W,H).data)))await once(proc.stdin,'drain');if(i%150===0)console.log(`Continuity ${i}/${D*FPS}`);}
proc.stdin.end();const [code]=await done;if(code)throw Error(tail);console.log('Part03 continuity render complete.');
