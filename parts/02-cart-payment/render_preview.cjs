// Deterministic renderer. Arguments: playwright-core module, browser, ffmpeg, [stills].
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {spawn} = require('node:child_process');
const {once} = require('node:events');
const [modulePath, browserPath, ffmpegPath, mode] = process.argv.slice(2);
const {chromium} = require(modulePath || 'playwright');
const here = __dirname;
const config = JSON.parse(fs.readFileSync(path.join(here,'preview-state.json'),'utf8'));
const keys = [['01-list',0],['02-rush',4.73],['03-courses',5.65],['04-cart',7.75],['05-cost',14.05],['06-deferred',15.80],['07-success',20.10],['08-lockscreen',24.25],['09-black',27.2],['10-transfer',14.75],['11-countdown',15.20]];
const keyDir = path.join(here,'keyframes',config.version);
const expectedCount=config.courses.length,expectedCredits=config.courses.reduce((s,c)=>s+c.credits,0),expectedSleep=config.courses.reduce((s,c)=>s+c.sleep,0),requiredCount=config.courses.filter(c=>c.required).length;
(async()=>{
 const started = Date.now();
 fs.mkdirSync(keyDir,{recursive:true});
 fs.mkdirSync(path.join(here,'renders'),{recursive:true});
 console.log('Playwright loaded. Launching headless browser.');
 const browser=await chromium.launch({executablePath:browserPath,headless:true,timeout:20000,args:['--no-sandbox','--disable-gpu','--hide-scrollbars','--disable-dev-shm-usage']});
 console.log('Browser ready.');
 const page=await browser.newPage({viewport:{width:1080,height:2376},deviceScaleFactor:1});
 const errors=[];
 page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(pathToFileURL(path.join(here,'part02-preview.html')).href+'?capture=1',{waitUntil:'load',timeout:20000});
 await page.evaluate(()=>window.animationReady);
 console.log('Animation loaded.');
 for(const [name,t] of keys){
  const info=await page.evaluate(t=>window.renderAt(t),t);
  await page.screenshot({path:path.join(keyDir,name+'.png')});
  console.log(JSON.stringify({keyframe:name,...info}));
 }
 const layout=await page.evaluate(()=>{
  window.renderAt(7.75);
  const viewport=document.querySelector('.cart-window').getBoundingClientRect();
  const rows=[...document.querySelectorAll('.cart-row')].map(e=>e.getBoundingClientRect());
  return {visibleCourses:rows.filter(r=>r.top>=viewport.top&&r.bottom<=viewport.bottom).length,totalCourses:rows.length,requiredCourses:document.querySelectorAll('.cart-row.required').length,electiveCourses:document.querySelectorAll('.cart-row.elective').length,scrollTransform:getComputedStyle(document.getElementById('cart-items')).transform,removedClaim:!document.body.innerText.includes('40学分')};
 });
 console.log(JSON.stringify({cartLayout:layout}));
 if(layout.visibleCourses!==expectedCount||layout.requiredCourses!==requiredCount||layout.electiveCourses!==expectedCount-requiredCount||layout.scrollTransform!=='none'||!layout.removedClaim)throw new Error('Cart layout/content verification failed');
 const initial=await page.evaluate(()=>window.renderAt(0));
 if(initial.count!==0)throw new Error('The initial cart must be empty');
 const final=await page.evaluate(()=>window.renderAt(7.75));
 if(final.count!==expectedCount||final.credits!==expectedCredits||final.sleep!==expectedSleep)throw new Error('Course totals do not match the order');
 const content=await page.evaluate(()=>({totals:[...document.querySelectorAll('.course-count')].map(e=>Number(e.textContent)),credits:[...document.querySelectorAll('.credit-total')].map(e=>Number(e.textContent)),clipped:[...document.querySelectorAll('.cart-course-title,.course-card .course-name')].filter(e=>e.scrollWidth>e.clientWidth).map(e=>e.textContent),placeholders:document.getElementById('stage').innerText.match(/【X】|\bundefined\b|\bNaN\b|\bnull\b|[Xx]学分/g)||[]}));
 console.log(JSON.stringify({orderContent:content}));
 if(content.totals.some(n=>n!==expectedCount)||content.credits.some(n=>n!==expectedCredits)||content.clipped.length||content.placeholders.length)throw new Error('Visible order content verification failed');
 const payment=await page.evaluate(()=>{
  const before=window.renderAt(14.30),during=window.renderAt(15.20),after=window.renderAt(15.80);
  const deferred=document.getElementById('deferred-cost'),future=document.getElementById('deferred-amount'),button=document.getElementById('confirm-button');
  const futureRect=deferred.getBoundingClientRect(),buttonRect=button.getBoundingClientRect();
  const deferredText=deferred.innerText.replace(/\s+/g,'');
  const lowerCostVisible=getComputedStyle(deferred).opacity==='1'&&getComputedStyle(future).opacity==='1'&&futureRect.bottom<buttonRect.top;
  window.renderAt(0);const cta=document.getElementById('add-required');
  return {before:before.payNow,during:during.payNow,after:after.payNow,deferred:after.deferredHours,deferredText,lowerCostVisible,ctaWidth:cta.offsetWidth,ctaHeight:cta.offsetHeight};
 });
 console.log(JSON.stringify({paymentAndCTA:payment}));
 if(payment.before!==expectedSleep||payment.during<=0||payment.during>=expectedSleep||payment.after!==0||payment.deferred!==expectedSleep||payment.deferredText!==`签收后消耗${expectedSleep}小时`||!payment.lowerCostVisible||payment.ctaWidth<220||payment.ctaHeight<52)throw new Error('Payment transfer or primary CTA verification failed');
 if(errors.length)throw new Error(errors.join('\n'));
 if(mode==='stills'){await browser.close();return;}
 const output=path.join(here,'renders','part02-'+config.version+'.mp4');
 const log=fs.openSync(path.join(here,'renders','encode.log'),'w');
 const cmd=['-y','-hide_banner','-loglevel','warning','-f','image2pipe','-vcodec','mjpeg','-framerate',String(config.fps),'-i','pipe:0','-i',path.join(here,'renders','operations.wav'),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-t',String(config.duration),'-movflags','+faststart',output];
 const encoder=spawn(ffmpegPath,cmd,{stdio:['pipe','ignore',log],windowsHide:true});
 const exited=once(encoder,'exit');
 encoder.stdin.on('error',e=>console.error('Encoder input:',e.message));
 for(let i=0;i<config.fps*config.duration;i++){
  await page.evaluate(t=>window.renderAt(t),i/config.fps);
  const frame=await page.screenshot({type:'jpeg',quality:95});
  if(!encoder.stdin.write(frame))await once(encoder.stdin,'drain');
  if(i%90===0)console.log(JSON.stringify({frame:i,total:config.fps*config.duration,elapsed:Math.round((Date.now()-started)/100)/10}));
 }
 encoder.stdin.end();
 const [code]=await exited;
 fs.closeSync(log);
 await browser.close();
 if(code)throw new Error('FFmpeg failed with exit code '+code);
 const info={version:config.version,duration:config.duration,fps:config.fps,width:1080,height:2376,size:fs.statSync(output).size,pageErrors:errors,renderSeconds:Math.round((Date.now()-started)/100)/10};
 fs.writeFileSync(path.join(here,'renders','render-info.json'),JSON.stringify(info,null,2));
 console.log(JSON.stringify(info));
})().catch(e=>{console.error(e);process.exit(1)});
