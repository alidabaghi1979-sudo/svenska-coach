"""
پخش‌کننده‌ی «دست‌آزاد»: چند فایل صوتی رو پشت‌سر هم (با تکرار و مکث) خودکار پخش می‌کنه.
فقط یک بار دکمه‌ی ▶️ رو لمس می‌کنی؛ بعدش خودش ادامه می‌ده (برای وقتی که دستت درگیره).
"""
import base64
import html
import json

import streamlit.components.v1 as components

MAX_TOTAL_MB = 18  # سقف حجم کل صدا داخل صفحه


def total_mb(tracks):
    return sum(len(b) for _, b in tracks) / 1_000_000


def player(tracks, repeat=1, gap=4, loop=True, height=330):
    """tracks: لیست (برچسب, bytes mp3). repeat: هر ترک چند بار؛ gap: ثانیه مکث؛ loop: تکرار کل لیست."""
    data = [{"label": str(lbl), "b64": base64.b64encode(raw).decode("ascii")} for lbl, raw in tracks if raw]
    if not data:
        return
    page = _TEMPLATE.replace("__TRACKS__", json.dumps(data)).replace(
        "__REPEAT__", str(int(repeat))).replace("__GAP__", str(float(gap))).replace(
        "__LOOP__", "true" if loop else "false")
    components.html(page, height=height)


_TEMPLATE = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
 body{margin:0;font-family:system-ui,sans-serif;background:#F7FBFE;color:#14293D;text-align:center}
 #label{font-size:18px;margin:14px 8px 4px;min-height:48px;direction:auto}
 #status{font-size:14px;color:#5b6b7a;margin-bottom:10px;min-height:20px}
 #play{width:140px;height:140px;border-radius:50%;border:5px solid #FECC02;background:#006AA7;color:#fff;font-size:56px;box-shadow:0 4px 12px rgba(0,106,167,.35)}
 .row{display:flex;justify-content:center;gap:14px;align-items:center;margin-top:14px}
 .sm{width:64px;height:64px;border-radius:50%;border:1.5px solid #006AA7;background:#fff;color:#006AA7;font-size:26px}
 select{background:#fff;color:#14293D;border:1.5px solid #006AA7;border-radius:8px;padding:8px;font-size:15px}
</style></head><body>
<div id="label">آماده</div><div id="status"></div>
<button id="play">▶</button>
<div class="row">
 <button class="sm" id="prev">⏮</button>
 <select id="speed"><option value="0.8">0.8×</option><option value="0.9">0.9×</option>
  <option value="1" selected>1×</option><option value="1.2">1.2×</option></select>
 <button class="sm" id="next">⏭</button>
</div>
<audio id="a"></audio>
<script>
const TRACKS=__TRACKS__, REPEAT=__REPEAT__, GAP=__GAP__*1000, LOOP=__LOOP__;
const a=document.getElementById('a'), play=document.getElementById('play');
const label=document.getElementById('label'), status=document.getElementById('status');
let idx=0, rep=0, playing=false, timer=null, wake=null, urls={};
function url(i){
  if(!urls[i]){
    const bin=atob(TRACKS[i].b64), u8=new Uint8Array(bin.length);
    for(let k=0;k<bin.length;k++)u8[k]=bin.charCodeAt(k);
    urls[i]=URL.createObjectURL(new Blob([u8],{type:'audio/mpeg'}));
  }
  return urls[i];
}
function show(){
  label.textContent=TRACKS[idx].label;
  status.textContent=(idx+1)+' / '+TRACKS.length+(REPEAT>1?'  ·  تکرار '+(rep+1)+' از '+REPEAT:'');
  if('mediaSession' in navigator){navigator.mediaSession.metadata=new MediaMetadata({title:TRACKS[idx].label,artist:'Svenska Coach'});}
}
function start(){
  clearTimeout(timer); a.src=url(idx); a.playbackRate=parseFloat(document.getElementById('speed').value);
  show(); a.play().catch(()=>{status.textContent='برای شروع ▶ رو بزن';playing=false;play.textContent='▶';});
}
async function keepAwake(){try{if('wakeLock' in navigator){wake=await navigator.wakeLock.request('screen');}}catch(e){}}
function toggle(){
  if(playing){playing=false;a.pause();clearTimeout(timer);play.textContent='▶';if(wake){wake.release();wake=null;}}
  else{playing=true;play.textContent='⏸';keepAwake();start();}
}
function advance(){
  rep++;
  if(rep>=REPEAT){rep=0;idx++;
    if(idx>=TRACKS.length){if(LOOP){idx=0;}else{playing=false;play.textContent='▶';status.textContent='تموم شد';return;}}}
  status.textContent='...';
  timer=setTimeout(()=>{if(playing)start();},GAP);
}
a.addEventListener('ended',()=>{if(playing)advance();});
play.onclick=toggle;
document.getElementById('next').onclick=()=>{rep=0;idx=(idx+1)%TRACKS.length;if(playing)start();else show();};
document.getElementById('prev').onclick=()=>{rep=0;idx=(idx-1+TRACKS.length)%TRACKS.length;if(playing)start();else show();};
document.getElementById('speed').onchange=e=>{a.playbackRate=parseFloat(e.target.value);};
if('mediaSession' in navigator){
  navigator.mediaSession.setActionHandler('play',toggle);navigator.mediaSession.setActionHandler('pause',toggle);
  navigator.mediaSession.setActionHandler('nexttrack',()=>document.getElementById('next').click());
  navigator.mediaSession.setActionHandler('previoustrack',()=>document.getElementById('prev').click());
}
show();
</script></body></html>"""
