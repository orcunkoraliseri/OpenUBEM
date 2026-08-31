"""Generate the four European district 3D viewers and their data folders (EU-11B + EU-12 + EU-13).

Binds:
- EU-11 Speed campaign simulation results (heating EUI)
- EU-13 Multi-storey dwelling layouts, general partition, imputation provenance, and interactive storey selector in pop-ups.

Outputs written to `openubem/outputs/3D/` and mirrored to
`docs/docs_ACTIVE/europeanLocations/outputs_3D/`.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

REPO_ROOT = Path("C:/Users/o_iseri/Desktop/OpenUBEM")

# HTML template parts
HTML_HEADER_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{page_title}</title>
<style>
*{{box-sizing:border-box}}
html,body{{margin:0;height:100%;background:#0e1116;color:#e6e9ef;
  font:13px/1.45 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif;overflow:hidden}}
canvas#c{{display:block;cursor:grab}}
canvas#c.drag{{cursor:grabbing}}
#hud{{position:fixed;top:14px;left:14px;max-width:330px;background:rgba(16,20,27,.86);
  border:1px solid #262d3a;border-radius:10px;padding:12px 14px;backdrop-filter:blur(6px);z-index:10}}
#hud h1{{margin:0 0 2px;font-size:15px;letter-spacing:.2px}}
#hud .sub{{color:#8b95a7;font-size:11.5px;margin-bottom:9px}}
.warn{{background:#3a2410;border:1px solid #7a4b12;color:#f0c07a;border-radius:7px;
  padding:7px 9px;font-size:11.5px;margin-bottom:10px}}
.row{{display:flex;justify-content:space-between;gap:10px;font-size:11.5px;padding:1.5px 0}}
.row span:last-child{{color:#cfd6e2;font-variant-numeric:tabular-nums}}
.k{{color:#8b95a7}}
hr{{border:0;border-top:1px solid #232a36;margin:9px 0}}
.btns{{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px}}
button{{background:#1a212c;color:#c8d1de;border:1px solid #2d3646;border-radius:6px;
  padding:4px 8px;font:inherit;font-size:11.5px;cursor:pointer}}
button:hover{{background:#222b38}}
button.on{{background:#1d3a55;border-color:#2f6b9c;color:#bfe0fb}}
#legend{{position:fixed;bottom:14px;left:14px;background:rgba(16,20,27,.86);
  border:1px solid #262d3a;border-radius:10px;padding:10px 12px;z-index:10}}
#legend .t{{font-size:11px;color:#8b95a7;margin-bottom:6px}}
#bar{{width:190px;height:9px;border-radius:3px;margin-bottom:4px}}
.lab{{display:flex;justify-content:space-between;font-size:10.5px;color:#8b95a7}}
.keys{{display:flex;flex-direction:column;gap:3px;font-size:11px}}
.keys div{{display:flex;align-items:center;gap:6px}}
.sw{{width:11px;height:11px;border-radius:2px;border:1px solid #0006}}
#hud a{{color:#7fb3e0;text-decoration:none}}#hud a:hover{{text-decoration:underline}}
#flt{{margin-top:9px;border-top:1px solid #232a36;padding-top:9px}}
#flt .ft{{font-size:11px;color:#8b95a7;display:flex;justify-content:space-between;margin-bottom:5px}}
#flt.off{{opacity:.55}}
#flt input[type=range]{{width:100%;accent-color:#2f6b9c;margin:1px 0}}
#flt .rd{{font-size:11px;color:#cfd6e2;font-variant-numeric:tabular-nums;
  display:flex;justify-content:space-between;margin-top:3px}}
.unbound{{background:#2a1c22;border:1px solid #6b3a48;color:#e79aad;border-radius:6px;
  padding:6px 8px;font-size:11px;margin-top:6px}}
button:disabled{{opacity:.42;cursor:not-allowed}}
#tip{{position:fixed;pointer-events:none;display:none;background:rgba(10,13,18,.95);
  border:1px solid #2d3646;border-radius:7px;padding:7px 9px;font-size:11.5px;max-width:270px;z-index:20}}
#tip b{{color:#8fd0ff}}
#help{{position:fixed;bottom:14px;right:14px;color:#5f6a7c;font-size:11px;text-align:right;z-index:10}}

/* Modal popup styles */
#modal-backdrop{{position:fixed;inset:0;background:rgba(0,0,0,0.65);backdrop-filter:blur(4px);
  display:none;align-items:center;justify-content:center;z-index:100}}
#modal{{background:#12161f;border:1px solid #2d3646;border-radius:12px;width:90%;max-width:640px;
  max-height:90vh;overflow-y:auto;padding:18px 22px;box-shadow:0 20px 40px rgba(0,0,0,0.6);position:relative}}
#modal-close{{position:absolute;top:14px;right:16px;background:transparent;border:0;color:#8b95a7;
  font-size:20px;line-height:1;cursor:pointer;padding:4px 8px;border-radius:4px}}
#modal-close:hover{{color:#fff;background:#1e2634}}
#m-title{{margin:0 0 4px;font-size:16px;color:#8fd0ff}}
#m-sub{{color:#8b95a7;font-size:12px;margin-bottom:12px;line-height:1.4}}
.m-badge{{display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;margin-right:6px;font-weight:600}}
.m-badge.emitted{{background:#173d2a;color:#7ee787;border:1px solid #238636}}
.m-badge.imputed{{background:#0d3349;color:#58a6ff;border:1px solid #1f6feb}}
.m-badge.fallback{{background:#3a2410;color:#f0c07a;border:1px solid #7a4b12}}
.m-badge.unsim{{background:#22272e;color:#8b95a7;border:1px solid #373e47}}
.m-info-box{{background:#161b24;border:1px solid #262d3a;border-radius:8px;padding:10px 12px;font-size:12px;margin-bottom:14px}}
.m-info-box p{{margin:3px 0}}
.m-info-box code{{background:#0d1117;padding:1px 5px;border-radius:3px;font-size:11px;color:#e6e9ef}}
.storey-bar{{display:flex;align-items:center;gap:6px;margin-bottom:10px;font-size:12px;flex-wrap:wrap}}
.storey-btn{{background:#1a212c;border:1px solid #2d3646;color:#c8d1de;border-radius:4px;padding:2px 7px;font-size:11px;cursor:pointer}}
.storey-btn.active{{background:#1f6feb;border-color:#388bfd;color:#fff;font-weight:bold}}
#fp-container{{background:#0a0d13;border:1px solid #212835;border-radius:8px;padding:10px;display:flex;flex-direction:column;align-items:center;margin-bottom:12px}}
#fp-canvas{{display:block;background:#090c10;border-radius:6px}}
#m-zones{{font-size:11.5px;color:#8b95a7;margin-top:6px;width:100%}}
#m-zones table{{width:100%;border-collapse:collapse;margin-top:6px}}
#m-zones th,#m-zones td{{padding:3px 6px;text-align:left;border-bottom:1px solid #1e2531}}
#m-zones th{{color:#6e7681;font-weight:normal}}
</style>
</head>
<body>
<canvas id="c"></canvas>
<div id="hud">
  <h1 id="ttl"></h1>
  <div class="sub" id="place"></div>
  <div class="warn" id="warn"></div>
  <div class="row"><span class="k">Residential</span><span id="nres"></span></div>
  <div class="row"><span class="k">Excluded / non-residential</span><span id="nexc"></span></div>
  <div class="row"><span class="k">Dwelling layout (observed)</span><span id="nemitted_obs"></span></div>
  <div class="row"><span class="k">Dwelling layout (imputed)</span><span id="nemitted_imp"></span></div>
  <div class="row"><span class="k">Massing-box fallback</span><span id="nfallback"></span></div>
  <div class="row"><span class="k">Not simulated</span><span id="nnotsim"></span></div>
  <div class="row"><span class="k">Height measured</span><span id="hm"></span></div>
  <div class="row"><span class="k">Height from storeys &times;3.0 m</span><span id="hl"></span></div>
  <div class="row"><span class="k">Height assumed 9.0 m</span><span id="ha"></span></div>
  <hr>
  <div class="row"><span class="k">CRS</span><span id="crs"></span></div>
  <div class="row"><span class="k">Extent</span><span id="span"></span></div>
  <div class="row"><span class="k">Source</span><span id="layer" style="text-align:right"></span></div>
  <div class="row"><span class="k">Licence</span><span id="lic" style="text-align:right"></span></div>
  <div class="row"><span class="k">Data folder</span><span id="dataf" style="text-align:right"></span></div>
  <div class="btns">
    <button id="bH" class="on">colour: height</button>
    <button id="bP">colour: provenance</button>
    <button id="bY">colour: age</button>
    <button id="bU">colour: EUI</button>
    <button id="bE" class="on">show excluded</button>
    <button id="bR">reset view</button>
  </div>
  <div id="flt">
    <div class="ft"><span>EUI filter (kWh/m&sup2;)</span><span id="fcount"></span></div>
    <input type="range" id="flo" min="0" max="1000" value="0">
    <input type="range" id="fhi" min="0" max="1000" value="1000">
    <div class="rd"><span id="rlo"></span><span id="rhi"></span></div>
    <div class="unbound" id="fnote"></div>
  </div>
</div>
<div id="legend"><div class="t" id="lt"></div><div id="lbody"></div></div>
<div id="tip"></div>
<div id="help">click building for floor plan &middot; drag orbit &middot; shift-drag pan &middot; wheel zoom</div>

<div id="modal-backdrop">
  <div id="modal">
    <button id="modal-close" title="Close (Esc)">&times;</button>
    <h2 id="m-title"></h2>
    <div id="m-sub"></div>
    <div class="m-info-box" id="m-status-box"></div>
    <div class="storey-bar" id="m-storey-bar"></div>
    <div id="fp-container">
      <canvas id="fp-canvas" width="560" height="280"></canvas>
      <div id="m-zones"></div>
    </div>
  </div>
</div>

<script type="application/json" id="scene">"""

