import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import fs from 'node:fs';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {PresenterVideo} from './presenter-video.mjs';

const DIR=path.dirname(fileURLToPath(import.meta.url));
const ROOT=path.resolve(DIR,'../..');
const require=createRequire(import.meta.url);
let canvasLib;
try {canvasLib=require('@napi-rs/canvas');} catch {
  const bundled=process.env.CANVAS_MODULE_ROOT || 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
  canvasLib=createRequire(path.join(bundled,'package.json'))('@napi-rs/canvas');
}
const {createCanvas,loadImage,GlobalFonts}=canvasLib;
for(const [file,name] of [[process.env.FONT_REGULAR || 'C:/Windows/Fonts/msyh.ttc','YaHei'],[process.env.FONT_BOLD || 'C:/Windows/Fonts/msyhbd.ttc','YaHei Bold']]){
  if(fs.existsSync(file))GlobalFonts.registerFromPath(file,name);
}
const S=JSON.parse(fs.readFileSync(path.join(DIR,'scene.json'),'utf8'));
const OUT=path.join(DIR,'exports'); fs.mkdirSync(OUT,{recursive:true});
const SCALE=process.argv.includes('--half')?0.5:1;
const W=Math.round(S.width*SCALE),H=Math.round(S.height*SCALE);
const canvas=createCanvas(W,H),c=canvas.getContext('2d');
const liveCanvas=createCanvas(1080,2376),l=liveCanvas.getContext('2d');
const home=await loadImage(path.join(ROOT,'assets/references/home-v1.png'));
const presenter=await loadImage(path.join(DIR,S.presenterImages?.megaphone || 'assets/bookseller-megaphone.png'));
const presenterBook=await loadImage(path.join(DIR,S.presenterImages?.book || 'assets/bookseller-book.png'));
const presenterFile=S.presenterVideo?.file&&path.join(DIR,S.presenterVideo.file);
if(presenterFile&&!fs.existsSync(presenterFile))throw Error('Configured presenter clip is missing: '+presenterFile);
const presenterVideo=presenterFile?new PresenterVideo({file:presenterFile,ffmpeg:process.env.FFMPEG_PATH||'ffmpeg',fps:S.fps,createCanvas,ImageData:canvasLib.ImageData}):null;
let presenterFrame=null;
const purple='#660099',ink='#171525',muted='#858398';
const clamp=(x)=>Math.max(0,Math.min(1,x));
const ease=(x)=>{x=clamp(x);return x*x*(3-2*x);};
const outCubic=(x)=>1-Math.pow(1-clamp(x),3);
const lerp=(a,b,t)=>a+(b-a)*t;
const stage=(t,key)=>{const [a,b]=S.scenes[key];return clamp((t-a)/(b-a));};

