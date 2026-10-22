import {spawn} from 'node:child_process';

// Stream frames rather than keeping a full portrait clip in memory.
export class PresenterVideo {
  constructor({file,ffmpeg,fps,createCanvas,ImageData}) {
    Object.assign(this,{file,ffmpeg,fps,ImageData});
    this.canvas=createCanvas(720,1280);this.ctx=this.canvas.getContext('2d');
    this.index=-1;this.proc=null;this.iterator=null;
  }
  async *decode(proc) {
    const bytes=720*1280*4;let pending=Buffer.alloc(0);
    for await(const chunk of proc.stdout) {
      pending=Buffer.concat([pending,chunk]);
      while(pending.length>=bytes) {
        yield pending.subarray(0,bytes);pending=pending.subarray(bytes);
      }
    }
    if(proc.exitCode!==null&&proc.exitCode!==0)throw Error('Presenter video decoding failed: '+this.stderr);
  }
  restart() {
    this.close();this.index=-1;this.stderr='';
    this.proc=spawn(this.ffmpeg,['-v','error','-i',this.file,'-an','-vf',`scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,fps=${this.fps}`,'-pix_fmt','rgba','-f','rawvideo','pipe:1'],{stdio:['ignore','pipe','pipe'],windowsHide:true});
    this.proc.stderr.on('data',b=>this.stderr=(this.stderr+b).slice(-2000));
    this.iterator=this.decode(this.proc)[Symbol.asyncIterator]();
  }
  async frame(seconds) {
    const target=Math.max(0,Math.floor(seconds*this.fps+1e-6));
    if(!this.iterator||target<this.index)this.restart();
    while(this.index<target) {
      const next=await this.iterator.next();
      if(next.done){if(this.index<0)throw Error('Presenter video contains no frames');break;}
      const rgba=new Uint8ClampedArray(next.value.buffer,next.value.byteOffset,next.value.byteLength);
      this.ctx.putImageData(new this.ImageData(rgba,720,1280),0,0);this.index++;
    }
    return this.canvas;
  }
  close(){if(this.proc){this.proc.stdout.destroy();this.proc.kill();this.proc=null;}this.iterator=null;}
}