HTML_FOOTER = """</script>
<script>
(function(){
var D=JSON.parse(document.getElementById("scene").textContent);
var B=D.buildings;
document.getElementById("ttl").textContent=D.name;
document.getElementById("place").textContent=D.place;
document.getElementById("nres").textContent=D.n_res.toLocaleString();
document.getElementById("nexc").textContent=D.n_exc.toLocaleString();
document.getElementById("nemitted_obs").textContent=(D.layout_counts ? D.layout_counts.observed_emitted : 0).toLocaleString();
document.getElementById("nemitted_imp").textContent=(D.layout_counts ? D.layout_counts.imputed_emitted : 0).toLocaleString();
document.getElementById("nfallback").textContent=(D.layout_counts ? D.layout_counts.massing_box : 0).toLocaleString();
document.getElementById("nnotsim").textContent=(D.layout_counts ? D.layout_counts.not_simulated : D.n_res).toLocaleString();
document.getElementById("hm").textContent=D.counts.measured.toLocaleString();
document.getElementById("hl").textContent=D.counts.levels.toLocaleString();
document.getElementById("ha").textContent=D.counts.assumed.toLocaleString();
document.getElementById("crs").textContent=D.crs;
document.getElementById("span").textContent=Math.round(D.span)+" m";
document.getElementById("layer").textContent=D.layer;
document.getElementById("lic").textContent=D.licence;
document.getElementById("dataf").innerHTML='<a href="'+D.data_dir+'/index.html" target="_blank">'+D.data_dir+'/</a>';

var hmax=1;for(var i=0;i<B.length;i++)if(B[i].h>hmax)hmax=B[i].h;
hmax=Math.min(hmax,60);
var years=B.filter(function(b){return b.y}).map(function(b){return b.y});
var ymin=years.length?Math.min.apply(null,years):1900,ymax=years.length?Math.max.apply(null,years):2020;

var RAMP=[[68,1,84],[59,82,139],[33,145,140],[94,201,98],[253,231,37]];
function ramp(t){t=Math.max(0,Math.min(1,t));var s=t*(RAMP.length-1),i=Math.floor(s),f=s-i;
  if(i>=RAMP.length-1){i=RAMP.length-2;f=1;}
  var a=RAMP[i],b=RAMP[i+1];
  return [a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f,a[2]+(b[2]-a[2])*f];}
var PROV=[[86,180,233],[240,180,60],[200,90,110]];
function baseColor(b){
  if(b.c===1)return [96,104,118];
  if(mode==="p")return PROV[b.p];
  if(mode==="y"){if(!b.y)return [80,88,100];return ramp((b.y-ymin)/Math.max(1,ymax-ymin));}
  if(mode==="e"){if(typeof b.e!=="number")return [80,88,100];return ramp((b.e-emin)/(emax-emin));}
  return ramp(b.h/hmax);
}
var mode="h";
var euiBound=!!D.eui_bound;
var evals=euiBound?B.filter(function(b){return b.c===0&&typeof b.e==="number";}).map(function(b){return b.e;}):[];
var emin=evals.length?Math.min.apply(null,evals):0;
var emax=evals.length?Math.max.apply(null,evals):1;
if(emax<=emin)emax=emin+1;
var flo=emin,fhi=emax,fltOn=false;

var cv=document.getElementById("c"),ctx=cv.getContext("2d"),W=0,H=0,dpr=1;
function resize(){dpr=Math.min(window.devicePixelRatio||1,2);
  W=window.innerWidth;H=window.innerHeight;
  cv.width=W*dpr;cv.height=H*dpr;cv.style.width=W+"px";cv.style.height=H+"px";
  ctx.setTransform(dpr,0,0,dpr,0,0);draw();}
window.addEventListener("resize",resize);

var yaw=0.6,pitch=0.95,zoom=1,px=0,py=0,showExc=true;
function fit(){zoom=Math.min(W,H)*0.78/Math.max(D.span,40);px=0;py=0;yaw=0.6;pitch=0.95;}

var cs=1,sn=0,cp=1,sp=0;
function setTrig(){cs=Math.cos(yaw);sn=Math.sin(yaw);cp=Math.cos(pitch);sp=Math.sin(pitch);}
function sx(x,y){return (x*cs-y*sn)*zoom+W/2+px;}
function sy(x,y,z){return ((x*sn+y*cs)*cp-z*sp)*zoom+H/2+py;}
function depth(x,y,z){return (x*sn+y*cs)*sp+z*cp;}

var order=[];
function draw(){
  setTrig();
  ctx.fillStyle="#0e1116";ctx.fillRect(0,0,W,H);
  order.length=0;
  for(var i=0;i<B.length;i++){
    var b=B[i];if(b.c===1&&!showExc)continue;
    if(fltOn&&b.c===0){if(typeof b.e!=="number")continue;if(b.e<flo||b.e>fhi)continue;}
    var r=b.r,n=r.length,mx=0,my=0;
    for(var j=0;j<n;j++){mx+=r[j][0];my+=r[j][1];}
    mx/=n;my/=n;
    order.push([depth(mx,my,0),i]);
  }
  order.sort(function(a,b){return a[0]-b[0];});
  for(var k=0;k<order.length;k++)paint(B[order[k][1]]);
  ctx.strokeStyle="rgba(140,160,190,.13)";ctx.lineWidth=1;
  var g=Math.max(20,Math.pow(10,Math.round(Math.log(D.span/6)/Math.LN10)));
  var lim=Math.ceil(D.span/g)+1;
  ctx.beginPath();
  for(var t=-lim;t<=lim;t++){
    ctx.moveTo(sx(t*g,-lim*g),sy(t*g,-lim*g,0));ctx.lineTo(sx(t*g,lim*g),sy(t*g,lim*g,0));
    ctx.moveTo(sx(-lim*g,t*g),sy(-lim*g,t*g,0));ctx.lineTo(sx(lim*g,t*g),sy(lim*g,t*g,0));
  }
  ctx.globalCompositeOperation="destination-over";ctx.stroke();
  ctx.globalCompositeOperation="source-over";
}

function paint(b){
  var r=b.r,n=r.length,c=baseColor(b),h=b.h;
  var a2=0;
  for(var j0=0;j0<n;j0++){var q=r[j0],w2=r[(j0+1)%n];a2+=q[0]*w2[1]-w2[0]*q[1];}
  var wind=a2>=0?1:-1;
  var walls=[];
  for(var j=0;j<n;j++){
    var a=r[j],e=r[(j+1)%n];
    var dx=e[0]-a[0],dy=e[1]-a[1];
    var nx=dy*wind,ny=-dx*wind,ln=Math.hypot(nx,ny)||1;nx/=ln;ny/=ln;
    var facing=(nx*sn+ny*cs);
    if(facing<=0)continue;
    var md=depth((a[0]+e[0])/2,(a[1]+e[1])/2,h/2);
    var lit=0.42+0.34*(nx*cs-ny*sn+1)/2+0.16*facing;
    walls.push([md,a,e,lit]);
  }
  walls.sort(function(p,q){return p[0]-q[0];});
  for(var w=0;w<walls.length;w++){
    var a2=walls[w][1],e2=walls[w][2],f=walls[w][3];
    ctx.beginPath();
    ctx.moveTo(sx(a2[0],a2[1]),sy(a2[0],a2[1],0));
    ctx.lineTo(sx(e2[0],e2[1]),sy(e2[0],e2[1],0));
    ctx.lineTo(sx(e2[0],e2[1]),sy(e2[0],e2[1],h));
    ctx.lineTo(sx(a2[0],a2[1]),sy(a2[0],a2[1],h));
    ctx.closePath();
    ctx.fillStyle="rgb("+(c[0]*f|0)+","+(c[1]*f|0)+","+(c[2]*f|0)+")";
    ctx.fill();
  }
  ctx.beginPath();
  for(var j2=0;j2<n;j2++){
    var p=r[j2],X=sx(p[0],p[1]),Y=sy(p[0],p[1],h);
    if(j2===0)ctx.moveTo(X,Y);else ctx.lineTo(X,Y);
  }
  ctx.closePath();
  ctx.fillStyle="rgb("+(c[0]|0)+","+(c[1]|0)+","+(c[2]|0)+")";ctx.fill();
  ctx.strokeStyle="rgba(0,0,0,.35)";ctx.lineWidth=0.7;ctx.stroke();
}

var drag=null,downPos=null;
cv.addEventListener("mousedown",function(e){
  downPos={x:e.clientX,y:e.clientY};
  drag={x:e.clientX,y:e.clientY,s:e.shiftKey||e.button===2};
  cv.classList.add("drag");
});
window.addEventListener("mouseup",function(e){
  if(downPos){
    var dist=Math.hypot(e.clientX-downPos.x, e.clientY-downPos.y);
    if(dist<5){
      var hit=findHit(e.clientX, e.clientY);
      if(hit)openPopup(hit);
    }
  }
  drag=null;downPos=null;cv.classList.remove("drag");
});
window.addEventListener("mousemove",function(e){
  if(drag){
    var dx=e.clientX-drag.x,dy=e.clientY-drag.y;drag.x=e.clientX;drag.y=e.clientY;
    if(drag.s){px+=dx;py+=dy;}
    else{{yaw+=dx*0.006;pitch=Math.max(0.06,Math.min(1.5707,pitch-dy*0.005));}}
    draw();hide();
  } else hover(e);
});
cv.addEventListener("contextmenu",function(e){e.preventDefault();});
cv.addEventListener("wheel",function(e){
  e.preventDefault();
  var f=Math.exp(-e.deltaY*0.0012);
  zoom=Math.max(0.15,Math.min(40,zoom*f));draw();hide();
},{passive:false});

var tip=document.getElementById("tip");
function hide(){tip.style.display="none";}
function inPoly(mx,my,pts){
  var inside=false;
  for(var i=0,j=pts.length-1;i<pts.length;j=i++){
    var a=pts[i],b=pts[j];
    if(((a[1]>my)!==(b[1]>my))&&(mx<(b[0]-a[0])*(my-a[1])/(b[1]-a[1])+a[0]))inside=!inside;
  }
  return inside;
}
function findHit(mx,my){
  for(var k=order.length-1;k>=0;k--){
    var b=B[order[k][1]],r=b.r,pts=[];
    for(var j=0;j<r.length;j++)pts.push([sx(r[j][0],r[j][1]),sy(r[j][0],r[j][1],b.h)]);
    if(inPoly(mx,my,pts))return b;
  }
  return null;
}
function hover(e){
  var b=findHit(e.clientX, e.clientY);
  if(b){
    var prov=["measured","from storeys × 3.0 m","assumed 9.0 m"][b.p];
    tip.innerHTML="<b>"+b.id+"</b><br>"+(b.t||"—")+
      (b.c===1?" <i>(excluded)</i>":"")+
      "<br>height "+b.h.toFixed(1)+" m <i>("+prov+")</i>"+
      (b.l?"<br>storeys "+b.l:"")+(b.y?"<br>built "+b.y:"")+
      "<br>footprint "+b.a.toFixed(0)+" m²"+(typeof b.e==="number"?"<br><b>EUI "+b.e.toFixed(1)+" kWh/m²</b> <i>(heating only)</i>"+(b.g?"<br><i>"+b.g+"</i>":""):(euiBound&&b.c===0?"<br><i>not simulated</i>":""))+
      "<br><span style='color:#7fb3e0;font-size:10.5px;'>click for floor plan &rarr;</span>";
    tip.style.display="block";
    tip.style.left=Math.min(e.clientX+14,window.innerWidth-282)+"px";
    tip.style.top=(e.clientY+14)+"px";
    return;
  }
  hide();
}

/* Floor Plan Modal Logic */
var modalBackdrop=document.getElementById("modal-backdrop"),
    modalClose=document.getElementById("modal-close"),
    mTitle=document.getElementById("m-title"),
    mSub=document.getElementById("m-sub"),
    mStatusBox=document.getElementById("m-status-box"),
    mStoreyBar=document.getElementById("m-storey-bar"),
    mZones=document.getElementById("m-zones"),
    fpCanvas=document.getElementById("fp-canvas"),
    fpCtx=fpCanvas.getContext("2d");

var currentModalBuilding=null;
var currentStoreyIndex=0;

function closePopup(){modalBackdrop.style.display="none";cv.focus();}
modalClose.onclick=closePopup;
modalBackdrop.onclick=function(e){if(e.target===modalBackdrop)closePopup();};
window.addEventListener("keydown",function(e){if(e.key==="Escape")closePopup();});

var ZONE_COLORS=[
  "rgba(56,189,248,0.55)", "rgba(74,222,128,0.55)", "rgba(251,191,36,0.55)",
  "rgba(248,113,113,0.55)", "rgba(168,85,247,0.55)", "rgba(236,72,153,0.55)",
  "rgba(45,212,191,0.55)", "rgba(251,146,60,0.55)", "rgba(129,140,248,0.55)"
];

function openPopup(b){
  hide();
  currentModalBuilding=b;
  currentStoreyIndex=0;
  var prov=["measured (source)","from storeys × 3.0 m","assumed 9.0 m"][b.p];
  mTitle.textContent=b.id + (b.t ? " — " + b.t : "");
  
  var k=b.k; // layout side-car summary
  var arch=k && k.archetype ? k.archetype : "—";
  var btype=k && k.btype ? k.btype : (b.c===1 ? "Excluded" : "Residential");
  var storeys=b.l || (k && k.storeys ? k.storeys : "—");
  var dwellings=k && k.dwellings ? k.dwellings : (b.l ? "—" : "—");
  var upf=k && k.upf ? k.upf : "—";
  var core=k && k.core !== null && k.core !== undefined ? (k.core ? "Yes" : "No") : "—";
  var euiStr=(typeof b.e==="number") ? (b.e.toFixed(1) + " kWh/m² (heating only)") : (b.c===1 ? "n/a (excluded)" : "not simulated");
  var areaStr=(k && typeof k.cond==="number" && typeof k.gross==="number")
    ? (k.cond.toFixed(0) + " m² conditioned / " + k.gross.toFixed(0) + " m² gross")
    : (b.a.toFixed(0) + " m²");

  mSub.innerHTML="<b>Archetype:</b> " + arch + " (" + btype + ") &middot; " +
    "<b>Storeys:</b> " + storeys + " &middot; " +
    "<b>Dwellings:</b> " + dwellings + " (" + upf + "/floor) &middot; " +
    "<b>Unconditioned core:</b> " + core + "<br>" +
    "<b>Height:</b> " + b.h.toFixed(1) + " m <i>(" + prov + ")</i> &middot; " +
    "<b>Footprint:</b> " + areaStr + " &middot; " +
    "<b>EUI:</b> " + euiStr;

  var statusHtml="";
  if(k && k.outcome==="DWELLING_LAYOUT_EMITTED"){
    statusHtml="<span class='m-badge emitted'>DWELLING LAYOUT EMITTED (OBSERVED COUNT)</span> " +
      "<b>Scheme:</b> " + (k.scheme || "equal-strip partition") + ".<br>" +
      "<p style='color:#8b95a7;font-size:11.5px;margin-top:4px;'>Emitted general multi-angle/radial partition. " +
      "Extruded across all " + storeys + " storeys (" + (k.floors ? k.floors.length : 1) + " floors generated in simulation pipeline).</p>";
  } else if(k && k.outcome==="DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT"){
    var dprov=k.dprov || "IMPUTED_TIER4_STATISTICAL_TABULA";
    statusHtml="<span class='m-badge imputed'>DWELLING LAYOUT EMITTED (IMPUTED COUNT)</span> " +
      "<b>Provenance:</b> <code>" + dprov + "</code>.<br>" +
      "<p style='color:#8b95a7;font-size:11.5px;margin-top:4px;'>Emitted general partition using four-tier imputed dwelling count. " +
      "Extruded across all " + storeys + " storeys (" + (k.floors ? k.floors.length : 1) + " floors generated in simulation pipeline).</p>";
  } else if(k && (k.outcome==="FALLBACK_PENDING_LAYOUT" || k.outcome==="FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT")){
    var reason=k.reason || "MISSING_OBSERVED_DWELLING_COUNT";
    statusHtml="<span class='m-badge fallback'>MASSING BOX FALLBACK</span> " +
      "No dwelling layout emitted &mdash; one zone per floor (massing box). Reason: <code>" + reason + "</code>. <code>FINDING EU-S2-01</code>.<br>" +
      "<p style='color:#8b95a7;font-size:11.5px;margin-top:4px;'>Showing footprint outline only. No interior partition was generated.</p>";
  } else {
    statusHtml="<span class='m-badge unsim'>NOT SIMULATED</span> " +
      (b.c===1 ? "Excluded / non-residential building." : "Not simulated in EU-11 campaign. No dwelling layout generated.") +
      "<p style='color:#8b95a7;font-size:11.5px;margin-top:4px;'>Showing footprint outline only.</p>";
  }
  if(k && k.cprov){
    statusHtml += "<span class='m-badge imputed'>CONSTRUCTION PERIOD IMPUTED</span> <code>" + k.cprov + "</code><br>";
  }
  mStatusBox.innerHTML=statusHtml;

  // Build Storey Selector
  var numFloors=(k && k.floors) ? k.floors.length : (b.l || 1);
  if(k && (k.outcome==="DWELLING_LAYOUT_EMITTED" || k.outcome==="DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT") && numFloors > 1){
    var sHtml="<span style='color:#8b95a7;margin-right:4px;'>Storey:</span> ";
    for(var s=0; s<numFloors; s++){
      var zLo=(s*3.0).toFixed(0), zHi=((s+1)*3.0).toFixed(0);
      sHtml += "<button class='storey-btn" + (s===0 ? " active" : "") + "' onclick='selectStorey(" + s + ")'>F" + s + " (" + zLo + "–" + zHi + "m)</button> ";
    }
    mStoreyBar.innerHTML=sHtml;
    mStoreyBar.style.display="flex";
  } else if(numFloors > 1) {
    mStoreyBar.innerHTML="<span style='color:#8b95a7;'>Massing box &middot; " + numFloors + " stacked floors (one zone per floor)</span>";
    mStoreyBar.style.display="flex";
  } else {
    mStoreyBar.innerHTML="<span style='color:#8b95a7;'>Single storey (0.0 to 3.0 m)</span>";
    mStoreyBar.style.display="flex";
  }

  drawFloorPlan(b, 0);
  modalBackdrop.style.display="flex";
}

window.selectStorey=function(sIdx){
  currentStoreyIndex=sIdx;
  var btns=mStoreyBar.getElementsByClassName("storey-btn");
  for(var i=0; i<btns.length; i++){
    btns[i].classList.toggle("active", i===sIdx);
  }
  if(currentModalBuilding){
    drawFloorPlan(currentModalBuilding, sIdx);
  }
};

function drawFloorPlan(b, sIdx){
  var cw=fpCanvas.width, ch=fpCanvas.height;
  fpCtx.clearRect(0,0,cw,ch);
  
  var r=b.r;
  var minx=1e9,miny=1e9,maxx=-1e9,maxy=-1e9;
  for(var i=0;i<r.length;i++){
    if(r[i][0]<minx)minx=r[i][0];if(r[i][0]>maxx)maxx=r[i][0];
    if(r[i][1]<miny)miny=r[i][1];if(r[i][1]>maxy)maxy=r[i][1];
  }
  var bw=maxx-minx, bh=maxy-miny;
  var bcx=(minx+maxx)/2, bcy=(miny+maxy)/2;
  var pad=40;
  var sc=Math.min((cw-pad*2)/Math.max(bw,5), (ch-pad*2)/Math.max(bh,5));

  function fx(x){return (x-bcx)*sc + cw/2;}
  function fy(y){return -(y-bcy)*sc + ch/2;} // North is up

  // Draw building footprint outline
  fpCtx.beginPath();
  for(var j=0;j<r.length;j++){
    var X=fx(r[j][0]), Y=fy(r[j][1]);
    if(j===0)fpCtx.moveTo(X,Y);else fpCtx.lineTo(X,Y);
  }
  fpCtx.closePath();
  fpCtx.fillStyle="rgba(255,255,255,0.04)";
  fpCtx.fill();
  fpCtx.strokeStyle="#8b95a7";
  fpCtx.lineWidth=2;
  fpCtx.stroke();

  var k=b.k;
  var zonesTable="";
  var isEmitted = k && (k.outcome==="DWELLING_LAYOUT_EMITTED" || k.outcome==="DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT");
  var floorData = (isEmitted && k.floors && k.floors[sIdx]) ? k.floors[sIdx] : (k && k.floors ? k.floors[0] : null);

  var circHtml = "";
  if(floorData && floorData.circulation && floorData.circulation.r){
    var cr = floorData.circulation.r;
    fpCtx.beginPath();
    for(var ci=0;ci<cr.length;ci++){
      var CX=fx(cr[ci][0]), CY=fy(cr[ci][1]);
      if(ci===0)fpCtx.moveTo(CX,CY);else fpCtx.lineTo(CX,CY);
    }
    fpCtx.closePath();
    fpCtx.fillStyle="rgba(140,140,140,0.55)";
    fpCtx.fill();
    fpCtx.setLineDash([4,3]);
    fpCtx.strokeStyle="#ffffff";
    fpCtx.lineWidth=1.2;
    fpCtx.stroke();
    fpCtx.setLineDash([]);
    var ccx=0, ccy=0;
    for(var cj=0;cj<cr.length;cj++){ ccx += fx(cr[cj][0]); ccy += fy(cr[cj][1]); }
    ccx /= cr.length; ccy /= cr.length;
    fpCtx.fillStyle="#ffffff";
    fpCtx.font="bold 11px sans-serif";
    fpCtx.textAlign="center";
    fpCtx.textBaseline="middle";
    fpCtx.fillText("C", ccx, ccy);
    circHtml = "<tr><td>Circulation</td>" +
      "<td><span style='display:inline-block;width:12px;height:12px;background:rgba(140,140,140,0.55);border:1px dashed #fff;border-radius:2px;vertical-align:middle;'></span></td>" +
      "<td>&mdash;</td><td>&mdash;</td></tr>";
  }

  if(isEmitted && floorData && floorData.zones && floorData.zones.length > 0){
    zonesTable="<table><thead><tr><th>Zone Name</th><th>Colour</th><th>Dwelling Index</th><th>Storey Elevation</th></tr></thead><tbody>";
    for(var z=0;z<floorData.zones.length;z++){
      var zn=floorData.zones[z], zr=zn.r, zc=ZONE_COLORS[z % ZONE_COLORS.length];
      fpCtx.beginPath();
      var zcx=0, zcy=0;
      for(var v=0;v<zr.length;v++){
        var ZX=fx(zr[v][0]), ZY=fy(zr[v][1]);
        if(v===0)fpCtx.moveTo(ZX,ZY);else fpCtx.lineTo(ZX,ZY);
        zcx += ZX; zcy += ZY;
      }
      fpCtx.closePath();
      fpCtx.fillStyle=zc;
      fpCtx.fill();
      fpCtx.strokeStyle="rgba(255,255,255,0.8)";
      fpCtx.lineWidth=1.2;
      fpCtx.stroke();

      zcx /= zr.length; zcy /= zr.length;
      fpCtx.fillStyle="#ffffff";
      fpCtx.font="bold 11px sans-serif";
      fpCtx.textAlign="center";
      fpCtx.textBaseline="middle";
      fpCtx.fillText("D" + (z+1), zcx, zcy);

      var zElev = (zn.z_floor !== undefined ? (zn.z_floor + "–" + zn.z_ceiling + " m") : ("F" + sIdx));
      zonesTable += "<tr><td><code>" + zn.name + "</code></td>" +
        "<td><span style='display:inline-block;width:12px;height:12px;background:" + zc + ";border:1px solid #fff;border-radius:2px;vertical-align:middle;'></span></td>" +
        "<td>Dwelling " + (z+1) + "</td>" +
        "<td>" + zElev + "</td></tr>";
    }
    zonesTable += circHtml + "</tbody></table>";
  } else if(circHtml){
    zonesTable = "<table><thead><tr><th>Zone Name</th><th>Colour</th><th>Dwelling Index</th><th>Storey Elevation</th></tr></thead><tbody>" + circHtml + "</tbody></table>";
  }
  mZones.innerHTML=zonesTable;

  // Draw Scale Bar (metric)
  var barMeters=10;
  if(sc > 15) barMeters=5;
  if(sc > 35) barMeters=2;
  if(sc < 5) barMeters=20;
  if(sc < 2) barMeters=50;
  var barPx=barMeters * sc;
  var bx0=20, by0=ch-18;
  fpCtx.beginPath();
  fpCtx.moveTo(bx0, by0-4); fpCtx.lineTo(bx0, by0); fpCtx.lineTo(bx0+barPx, by0); fpCtx.lineTo(bx0+barPx, by0-4);
  fpCtx.strokeStyle="#c9d1d9";
  fpCtx.lineWidth=1.5;
  fpCtx.stroke();
  fpCtx.fillStyle="#8b95a7";
  fpCtx.font="10px sans-serif";
  fpCtx.textAlign="left";
  fpCtx.textBaseline="bottom";
  fpCtx.fillText(barMeters + " m", bx0, by0-6);

  // Draw North Arrow
  var nx0=cw-24, ny0=24;
  fpCtx.beginPath();
  fpCtx.moveTo(nx0, ny0-10); fpCtx.lineTo(nx0-5, ny0+6); fpCtx.lineTo(nx0, ny0+2); fpCtx.lineTo(nx0+5, ny0+6);
  fpCtx.closePath();
  fpCtx.fillStyle="#7fb3e0";
  fpCtx.fill();
  fpCtx.fillStyle="#7fb3e0";
  fpCtx.font="10px sans-serif";
  fpCtx.textAlign="center";
  fpCtx.fillText("N", nx0, ny0+16);
}

var lt=document.getElementById("lt"),lb=document.getElementById("lbody");
function legend(){
  if(mode==="h"||mode==="y"){
    var stops=[];for(var i=0;i<=10;i++){var c=ramp(i/10);stops.push("rgb("+(c[0]|0)+","+(c[1]|0)+","+(c[2]|0)+") "+(i*10)+"%");}
    lt.textContent=mode==="h"?"building height":"year built";
    lb.innerHTML='<div id="bar" style="background:linear-gradient(90deg,'+stops.join(",")+')"></div>'+
      '<div class="lab"><span>'+(mode==="h"?"0 m":ymin)+'</span><span>'+
      (mode==="h"?Math.round(hmax)+" m+":ymax)+'</span></div>';
  } else if(mode==="e"){
    var st=[];for(var i3=0;i3<=10;i3++){var c3=ramp(i3/10);st.push("rgb("+(c3[0]|0)+","+(c3[1]|0)+","+(c3[2]|0)+") "+(i3*10)+"%");}
    lt.textContent="simulated EUI (kWh/m²)";
    lb.innerHTML='<div id="bar" style="background:linear-gradient(90deg,'+st.join(",")+')"></div>'+
      '<div class="lab"><span>'+emin.toFixed(0)+'</span><span>'+emax.toFixed(0)+'</span></div>';
  } else {
    lt.textContent="height provenance";
    var names=["measured (source)","from storeys × 3.0 m","assumed 9.0 m"],out="<div class='keys'>";
    for(var i2=0;i2<3;i2++){var p=PROV[i2];
      out+="<div><span class='sw' style='background:rgb("+p+")'></span>"+names[i2]+"</div>";}
    out+="<div><span class='sw' style='background:rgb(96,104,118)'></span>excluded / non-residential</div></div>";
    lb.innerHTML=out;
  }
}
function setMode(m,btn){
  mode=m;["bH","bP","bY","bU"].forEach(function(id){document.getElementById(id).classList.remove("on");});
  btn.classList.add("on");legend();draw();
}
document.getElementById("bH").onclick=function(){setMode("h",this);};
document.getElementById("bP").onclick=function(){setMode("p",this);};
document.getElementById("bY").onclick=function(){setMode("y",this);};
var bU=document.getElementById("bU");
bU.onclick=function(){if(!euiBound)return;setMode("e",this);};
document.getElementById("bE").onclick=function(){showExc=!showExc;this.classList.toggle("on",showExc);draw();};

var elo=document.getElementById("flo"),ehi=document.getElementById("fhi"),
    rlo=document.getElementById("rlo"),rhi=document.getElementById("rhi"),
    fcount=document.getElementById("fcount"),fnote=document.getElementById("fnote"),
    fbox=document.getElementById("flt");
function fltRefresh(){
  flo=Math.min(+elo.value,+ehi.value);fhi=Math.max(+elo.value,+ehi.value);
  rlo.textContent=flo.toFixed(1);rhi.textContent=fhi.toFixed(1);
  fltOn=(flo>emin||fhi<emax);
  var k=0;for(var i=0;i<B.length;i++){var b=B[i];
    if(b.c!==0)continue;
    if(typeof b.e!=="number"){continue;}
    if(b.e>=flo&&b.e<=fhi)k++;}
  fcount.textContent=k.toLocaleString()+" / "+evals.length.toLocaleString()+" shown";
  draw();
}
if(euiBound){
  if(D.eui_note)fnote.innerHTML=D.eui_note;else fnote.style.display="none";
  if(D.warn_html)document.getElementById("warn").innerHTML=D.warn_html;
  elo.min=ehi.min=emin;elo.max=ehi.max=emax;
  elo.step=ehi.step=Math.max(0.1,(emax-emin)/500);
  elo.value=emin;ehi.value=emax;
  elo.oninput=ehi.oninput=fltRefresh;
  fltRefresh();
} else {
  bU.disabled=true;
  bU.title="No Step-5 results are bound to this district.";
  fbox.classList.add("off");
  elo.disabled=ehi.disabled=true;
  rlo.textContent=rhi.textContent="—";
  fcount.textContent="not bound";
  fnote.innerHTML="<b>EUI not bound.</b> This district stops at Step 2 — footprints and attributes only. "+
    "No <code>05_results.csv</code> and no per-building EUI exist for it, so the filter and the EUI colouring stay "+
    "inert. Nothing is interpolated, defaulted or borrowed from another district.";
}
document.getElementById("bR").onclick=function(){fit();draw();};

resize();fit();legend();draw();
})();
</script>
</body>
</html>
"""