function rr(ctx,x,y,w,h,r,fill,stroke,width=2){
  ctx.beginPath();ctx.roundRect(x,y,w,h,r);
  if(fill){ctx.fillStyle=fill;ctx.fill();}
  if(stroke){ctx.strokeStyle=stroke;ctx.lineWidth=width;ctx.stroke();}
}
function text(ctx,s,x,y,size=34,color=ink,bold=false,align='left'){
  ctx.font=`${bold?'700':'400'} ${size}px "${bold?'YaHei Bold':'YaHei'}","Microsoft YaHei",sans-serif`;
  ctx.fillStyle=color;ctx.textAlign=align;ctx.textBaseline='middle';ctx.fillText(s,x,y);
}
function line(ctx,pts,color,width=4){ctx.beginPath();ctx.strokeStyle=color;ctx.lineWidth=width;ctx.lineCap='round';ctx.lineJoin='round';ctx.moveTo(...pts[0]);for(const p of pts.slice(1))ctx.lineTo(...p);ctx.stroke();}
function crop(ctx,rect,x,y,w,h,r=0){
  ctx.save();if(r){ctx.beginPath();ctx.roundRect(x,y,w,h,r);ctx.clip();}
  let [sx,sy,sw,sh]=rect;
  const ratio=w/h;
  if(sw/sh>ratio){const nw=sh*ratio;sx+=(sw-nw)/2;sw=nw;}else{const nh=sw/ratio;sy+=(sh-nh)/2;sh=nh;}
  ctx.drawImage(home,sx,sy,sw,sh,x,y,w,h);ctx.restore();
}
function cover(ctx,img,x,y,w,h,zoom=1){
  const scale=Math.max(w/img.width,h/img.height)*zoom;
  ctx.drawImage(img,x+(w-img.width*scale)/2,y+(h-img.height*scale)/2,img.width*scale,img.height*scale);
}
function status(ctx,dark=false){
  const color=dark?'#fff':ink;
  text(ctx,S.time,58,59,38,color,true);
  ctx.strokeStyle=color;ctx.lineWidth=5;
  for(let n=0;n<3;n++){ctx.beginPath();ctx.arc(770,62,13+n*11,Math.PI*1.17,Math.PI*1.83);ctx.stroke();}
  rr(ctx,768,70,5,5,3,color);
  for(let i=0;i<4;i++)rr(ctx,824+i*11,67-i*8,6,15+i*8,1,color);
  text(ctx,'5G',875,42,17,color,true);
  rr(ctx,932,41,70,32,7,dark?'#fff':'#777',color,3);rr(ctx,1005,50,4,14,1,color);
  text(ctx,'53',966,58,23,dark?'#25212c':'#fff',true,'center');
}
function icon(ctx,type,x,y,color,size=56){
  ctx.save();ctx.translate(x,y);ctx.scale(size/56,size/56);
  if(type==='home'){line(ctx,[[-27,0],[0,-23],[27,0],[24,28],[8,28],[8,8],[-8,8],[-8,28],[-24,28],[-27,0]],color,5);}
  if(type==='live'){rr(ctx,-28,-21,56,48,10,null,color,5);ctx.fillStyle=color;ctx.beginPath();ctx.moveTo(-6,-9);ctx.lineTo(13,3);ctx.lineTo(-6,15);ctx.fill();}
  if(type==='message'){rr(ctx,-28,-22,56,45,17,null,color,5);line(ctx,[[-20,17],[-25,32],[-5,22]],color,4);for(let i=-13;i<=13;i+=13)rr(ctx,i-2,-2,5,5,3,color);}
  if(type==='cart'){line(ctx,[[-29,-24],[-20,-24],[-12,15],[24,15],[29,-13],[-17,-13]],color,5);for(const xx of [-7,20])rr(ctx,xx-4,25,8,8,5,color);}
  if(type==='profile'){ctx.strokeStyle=color;ctx.lineWidth=5;ctx.beginPath();ctx.arc(0,3,26,0,Math.PI*2);ctx.stroke();ctx.beginPath();ctx.arc(0,5,12,.12*Math.PI,.88*Math.PI);ctx.stroke();}
  ctx.restore();
}
function navigation(ctx,active=0){
  rr(ctx,0,2118,1080,258,0,'#fff');line(ctx,[[0,2118],[1080,2118]],'#e8e7ee',2);
  const labels=['首页','直播','消息','选课车','我的课表'],types=['home','live','message','cart','profile'];
  for(let i=0;i<5;i++){const x=108+i*216,color=i===active?purple:ink;icon(ctx,types[i],x,2174,color,64);text(ctx,labels[i],x,2246,31,color,i===active,'center');
    if(i===2||(i===3&&S.cartInitialCount>0)){rr(ctx,x+15,2125,55,44,23,purple);text(ctx,i===2?'29':String(S.cartInitialCount),x+42,2147,28,'#fff',true,'center');}
  }
  line(ctx,[[260,2318],[285,2318]],'#999',3);line(ctx,[[260,2327],[285,2327]],'#999',3);rr(ctx,525,2308,29,29,8,null,'#999',3);line(ctx,[[822,2308],[800,2324],[822,2339],[822,2308]],'#999',3);
}
function course(ctx,key,title,credits,tag,x,y){
  rr(ctx,x,y,498,650,24,'#fff');
  if(S.referenceCrops[key])crop(ctx,S.referenceCrops[key],x+12,y+12,474,430,17);
  else {
    const palette={algebra:['#efe8fa','#714aa6','线性代数'],probability:['#e6edf8','#466693','概率与统计'],coding:['#e7edf8','#424a76','程序设计'],art:['#f7e6ed','#9c637f','艺术导论'],psychology:['#e8f0ec','#527b6b','心理学'],writing:['#f2eaf6','#77578c','学术写作'],library:['#ece6f5','#69598a','信息检索'],photo:['#eee9f3','#655c7a','摄影基础']};
    const [bg,fg,label]=palette[key];rr(ctx,x+12,y+12,474,430,17,bg);ctx.save();ctx.translate(x+104,y+42);ctx.rotate(-.07);
    rr(ctx,0,0,295,356,8,'#fff');rr(ctx,0,0,18,356,5,fg);text(ctx,'清华选课',40,39,18,fg);
    text(ctx,label,37,115,label.length>5?32:40,fg,true);
    for(let k=0;k<4;k++)line(ctx,[[42,190+k*30],[243-k*18,190+k*30]],fg,2);
    ctx.restore();
  }
  text(ctx,title,x+25,y+474,title.length>8?31:35,ink,true);
  text(ctx,`${credits}学分`,x+25,y+541,39,purple,true);
  text(ctx,tag,x+25,y+605,26,muted);
  rr(ctx,x+410,y+515,58,58,15,null,purple,3);
  line(ctx,[[x+423,y+544],[x+455,y+544]],purple,3);line(ctx,[[x+439,y+528],[x+439,y+560]],purple,3);
}
function adCarousel(t){
  const position=outCubic((t-2.7)/.33)+outCubic((t-3.55)/.33);
  c.save();c.beginPath();c.roundRect(28,462,1024,306,26);c.clip();
  for(let i=0;i<S.advertisements.length;i++){
    c.save();c.translate(28+(i-position)*1024,462);
    const ad=S.advertisements[i],bg=c.createLinearGradient(0,0,1024,306);bg.addColorStop(0,['#f1e3ff','#e8ddf6','#f4e9ff'][i]);bg.addColorStop(1,['#c8b0ed','#c2afd9','#d9c4ee'][i]);c.fillStyle=bg;c.fillRect(0,0,1024,306);
    rr(c,38,30,170,42,21,'rgba(255,255,255,.68)');text(c,ad.badge,123,51,24,purple,true,'center');
    text(c,ad.title,40,126,57,purple,true);text(c,ad.copy,42,211,40,purple,true);
    if(i===0)crop(c,S.referenceCrops.banner,695,0,329,306,0);
    if(i===1){c.strokeStyle='#8051a5';c.lineWidth=8;c.beginPath();c.arc(837,150,95,0,Math.PI*2);c.stroke();line(c,[[837,89],[837,150],[888,178]],purple,8);}
    if(i===2)crop(c,S.referenceCrops.flowers,715,0,309,306,0);
    c.restore();
  }
  c.restore();
  for(let i=0;i<3;i++)rr(c,486+i*34,741,i===Math.round(position)?28:13,7,4,i===Math.round(position)?purple:'#bba5d0');
  for(const start of [2.7,3.55]){const p=(t-start)/.33;if(p>0&&p<1){c.save();c.globalAlpha=Math.sin(Math.PI*p)*.75;rr(c,880-560*p,628,27,27,14,'#fff');c.restore();}}
}
function homePage(t){
  const bg=c.createLinearGradient(0,0,1080,2000);bg.addColorStop(0,'#f7f4ff');bg.addColorStop(1,'#f0f0f8');c.fillStyle=bg;c.fillRect(0,0,1080,2376);
  c.save();rr(c,0,98,1080,2020,0);c.clip();
  let offset=0;
  for(const g of S.browseGestures){if(t>=g.start)offset=lerp(g.from,g.to,outCubic((t-g.start)/(g.end-g.start)));}
  c.translate(0,-offset);
  crop(c,[30,98,82,73],40,122,86,76);
  text(c,'清华选课',157,165,52,ink,true);
  for(const [i,s] of ['推荐','通识','专业','体育'].entries())text(c,s,140+267*i,278,44,i===0?purple:muted,i===0,'center');
  rr(c,119,313,45,7,4,purple);
  rr(c,28,337,1024,100,28,'#fff',purple,2);c.strokeStyle=purple;c.lineWidth=4;c.beginPath();c.arc(83,385,16,0,Math.PI*2);c.stroke();line(c,[[96,398],[110,412]],purple,4);
  text(c,'搜索课程',135,388,37,muted);rr(c,856,345,187,84,22,purple);text(c,'搜索',950,387,36,'#fff',true,'center');
  adCarousel(t);
  rr(c,20,790,1040,205,25,'#fff');
  const quick=['培养方案','通识好课','限量体育','选课直播'];
  for(let i=0;i<4;i++){const x=155+257*i;rr(c,x-48,814,96,96,48,'#f0e2ff');icon(c,['profile','message','cart','live'][i],x,860,purple,42);text(c,quick[i],x,954,32,ink,false,'center');}
  text(c,'课程推荐',30,1060,46,ink,true);text(c,'全部课程 ›',1040,1060,30,muted,false,'right');
  c.drawImage(courseFeed,0,1110);
  c.restore();
  rr(c,0,0,1080,100,0,'#f8f6ff');status(c);navigation(c,0);
}
function livePage(t){
  l.clearRect(0,0,1080,2376);
  l.fillStyle='#27222e';l.fillRect(0,0,1080,2376);
  // A configured video uses the same decoded frame in both live layouts.
  l.save();l.beginPath();l.rect(0,95,1080,2023);l.clip();cover(l,presenterFrame||(t<12.1?presenter:presenterBook),0,95,1080,2023,presenterFrame?1:1+0.004*Math.sin(t/6));l.restore();
  const shade=l.createLinearGradient(0,0,0,650);shade.addColorStop(0,'rgba(10,6,18,.65)');shade.addColorStop(1,'rgba(10,6,18,0)');l.fillStyle=shade;l.fillRect(0,0,1080,650);
  status(l,true);
  rr(l,30,128,580,94,47,'rgba(0,0,0,.27)');l.save();l.beginPath();l.arc(80,175,40,0,Math.PI*2);l.clip();l.drawImage(presenter,250,220,420,420,40,135,80,80);l.restore();
  text(l,'老板的学分书摊',142,176,35,'#fff',true);
  rr(l,451,143,142,64,32,purple);text(l,'直播中',522,175,29,'#fff',false,'center');
  rr(l,756,143,220,64,32,'rgba(0,0,0,.35)');text(l,'1.5万人观看',866,175,26,'#fff',false,'center');line(l,[[1010,155],[1040,185]],'#fff',5);line(l,[[1040,155],[1010,185]],'#fff',5);
  rr(l,32,269,446,96,22,'rgba(102,0,153,.88)','#e3c1ff',2);text(l,'双11  学分专场',255,317,40,'#fff',true,'center');
  rr(l,641,280,407,190,23,'rgba(255,251,255,.95)');crop(l,S.referenceCrops.flowers,661,303,115,144,14);
  text(l,'花卉鉴赏',795,326,36,ink,true);text(l,'2学分',795,379,36,purple,true);text(l,'早八精品',795,429,29,muted);
  const lp=clamp((t-10)/2);
  for(let i=0;i<3;i++){
    const y=1650-((t*45+i*112)%350);l.save();l.globalAlpha=(.35+.3*Math.sin(t+i))*lp;l.translate(1000,y);l.scale(.8+i*.1,.8+i*.1);
    l.beginPath();l.moveTo(0,20);l.bezierCurveTo(-56,-10,-32,-45,0,-20);l.bezierCurveTo(32,-45,56,-10,0,20);l.fillStyle='#c77aef';l.fill();l.restore();
  }
  const p=outCubic(stage(t,'courseCardAppear'));
  if(p>0){l.save();l.translate(0,(1-p)*380);l.globalAlpha=p;
    rr(l,28,1760,1024,306,28,'#fff');crop(l,S.referenceCrops.flowers,48,1780,232,265,18);
    text(l,'花卉鉴赏',310,1820,43,ink,true);text(l,'早八精品 · 美育好课',310,1882,29,muted);text(l,'2学分',310,1987,49,purple,true);
    rr(l,752,1866,268,110,23,purple);text(l,'加入选课车',886,1921,33,'#fff',true,'center');l.restore();
  }
  navigation(l,1);
}
function floatingLive(t){
  const appear=outCubic(stage(t,'liveWindowAppear'));
  if(!appear)return;
  const pop=stage(t,'liveWindowExpand');
  const expanded=pop===0?0:pop===1?1:1+2.70158*Math.pow(pop-1,3)+1.70158*Math.pow(pop-1,2);
  const start={x:770,y:193,w:270,h:410};
  const x=lerp(start.x,0,expanded)+(1-appear)*110,y=lerp(start.y,0,expanded);
  const w=lerp(start.w,1080,expanded),h=lerp(start.h,2376,expanded),r=Math.max(0,lerp(24,0,expanded));
  const press=pop===0?1-.065*Math.sin(Math.PI*clamp((t-7.88)/.17)):1;
  c.save();c.globalAlpha=appear;
  c.translate(x+w/2,y+h/2);c.scale(press,press);c.translate(-(x+w/2),-(y+h/2));
  c.shadowColor='rgba(49,8,69,.25)';c.shadowBlur=32;c.shadowOffsetY=12;rr(c,x,y,w,h,r,'#201c27');c.shadowColor='transparent';
  c.beginPath();c.roundRect(x,y,w,h,r);c.clip();
  // Same source frame is present in the small window and the expanded live view.
  if(pop===0)cover(c,presenterFrame||presenter,x,y,w,h-38);
  else c.drawImage(liveCanvas,0,lerp(350,0,clamp(expanded)),1080,lerp(1500,2376,clamp(expanded)),x,y,w,h);
  if(pop<.5){c.save();c.globalAlpha=1-pop*2;
    rr(c,x,y+h-46,w,46,0,'rgba(102,0,153,.95)');
    for(let i=0;i<3;i++){const bh=9+Math.abs(Math.sin(t*7+i))*15;rr(c,x+18+i*8,y+h-13-bh,4,bh,2,'#fff');}
    text(c,'直播中',x+61,y+h-23,22,'#fff',true);text(c,'书摊甩卖',x+w-12,y+h-23,18,'#ead8ff',false,'right');c.restore();
  }
  c.restore();
}
function opening(t){
  const p=ease(stage(t,'openingToHome'));
  if(p>=1)return;
  c.save();c.globalAlpha=1-p;
  const g=c.createLinearGradient(0,0,1080,2376);g.addColorStop(0,'#fbf8ff');g.addColorStop(.6,'#eee2fb');g.addColorStop(1,'#e9def4');c.fillStyle=g;c.fillRect(0,0,1080,2376);status(c);
  const y=lerp(1030,165,p),size=lerp(63,46,p);
  text(c,'欢迎进入清华大学',540,y,size,purple,true,'center');text(c,'双十一学分专场',540,y+95*(1-p),size,purple,true,'center');
  text(c,'知识好物，限时开抢！',540,1210-700*p,35,'#9773b1',false,'center');
  rr(c,438,1375-700*p,204,7,4,'#d5b5ec');rr(c,438,1375-700*p,204*clamp(t/1.4),7,4,purple);
  c.restore();
}
function touch(t){
  const p=(t-7.85)/.2;if(p<0||p>1)return;
  c.save();c.globalAlpha=Math.sin(Math.PI*p)*.7;c.strokeStyle='#fff';c.lineWidth=4;c.beginPath();c.arc(905,410,12+17*p,0,Math.PI*2);c.stroke();c.restore();
}
async function render(t){
  if(presenterVideo){const sourceTime=Math.max(0,t-S.presenterVideo.start)+(S.presenterVideo.trimStart||0);presenterFrame=await presenterVideo.frame(Math.min(sourceTime,(S.presenterVideo.trimEnd||Infinity)-1/S.fps));}
  c.resetTransform();c.clearRect(0,0,W,H);c.scale(SCALE,SCALE);
  const sceneT=Math.min(t,S.scenes.tailHold[0]);
  homePage(sceneT);livePage(sceneT);floatingLive(sceneT);touch(sceneT);opening(sceneT);
  const light=ease(stage(t,'openingFade'));
  if(light<1){c.fillStyle=`rgba(18,12,24,${1-light})`;c.fillRect(0,0,1080,2376);}
}
const courseFeed=createCanvas(1080,Math.ceil(S.courses.length/2)*670);
const feedCtx=courseFeed.getContext('2d');
for(let i=0;i<S.courses.length;i++){const row=Math.floor(i/2),item=S.courses[i];course(feedCtx,item.key,item.title,item.credits,item.tag,i%2?562:20,row*670);}
const marks=[...new Set([0.8,2.4,3.1,3.95,4.8,6.2,7.6,7.98,8.15,8.35,11.2,13.1,15.8,S.duration-.05].filter(t=>t<S.duration))].sort((a,b)=>a-b);
for(const t of marks){await render(t);fs.writeFileSync(path.join(OUT,`frame-${t.toFixed(2)}.png`),canvas.toBuffer('image/png'));}
await render(S.duration-1/S.fps);fs.writeFileSync(path.join(DIR,'live-card-end.png'),canvas.toBuffer('image/png'));
presenterVideo?.close();