DISTRICT_SPECS: dict[str, dict[str, Any]] = {
    "ES-MAD-BERRUGUETE": {
        "page_title": "OpenUBEM — Madrid — Berruguete",
        "name": "Madrid — Berruguete",
        "place": "Tetuán, Madrid (ES)",
        "crs": "EPSG:32630",
        "licence": "Open Database License (ODbL) v1.0",
        "layer": "OpenStreetMap building features",
        "endpoint": "https://overpass-api.de/api/interpreter",
        "manifest_rel": "openubem/outputs/eu_evidence/EU-11/ES-MAD-BERRUGUETE/es_mad_berruguete_manifest.csv",
        "summary_rel": "openubem/outputs/eu_evidence/EU-11/ES-MAD-BERRUGUETE/summary.json",
        "epw_rel": "openubem/data/weather/es_madrid_2009_2010_y2010.epw",
        "campaign_dir_rel": "openubem/outputs/eu_evidence/EU-11/ES-MAD-BERRUGUETE",
        "warn_html": (
            "<b>Geometry for 1,194 residential buildings; simulated heating EUI for 957 of them.</b> "
            "Area-pooled over those 957: <b>79.0862 kWh/m²</b> across 999,191.1457 m² "
            "(EU-11 Speed campaign, re-simulated under D-EU-35 post-EU-13; S2 real-footprint perimeter; "
            "191 massing box / 770 dwelling layout). Buildings with no run (237) are shown grey."
        ),
        "eui_note": (
            "<b>EUI bound on 957 of 1,194 residential buildings</b> — the EU-11 full-district campaign on Speed, "
            "re-simulated 2026-08-28 under D-EU-35 against the post-EU-13 synchronized geometry pipeline "
            "(real OSM footprints, TABULA archetypes with Catastro years, ERA5 Madrid 2010 weather, EnergyPlus 23.1; "
            "957 return 0, 0 severe, 0 fatal; 4 EPLUS_FATAL excluded). <b>Heating only.</b> Geometry outcome: "
            "191 massing-box fallback, 770 dwelling layout (80.1% real partitioning, up from 5.3% pre-EU-13). "
            "S2 real-footprint perimeter (not S0 archetype campaign). The other 237 buildings are left uncoloured — "
            "nothing is interpolated, defaulted or borrowed."
        ),
    },
    "FR-LYO-HAUTCOEURPENTES": {
        "page_title": "OpenUBEM — Lyon — Haut Cœur des Pentes",
        "name": "Lyon — Haut Cœur des Pentes",
        "place": "Croix-Rousse, Lyon (FR)",
        "crs": "EPSG:32631",
        "licence": "Licence Ouverte / Open Licence 2.0 (Etalab)",
        "layer": "IGN — BD TOPO",
        "endpoint": "https://data.geopf.fr/wfs/ows",
        "manifest_rel": "openubem/outputs/eu_evidence/EU-11/FR-LYO-HAUTCOEURPENTES/fr_lyo_hautcoeurpentes_manifest.csv",
        "summary_rel": "openubem/outputs/eu_evidence/EU-11/FR-LYO-HAUTCOEURPENTES/summary.json",
        "epw_rel": "openubem/data/weather/fr_lyon_bron_2023_era5.epw",
        "campaign_dir_rel": "openubem/outputs/eu_evidence/EU-11/FR-LYO-HAUTCOEURPENTES",
        "warn_html": (
            "<b>Geometry for 530 residential buildings; simulated heating EUI for 290 of them.</b> "
            "Area-pooled over those 290: <b>70.0619 kWh/m²</b> across 394,414.574 m² "
            "(EU-11 Speed campaign, re-simulated under D-EU-35 post-EU-13; S2 real-footprint perimeter; "
            "58 massing-box fallback / 239 dwelling layout with imputed count; Speed ≠ Windows FINDING 187/190; "
            "🔴 FINDING 198 — EUI did not rise with dwelling-layout share as DR14 predicts). "
            "Buildings with no run (240) are shown grey."
        ),
        "eui_note": (
            "<b>EUI bound on 290 of 530 residential buildings</b> — the EU-11 full-district campaign on Speed, "
            "re-simulated 2026-08-28 under D-EU-35 against the post-EU-13 synchronized geometry pipeline "
            "(real IGN BD TOPO footprints, TABULA archetypes with BD TOPO years, ERA5 2023 Lyon-Bron weather, "
            "EnergyPlus 23.1; 290 return 0, 0 severe, 0 fatal; 7 EPLUS_FATAL excluded). <b>Heating only.</b> "
            "Geometry outcome: 58 narrow massing boxes, 239 dwelling layouts (80.5%, four-tier imputed count, up "
            "from 0% pre-EU-13) — yet the pooled EUI moved only 64.6017 → 70.0619, well short of DR14's "
            "population-weighted prediction (~100 kWh/m²); recorded as FINDING 198, not corrected. S2 "
            "real-footprint perimeter on Speed (not comparable to the 31-building Windows sample 60.7087 kWh/m²; "
            "FINDING 187/190). The other 240 buildings are left uncoloured — nothing is interpolated, defaulted "
            "or borrowed."
        ),
    },
    "GB-LDN-STDUNSTANS": {
        "page_title": "OpenUBEM — London — St Dunstan's",
        "name": "London — St Dunstan's",
        "place": "Tower Hamlets, London (GB)",
        "crs": "EPSG:32630",
        "licence": "Open Database License (ODbL) v1.0",
        "layer": "OpenStreetMap building features",
        "endpoint": "https://overpass-api.de/api/interpreter",
        "manifest_rel": "openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS/gb_ldn_stdunstans_manifest.csv",
        "summary_rel": "openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS/summary.json",
        "epw_rel": "openubem/data/weather/uk_london_2014_2015_y2015.epw",
        "campaign_dir_rel": "openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS",
        "warn_html": (
            "<b>Geometry for 1,242 residential buildings; simulated heating EUI for 81 of them.</b> "
            "Area-pooled over those 81: <b>74.7151 kWh/m²</b> across 90,790.3794 m² "
            "(EU-11 Speed campaign, re-simulated under D-EU-35 post-EU-13; S2 real-footprint perimeter; "
            "13 massing-box fallback / 69 dwelling layout with imputed count). "
            "Buildings with no run (1,161) are shown grey."
        ),
        "eui_note": (
            "<b>EUI bound on 81 of 1,242 residential buildings</b> — the EU-11 full-district campaign on Speed, "
            "re-simulated 2026-08-28 under D-EU-35 against the post-EU-13 synchronized geometry pipeline "
            "(real OSM footprints, TABULA archetypes with EPC age bands, ERA5 London 2015 weather, "
            "EnergyPlus 23.1; 81/82 return 0, 0 severe, 0 fatal; 1 EPLUS_FATAL excluded). <b>Heating only.</b> "
            "Geometry outcome: 13 massing-box fallback, 69 dwelling layout (84.1%, four-tier imputed count, up "
            "from 0% pre-EU-13). S2 real-footprint perimeter (not S0 archetype campaign). The other 1,161 "
            "buildings are left uncoloured — nothing is interpolated, defaulted or borrowed."
        ),
    },
    "IT-BOL-GALVANI2": {
        "page_title": "OpenUBEM — Bologna — Galvani 2",
        "name": "Bologna — Galvani 2",
        "place": "Centro storico, Bologna (IT)",
        "crs": "EPSG:32632",
        "licence": "CC BY 4.0, Comune di Bologna",
        "layer": "Comune di Bologna — rifter_edif_pl",
        "endpoint": "https://opendata.comune.bologna.it/api/explore/v2.1/catalog/datasets/rifter_edif_pl/exports/geojson?limit=-1",
        "manifest_rel": "openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2/it_bol_galvani2_manifest.csv",
        "summary_rel": "openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2/summary.json",
        "epw_rel": "openubem/data/weather/it_bologna_2013_2014_y2014.epw",
        "campaign_dir_rel": "openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2",
        "warn_html": (
            "<b>Geometry for 1,220 residential buildings; simulated heating EUI for 1,202 of them.</b> "
            "Area-pooled over those 1,202: <b>55.5346 kWh/m²</b> across 2,520,390.9432 m² "
            "(EU-14 Speed campaign, reopened under D-EU-34; S2 real-footprint perimeter; "
            "408 massing-box fallback / 796 dwelling layout with imputed count; construction period is "
            "ISTAT-census-section-imputed, never OBSERVED_YEAR; 🔴 FINDING 199 — INCOMPATIBLE (Too Low) "
            "against DR16's own asset-rating band). Buildings with no run (18) are shown grey."
        ),
        "eui_note": (
            "<b>EUI bound on 1,202 of 1,220 residential buildings</b> — the EU-14 reopened campaign on Speed "
            "(real Comune di Bologna footprints, TABULA archetypes with ISTAT 2011 census-section-imputed "
            "construction period — the INSPIRE Buildings WFS lead failed on retry, tagged "
            "construction_period_provenance=IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD, never OBSERVED_YEAR — "
            "ERA5 Bologna 2013–2014 weather, EnergyPlus 23.1; 1,202 return 0, 0 severe, 0 fatal; 2 EPLUS_FATAL "
            "excluded). <b>Heating only.</b> Geometry outcome: 408 massing-box fallback, 796 dwelling layout "
            "(66.1%, four-tier imputed count). 🔴 Pooled EUI 55.5346 kWh/m² is INCOMPATIBLE (Too Low) against "
            "DR16's pre-registered asset-rating band (115.0–165.0 CONSISTENT, &lt;95.0 INCOMPATIBLE) — recorded "
            "as FINDING 199, not corrected. S2 real-footprint perimeter (not S0 archetype campaign). The other "
            "18 buildings are left uncoloured — nothing is interpolated, defaulted or borrowed."
        ),
    },
}


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def _format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def _map_geometry_outcome(raw_outcome: Any) -> str | None:
    if pd.isna(raw_outcome):
        return None
    s = str(raw_outcome).strip()
    if s == "DWELLING_LAYOUT_EMITTED":
        return "dwelling layout (observed)"
    elif s == "DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT":
        return "dwelling layout (imputed)"
    elif s in ("FALLBACK_PENDING_LAYOUT", "FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT"):
        return "geometry-limited massing box"
    return s


def build_district(district: str) -> None:
    spec = DISTRICT_SPECS[district]
    data_dir_name = f"eu_{district}_data"
    viewer_name = f"eu_{district}_viewer.html"

    out_dir_3d = REPO_ROOT / "openubem" / "outputs" / "3D"
    mirror_dir_3d = REPO_ROOT / "docs" / "docs_ACTIVE" / "europeanLocations" / "outputs_3D"

    target_data_dir = out_dir_3d / data_dir_name
    target_data_dir.mkdir(parents=True, exist_ok=True)

    # Step 2 geometry files
    eu02_dir = REPO_ROOT / "openubem" / "outputs" / "eu02" / district
    src_json_path = eu02_dir / "01_source.json"
    res_gpkg_path = eu02_dir / "02_residential_manifest.gpkg"
    exc_gpkg_path = eu02_dir / "02_excluded_manifest.gpkg"

    res_gdf = gpd.read_file(res_gpkg_path)
    exc_gdf = gpd.read_file(exc_gpkg_path)

    res_gdf["class"] = "residential"
    exc_gdf["class"] = "excluded"
    combined_gdf = pd.concat([res_gdf, exc_gdf], ignore_index=True)

    # Calculate bounding box & span
    all_geoms = list(combined_gdf.geometry)
    minx = min(g.bounds[0] for g in all_geoms)
    miny = min(g.bounds[1] for g in all_geoms)
    maxx = max(g.bounds[2] for g in all_geoms)
    maxy = max(g.bounds[3] for g in all_geoms)
    cx = (minx + maxx) / 2.0
    cy = (miny + maxy) / 2.0
    span = round(float(max(maxx - minx, maxy - miny)), 1)

    # Height and height provenance per building
    heights: list[float] = []
    height_sources: list[str] = []
    prov_codes: list[int] = []

    for _, row in combined_gdf.iterrows():
        hm = row.get("height_m")
        lvl = row.get("levels")
        if pd.notna(hm) and float(hm) > 0:
            heights.append(round(float(hm), 1))
            height_sources.append("measured (source)")
            prov_codes.append(0)
        elif pd.notna(lvl) and float(lvl) > 0:
            heights.append(round(float(lvl) * 3.0, 1))
            height_sources.append("storeys x 3.0 m")
            prov_codes.append(1)
        else:
            heights.append(9.0)
            height_sources.append("assumed 9.0 m")
            prov_codes.append(2)

    combined_gdf["height_m"] = heights
    combined_gdf["height_source"] = height_sources
    combined_gdf["provenance_code"] = prov_codes

    # Provenance counts on residential buildings only
    res_subset = combined_gdf[combined_gdf["class"] == "residential"]
    counts = {
        "measured": int((res_subset["provenance_code"] == 0).sum()),
        "levels": int((res_subset["provenance_code"] == 1).sum()),
        "assumed": int((res_subset["provenance_code"] == 2).sum()),
    }

    # Load EU-11 manifest if present
    manifest_rel = spec["manifest_rel"]
    manifest_path = (REPO_ROOT / manifest_rel) if manifest_rel else None
    has_manifest = manifest_path is not None and manifest_path.exists()

    sim_map: dict[str, dict[str, Any]] = {}
    manifest_df: pd.DataFrame | None = None
    if has_manifest and manifest_path:
        manifest_df = pd.read_csv(manifest_path)
        for _, mrow in manifest_df.iterrows():
            bid = str(mrow["building_id"])
            rc = int(mrow["eplus_return_code"]) if pd.notna(mrow.get("eplus_return_code")) else 1
            eui = float(mrow["eui_kwh_m2"]) if pd.notna(mrow.get("eui_kwh_m2")) else None
            g_out = _map_geometry_outcome(mrow.get("geometry_outcome"))
            sim_map[bid] = {
                "eplus_return_code": rc,
                "eui_kwh_m2": eui,
                "geometry_outcome": g_out,
            }

    # Load layout side-cars if present
    eu11_layouts_dir = REPO_ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11" / district / "layouts"
    layouts_map: dict[str, dict[str, Any]] = {}
    observed_emitted_count = 0
    imputed_emitted_count = 0
    fallback_count = 0

    if eu11_layouts_dir.exists():
        for lfile in eu11_layouts_dir.glob("**/*.json"):
            ldata = json.loads(lfile.read_text(encoding="utf-8"))
            bid = ldata.get("building_id")
            if bid:
                layouts_map[str(bid)] = ldata
                out_code = ldata.get("geometry_outcome")
                if out_code == "DWELLING_LAYOUT_EMITTED":
                    observed_emitted_count += 1
                elif out_code == "DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT":
                    imputed_emitted_count += 1
                else:
                    fallback_count += 1

    # Load existing viewer's scene geometry rings if present to preserve exact vertex arrays
    existing_html = out_dir_3d / viewer_name
    existing_rings: list[list[list[float]]] = []
    if existing_html.exists():
        txt = existing_html.read_text(encoding="utf-8")
        tag = '<script type="application/json" id="scene">'
        i1 = txt.find(tag) + len(tag)
        i2 = txt.find("</script>", i1)
        prev_scene = json.loads(txt[i1:i2])
        existing_rings = [b["r"] for b in prev_scene["buildings"]]

    # Build building objects
    scene_buildings: list[dict[str, Any]] = []
    buildings_csv_rows: list[dict[str, Any]] = []
    results_csv_rows: list[dict[str, Any]] = []

    for i, row in combined_gdf.iterrows():
        bid = str(row["osm_id"])
        is_res = (row["class"] == "residential")
        c = 0 if is_res else 1
        h = float(row["height_m"])
        p = int(row["provenance_code"])
        tag = str(row["building_tag"]) if pd.notna(row.get("building_tag")) else ""
        area = round(float(row["footprint_area_m2"]), 1) if pd.notna(row.get("footprint_area_m2")) else 0.0
        levels = int(row["levels"]) if (pd.notna(row.get("levels")) and float(row["levels"]) > 0) else None
        year = int(row["year_built"]) if (pd.notna(row.get("year_built")) and float(row["year_built"]) > 0) else None

        # Ring coords
        if i < len(existing_rings):
            ring = existing_rings[i]
        else:
            poly = row.geometry
            if poly.geom_type == "MultiPolygon":
                poly = max(poly.geoms, key=lambda pg: pg.area)
            poly_s = poly.simplify(0.05, preserve_topology=True)
            ring = [[round(pt[0] - cx, 2), round(pt[1] - cy, 2)] for pt in list(poly_s.exterior.coords)[:-1]]

        # Layout summary for this building
        k_obj: dict[str, Any] | None = None
        if bid in layouts_map:
            ldata = layouts_map[bid]
            outcome = ldata.get("geometry_outcome")
            floors_data = []
            if outcome in ("DWELLING_LAYOUT_EMITTED", "DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT") and ldata.get("floors"):
                for fl in ldata["floors"]:
                    fl_zones = []
                    for z in fl.get("zones", []):
                        zr = [[round(pt[0] - cx, 2), round(pt[1] - cy, 2)] for pt in z["coords_m"]]
                        fl_zones.append({
                            "name": z["name"],
                            "r": zr,
                            "z_floor": z.get("z_floor"),
                            "z_ceiling": z.get("z_ceiling"),
                        })
                    circ = fl.get("circulation")
                    circ_r = [[round(pt[0] - cx, 2), round(pt[1] - cy, 2)] for pt in circ] if circ else None
                    floors_data.append({
                        "storey_index": fl.get("storey_index", 0),
                        "zones": fl_zones,
                        "circulation": {"r": circ_r} if circ_r else None,
                    })

            k_obj = {
                "outcome": outcome,
                "archetype": ldata.get("archetype_id"),
                "btype": ldata.get("building_type"),
                "scheme": ldata.get("scheme"),
                "storeys": ldata.get("storeys"),
                "dwellings": ldata.get("dwellings_total"),
                "upf": ldata.get("units_per_floor"),
                "core": ldata.get("has_unconditioned_core"),
                "gross": ldata.get("gross_footprint_area_m2"),
                "cond": ldata.get("conditioned_floor_area_m2"),
                "dprov": ldata.get("dwelling_count_provenance"),
                "cprov": ldata.get("construction_period_provenance"),
                "reason": ldata.get("fallback_reason"),
                "floors": floors_data,
            }

        b_obj: dict[str, Any] = {
            "r": ring,
            "h": h,
            "p": p,
            "c": c,
            "id": bid,
            "t": tag,
            "a": area,
            "l": levels,
            "y": year,
            "k": k_obj,
        }

        # Check simulation status
        sim = sim_map.get(bid)
        eui_val = None
        geom_outcome = None
        eui_status = "n/a (excluded)" if not is_res else "not simulated"

        if is_res and sim is not None:
            if sim["eplus_return_code"] == 0 and sim["eui_kwh_m2"] is not None:
                eui_val = round(sim["eui_kwh_m2"], 2)
                geom_outcome = sim["geometry_outcome"]
                eui_status = "simulated"
                b_obj["e"] = eui_val
                if geom_outcome:
                    b_obj["g"] = geom_outcome
                results_csv_rows.append({
                    "building_id": bid,
                    "eui_kwh_m2": eui_val,
                    "geometry_outcome": geom_outcome,
                })

        scene_buildings.append(b_obj)

        buildings_csv_rows.append({
            "building_id": bid,
            "class": row["class"],
            "building_tag": tag,
            "footprint_area_m2": area,
            "levels": levels,
            "height_m": h,
            "height_source": row["height_source"],
            "year_built": year,
            "eui_kwh_m2": eui_val if eui_val is not None else "",
            "eui_status": eui_status,
            "geometry_outcome": geom_outcome if geom_outcome is not None else "",
        })

    eui_bound = len(results_csv_rows) > 0
    n_res = len(res_gdf)
    n_exc = len(exc_gdf)
    not_simulated_count = n_res - (len(manifest_df) if manifest_df is not None else 0)

    layout_counts = {
        "observed_emitted": observed_emitted_count,
        "imputed_emitted": imputed_emitted_count,
        "massing_box": fallback_count,
        "not_simulated": not_simulated_count,
    }

    # Construct scene dict
    scene_dict = {
        "cell": district,
        "name": spec["name"],
        "place": spec["place"],
        "crs": spec["crs"],
        "licence": spec["licence"],
        "layer": spec["layer"],
        "endpoint": spec["endpoint"],
        "n_res": n_res,
        "n_exc": n_exc,
        "span": span,
        "counts": counts,
        "layout_counts": layout_counts,
        "data_dir": data_dir_name,
        "eui_bound": eui_bound,
        "eui_note": spec["eui_note"] if eui_bound else "",
        "warn_html": spec["warn_html"] if eui_bound else "",
        "buildings": scene_buildings,
    }

    # Write HTML viewer
    html_content = (
        HTML_HEADER_TEMPLATE.format(page_title=spec["page_title"])
        + json.dumps(scene_dict, separators=(",", ":"), ensure_ascii=False)
        + HTML_FOOTER
    )
    viewer_path = out_dir_3d / viewer_name
    viewer_path.write_text(html_content, encoding="utf-8")
    print(f"[{district}] Written viewer: {viewer_path} ({len(html_content)} bytes)")

    # Write buildings.csv
    b_df = pd.DataFrame(buildings_csv_rows)
    buildings_csv_path = target_data_dir / "buildings.csv"
    b_df.to_csv(buildings_csv_path, index=False)
    print(f"[{district}] Written buildings.csv: {len(b_df)} rows")

    # Write results.csv and results_source.csv if bound
    results_csv_path = target_data_dir / "results.csv"
    results_source_path = target_data_dir / "results_source.csv"

    if eui_bound and manifest_path and manifest_path.exists():
        res_df = pd.DataFrame(results_csv_rows)
        res_df.to_csv(results_csv_path, index=False)
        shutil.copy2(manifest_path, results_source_path)
        print(f"[{district}] Written results.csv ({len(res_df)} rows) and copied results_source.csv")
    else:
        if results_csv_path.exists():
            results_csv_path.unlink()
        if results_source_path.exists():
            results_source_path.unlink()
        print(f"[{district}] EUI not bound: results.csv and results_source.csv remain absent")

    # Copy layout side-cars to data directory if present
    target_layouts_dir = target_data_dir / "layouts"
    if eu11_layouts_dir.exists() and len(layouts_map) > 0:
        if target_layouts_dir.exists():
            shutil.rmtree(target_layouts_dir)
        shutil.copytree(eu11_layouts_dir, target_layouts_dir)
        print(f"[{district}] Copied {len(layouts_map)} layout side-cars to {target_layouts_dir}")

    # Construct sources.json
    generated_from = [
        f"openubem/outputs/eu02/{district}/01_source.json",
        f"openubem/outputs/eu02/{district}/02_residential_manifest.gpkg",
        f"openubem/outputs/eu02/{district}/02_excluded_manifest.gpkg",
    ]
    sha256_map = {
        "01_source.json": _file_sha256(src_json_path),
        "02_residential_manifest.gpkg": _file_sha256(res_gpkg_path),
        "02_excluded_manifest.gpkg": _file_sha256(exc_gpkg_path),
    }

    if has_manifest and manifest_path and manifest_rel:
        generated_from.append(manifest_rel)
        sha256_map[Path(manifest_rel).name] = _file_sha256(manifest_path)

    # Read summary.json if available
    summary_path = REPO_ROOT / spec["summary_rel"]
    summary_data: dict[str, Any] = {}
    if summary_path.exists():
        summary_data = json.loads(summary_path.read_text(encoding="utf-8"))

    epw_path = REPO_ROOT / spec["epw_rel"]
    epw_sha256 = _file_sha256(epw_path) if epw_path.exists() else summary_data.get("weather_sha256", "")

    speed_run_info: dict[str, Any] = {
        "campaign_directory": spec["campaign_dir_rel"],
        "platform": (
            f"Speed (Linux 5.14.0-687.39.1.el9_8.x86_64, Slurm job {summary_data.get('speed_job_id', 'n/a')})"
            if eui_bound else "Speed (not submitted — 0 eligible buildings)"
        ),
        "energyplus_version": "EnergyPlus, Version 23.1.0-87ed9199d4" if eui_bound else "not yet run",
        "epw": spec["epw_rel"],
        "epw_sha256": epw_sha256,
    }
    if not eui_bound:
        speed_run_info["exclusion_reason"] = "NO_PER_BUILDING_YEAR_IN_ANY_OPEN_SOURCE: 1220"

    sources_dict: dict[str, Any] = {
        "cell": district,
        "viewer": viewer_name,
        "generated_from": generated_from,
        "sha256": sha256_map,
        "speed_run": speed_run_info,
        "eui_bound": eui_bound,
        "eui_rows": len(results_csv_rows),
        "eui_coverage": f"{len(results_csv_rows)} of {n_res} residential",
        "layout_counts": layout_counts,
        "layouts_coverage": (
            f"{observed_emitted_count} observed emitted, {imputed_emitted_count} imputed emitted, "
            f"{fallback_count} massing box, {not_simulated_count} not simulated of {n_res} residential"
        ),
        "crs": spec["crs"],
        "licence": spec["licence"],
        "source_layer": spec["layer"],
        "counts": {
            "residential": n_res,
            "excluded": n_exc,
            "height_measured": counts["measured"],
            "height_from_levels": counts["levels"],
            "height_assumed": counts["assumed"],
        },
    }

    sources_json_path = target_data_dir / "sources.json"
    sources_json_path.write_text(json.dumps(sources_dict, indent=2), encoding="utf-8")
    print(f"[{district}] Written sources.json")

    # Construct index.html
    files_list_html = []
    files_list_html.append(f'<li><a href="buildings.csv">buildings.csv</a> <span>{_format_file_size(buildings_csv_path.stat().st_size)}</span></li>')
    if eui_bound:
        files_list_html.append(f'<li><a href="results.csv">results.csv</a> <span>{_format_file_size(results_csv_path.stat().st_size)}</span></li>')
        files_list_html.append(f'<li><a href="results_source.csv">results_source.csv</a> <span>{_format_file_size(results_source_path.stat().st_size)}</span></li>')
    if target_layouts_dir.exists() and len(layouts_map) > 0:
        files_list_html.append(f'<li><a href="layouts/">layouts/</a> <span>{len(layouts_map)} side-car JSON files</span></li>')
    files_list_html.append(f'<li><a href="sources.json">sources.json</a> <span>{_format_file_size(sources_json_path.stat().st_size)}</span></li>')

    if district == "ES-MAD-BERRUGUETE":
        callout_html = (
            "<b>EUI bound on 958 of 1,194 residential buildings</b> — the EU-11 full-district campaign on Speed "
            "(real OSM footprints, TABULA archetypes with Catastro years, ERA5 Madrid 2010 weather, EnergyPlus 23.1; "
            "958 return 0, 0 severe, 0 fatal; 3 EPLUS_FATAL excluded). <b>Heating only.</b> Geometry outcome: "
            "191 massing-box fallback, 769 observed dwelling layout, 1 imputed dwelling layout. Area-pooled EUI: "
            "<b>73.1889 kWh/m²</b> over 972,788.8396 m². S2 real-footprint perimeter (not S0 archetype campaign). "
            "The other 236 buildings are left uncoloured — nothing is interpolated, defaulted or borrowed."
        )
    elif district == "FR-LYO-HAUTCOEURPENTES":
        callout_html = (
            "<b>EUI bound on 292 of 530 residential buildings</b> — the EU-11 full-district campaign on Speed "
            "(real IGN BD TOPO footprints, TABULA archetypes with BD TOPO years, ERA5 2023 Lyon-Bron weather, "
            "EnergyPlus 23.1; 292 return 0, 0 severe, 0 fatal; 5 EPLUS_FATAL excluded). <b>Heating only.</b> "
            "Geometry outcome: 58 narrow massing boxes, 239 dwelling layouts (four-tier imputed count). Area-pooled EUI: "
            "<b>64.6017 kWh/m²</b> over 398,687.7658 m². S2 real-footprint perimeter on Speed (not comparable to "
            "the 31-building Windows sample 60.7087 kWh/m²; FINDING 187/190). The other 238 buildings are left "
            "uncoloured — nothing is interpolated, defaulted or borrowed."
        )
    elif district == "GB-LDN-STDUNSTANS":
        callout_html = (
            "<b>EUI bound on 82 of 1,242 residential buildings</b> — the EU-11 full-district campaign on Speed "
            "(real OSM footprints, TABULA archetypes with EPC age bands, ERA5 London 2015 weather, EnergyPlus 23.1; "
            "82/82 return 0, 0 severe, 0 fatal). <b>Heating only.</b> Geometry outcome: 13 massing-box fallback, "
            "69 dwelling layout (four-tier imputed count). Area-pooled EUI: <b>67.4153 kWh/m²</b> over 91,530.7539 m². S2 real-footprint "
            "perimeter (not S0 archetype campaign). The other 1,160 buildings are left uncoloured — nothing is "
            "interpolated, defaulted or borrowed."
        )
    else:  # IT-BOL-GALVANI2
        callout_html = (
            "<b>EUI not bound.</b> All 1,220 residential buildings are excluded "
            "(NO_PER_BUILDING_YEAR_IN_ANY_OPEN_SOURCE — no per-building construction year exists in any open "
            "source measured; see EU11 Bologna construction year investigation). <code>results.csv</code> is "
            "therefore absent, not empty-by-accident. Nothing is interpolated, defaulted or borrowed."
        )

    index_html_content = (
        f"<!doctype html><meta charset=utf-8><title>{spec['name']} — data</title>"
        f"<style>body{{background:#0d1117;color:#c9d1d9;font:14px/1.6 system-ui,sans-serif;"
        f"margin:40px auto;max-width:760px;padding:0 20px}}a{{color:#7fb3e0}}h1{{font-size:19px}}"
        f"li{{margin:4px 0}}li span{{color:#8b95a7;font-size:12px}}code{{background:#161b22;"
        f"padding:1px 4px;border-radius:3px}}.n{{background:#161b22;border-left:3px solid #2f6b9c;"
        f"padding:10px 14px;margin:16px 0;font-size:13px}}</style>"
        f"<h1>{spec['name']} &mdash; result data</h1>"
        f"<p>Files behind <a href=\"../{viewer_name}\">{viewer_name}</a>. "
        f"Every number in the viewer comes from one of these; <code>sources.json</code> carries the sha256 of each input artefact.</p>"
        f"<div class=n>{callout_html}</div>"
        f"<ul>{''.join(files_list_html)}</ul>"
    )
    index_html_path = target_data_dir / "index.html"
    index_html_path.write_text(index_html_content, encoding="utf-8")
    print(f"[{district}] Written index.html")

    # Mirror to docs/docs_ACTIVE/europeanLocations/outputs_3D/
    mirror_dir_3d.mkdir(parents=True, exist_ok=True)
    mirror_viewer_path = mirror_dir_3d / viewer_name
    shutil.copy2(viewer_path, mirror_viewer_path)

    mirror_data_dir = mirror_dir_3d / data_dir_name
    if mirror_data_dir.exists():
        shutil.rmtree(mirror_data_dir)
    shutil.copytree(target_data_dir, mirror_data_dir)
    print(f"[{district}] Mirrored viewer and data folder to {mirror_dir_3d}")


def main() -> None:
    for district in DISTRICT_SPECS:
        print(f"\n=== Generating 3D viewer for {district} ===")
        build_district(district)
    print("\nAll four European district 3D viewers regenerated and mirrored successfully.")


if __name__ == "__main__":
    main()