function writeAudio(filename){
  const rate=48000,count=Math.ceil(S.duration*rate);const pcm=Buffer.alloc(count*2);
  const events=[{t:6.3,d:.16,f:660,g:.10},{t:7.94,d:.07,f:900,g:.11},{t:8.08,d:.12,f:620,g:.07},{t:S.scenes.courseCardAppear[0],d:.22,f:600,g:.09}];
  for(let i=0;i<count;i++){const t=i/rate;let v=0;for(const e of events){const z=t-e.t;if(z>=0&&z<e.d){const env=Math.pow(Math.sin(Math.PI*z/e.d),2)*Math.exp(-9*z);v+=Math.sin(2*Math.PI*e.f*z)*env*e.g;}}pcm.writeInt16LE(Math.max(-32767,Math.min(32767,Math.round(v*32767))),i*2);}
  const hdr=Buffer.alloc(44);hdr.write('RIFF');hdr.writeUInt32LE(36+pcm.length,4);hdr.write('WAVE',8);hdr.write('fmt ',12);hdr.writeUInt32LE(16,16);hdr.writeUInt16LE(1,20);hdr.writeUInt16LE(1,22);hdr.writeUInt32LE(rate,24);hdr.writeUInt32LE(rate*2,28);hdr.writeUInt16LE(2,32);hdr.writeUInt16LE(16,34);hdr.write('data',36);hdr.writeUInt32LE(pcm.length,40);fs.writeFileSync(filename,Buffer.concat([hdr,pcm]));
}
if(!process.argv.includes('--frames-only')){
  const ffmpeg=process.env.FFMPEG_PATH || 'ffmpeg';
  const effects=path.join(OUT,'interface-effects.wav');writeAudio(effects);
  const file=path.join(OUT,`part-01-interface-preview-${S.version}${SCALE===1?'':'-half'}.mp4`);
  const args=['-y','-f','rawvideo','-pixel_format','rgba','-video_size',`${W}x${H}`,'-framerate',String(S.fps),'-i','pipe:0','-i',effects];
  const voice=S.audio.voice && path.join(DIR,S.audio.voice);
  if(presenterVideo&&S.presenterVideo.useAudio){
    const voiceFilter=S.audio.voiceFilter||{highpass:250,lowpass:5000};
    args.push('-i',presenterFile,'-filter_complex',`[2:a]atrim=start=${S.presenterVideo.trimStart||0}${S.presenterVideo.trimEnd?`:end=${S.presenterVideo.trimEnd}`:''},asetpts=PTS-STARTPTS,highpass=f=${voiceFilter.highpass},lowpass=f=${voiceFilter.lowpass},alimiter=limit=0.85,adelay=${S.presenterVideo.start*1000}:all=1[voice];[1:a][voice]amix=inputs=2:duration=first:normalize=0[a]`,'-map','0:v:0','-map','[a]');
  }else if(voice && fs.existsSync(voice)){
    const tempo=S.audio.voiceDuration/S.audio.voiceTargetDuration;
    args.push('-i',voice,'-filter_complex',`[2:a]atempo=${tempo},highpass=f=450,lowpass=f=3800,volume=1.1,alimiter=limit=0.7,adelay=${S.audio.voiceStart*1000}:all=1[voice];[1:a][voice]amix=inputs=2:duration=first:normalize=0[a]`,'-map','0:v:0','-map','[a]');
  }
  args.push('-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart','-shortest',file);
  const proc=spawn(ffmpeg,args,{stdio:['pipe','ignore','pipe']});let tail='';proc.stderr.on('data',b=>{tail=(tail+b.toString()).slice(-7000);});proc.on('error',err=>{console.error(err.message);});
  let pipeError;proc.stdin.on('error',e=>{pipeError=e;});
  const total=Math.round(S.duration*S.fps);
  for(let frame=0;frame<total;frame++){
    await render(frame/S.fps);
    const data=Buffer.from(c.getImageData(0,0,W,H).data);
    if(pipeError)throw pipeError;
    if(!proc.stdin.write(data))await once(proc.stdin,'drain');
    if(frame%90===0)console.log(`Rendered ${frame}/${total}`);
  }
  proc.stdin.end();const [code]=await once(proc,'close');presenterVideo?.close();if(code!==0)throw Error(tail);console.log(`Saved ${file}`);
}
console.log('Key frames and handoff frame saved.');
