"""Generate the four European district 3D viewers and their data folders.

EU-18c (`D-EU-59`): the click-through modal (3D district -> click a building
-> storey bar -> floor-plan canvas + zone table) is the deliverable. It
carries no energy, no EnergyPlus output, no run/job id, no weather -- pure
geometry. Per-building floor plans (dwelling rings, circulation ring, whole
massing-box ring, storey z-ranges) are read directly out of the emitted IDFs
under `openubem/outputs/eu_evidence/EU-17/<district>/idfs/*.idf` via
`scripts/eu_idf_plan_reader.py::read_building_plan` -- never out of the
EU-11 layout side-cars, which disagree with the IDFs on 970 buildings
(`FINDING 213` / `FINDING 215`). The district's own EU-17 side-car (same
rebuild tree) may supply the scheme name / refusal reason as annotation
only, and only when it agrees with what the IDF's own zone kinds show.

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

from scripts.eu_idf_plan_reader import BuildingPlan, ZonePlan, parse_idf_floor_zones, read_district

REPO_ROOT = Path("C:/Users/o_iseri/Desktop/OpenUBEM")
EU17_ROOT = REPO_ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-17"
EU11_ROOT = REPO_ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11"
EU21_ROOT = REPO_ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-21" / "district_plans"

# Same check-id order as `scripts/eu21/08_district_viewer.py:46` -- annotation
# only (T03, hard rule 3): never a second source of truth for geometry.
CHECK_IDS = ("C1", "C3", "C4", "C5", "C6", "C10", "C11")

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
.m-badge.finding{{background:#0d3349;color:#58a6ff;border:1px solid #1f6feb}}
.m-badge.fallback{{background:#3a2410;color:#f0c07a;border:1px solid #7a4b12}}
.m-badge.noidf{{background:#22272e;color:#8b95a7;border:1px solid #373e47}}
.checks{{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px}}
.chk{{font-family:"IBM Plex Mono",monospace;font-size:11px;padding:2px 7px;border:1px solid #262d3a;border-radius:3px;color:#8b95a7;background:#161b24}}
.chk.ok{{border-color:#238636;color:#7ee787;background:#173d2a}}
.chk.bad{{border-color:#9e3c2c;color:#f59e8b;background:#2e1a16}}
.m-info-box{{background:#161b24;border:1px solid #262d3a;border-radius:8px;padding:10px 12px;font-size:12px;margin-bottom:14px}}
.m-info-box p{{margin:3px 0}}
.m-info-box code{{background:#0d1117;padding:1px 5px;border-radius:3px;font-size:11px;color:#e6e9ef}}
.storey-bar{{display:flex;align-items:center;gap:6px;margin-bottom:10px;font-size:12px;flex-wrap:wrap}}
.storey-btn{{background:#1a212c;border:1px solid #2d3646;color:#c8d1de;border-radius:4px;padding:2px 7px;font-size:11px;cursor:pointer}}
.storey-btn.active{{background:#1f6feb;border-color:#388bfd;color:#fff;font-weight:bold}}
#fp-container{{background:#0a0d13;border:1px solid #212835;border-radius:8px;padding:12px;display:flex;flex-direction:column;align-items:center;margin-bottom:12px}}
#fp-canvas{{display:block;background:#090c10;border-radius:6px;border:1px solid #1a212d}}
#fp-legend{{display:flex;flex-wrap:wrap;gap:8px 20px;align-items:center;margin-top:8px;font-size:11px;color:#8b95a7}}
#fp-legend .sw{{display:inline-flex;align-items:center;gap:6px}}
#fp-legend .sw i{{width:14px;height:14px;display:inline-block;border-radius:2px}}
#m-zones{{font-size:11.5px;color:#8b95a7;margin-top:8px;width:100%}}
#m-zones table{{width:100%;border-collapse:collapse;margin-top:4px}}
#m-zones th,#m-zones td{{padding:5px 8px;text-align:left;border-bottom:1px solid #1e2531}}
#m-zones th{{color:#6e7681;font-weight:500;font-family:"IBM Plex Mono",monospace;font-size:11px}}
#m-zones td{{font-family:"IBM Plex Mono",monospace;font-size:11.5px;color:#c8d1de}}
#m-zones td code{{font-size:11px;color:#8fd0ff}}
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
  <div class="row"><span class="k">Simulated (has EUI)</span><span id="nsim"></span></div>
  <div class="row"><span class="k">IDF only, not simulated</span><span id="nidfonly"></span></div>
  <div class="row"><span class="k">No IDF</span><span id="nnoidf"></span></div>
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
    <button id="bS">colour: simulated</button>
    <button id="bU">colour: EUI</button>
    <button id="bE" class="on">show excluded</button>
    <button id="bR">reset view</button>
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
      <canvas id="fp-canvas" width="580" height="320"></canvas>
      <div id="fp-legend"></div>
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
document.getElementById("nsim").textContent=(D.sim_counts ? D.sim_counts.simulated : 0).toLocaleString();
document.getElementById("nidfonly").textContent=(D.sim_counts ? D.sim_counts.idf_only : 0).toLocaleString();
document.getElementById("nnoidf").textContent=(D.sim_counts ? D.sim_counts.no_idf : D.n_res).toLocaleString();
document.getElementById("hm").textContent=D.counts.measured.toLocaleString();
document.getElementById("hl").textContent=D.counts.levels.toLocaleString();
document.getElementById("ha").textContent=D.counts.assumed.toLocaleString();
document.getElementById("crs").textContent=D.crs;
document.getElementById("span").textContent=Math.round(D.span)+" m";
document.getElementById("layer").textContent=D.layer;
document.getElementById("lic").textContent=D.licence;
document.getElementById("dataf").innerHTML='<a href="'+D.data_dir+'/index.html" target="_blank">'+D.data_dir+'/</a>';
if(D.geometry_note)document.getElementById("warn").innerHTML=D.geometry_note;

var hmax=1;for(var i=0;i<B.length;i++)if(B[i].h>hmax)hmax=B[i].h;
hmax=Math.min(hmax,60);
var years=B.filter(function(b){return b.y}).map(function(b){return b.y});
var ymin=years.length?Math.min.apply(null,years):1900,ymax=years.length?Math.max.apply(null,years):2020;
var euis=B.filter(function(b){return b.eui!=null;}).map(function(b){return b.eui;});
var euimin=euis.length?Math.min.apply(null,euis):0,euimax=euis.length?Math.max.apply(null,euis):200;

var RAMP=[[68,1,84],[59,82,139],[33,145,140],[94,201,98],[253,231,37]];
function ramp(t){t=Math.max(0,Math.min(1,t));var s=t*(RAMP.length-1),i=Math.floor(s),f=s-i;
  if(i>=RAMP.length-1){i=RAMP.length-2;f=1;}
  var a=RAMP[i],b=RAMP[i+1];
  return [a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f,a[2]+(b[2]-a[2])*f];}
var PROV=[[86,180,233],[240,180,60],[200,90,110]];
var STATE_COLORS=[[59,130,246],[148,163,184],[217,119,6]];
var STATE_NAMES=["dwelling layout ruled","massing box","no IDF"];
function stateIdx(b){
  if(b.ls==="ruled")return 0;
  if(b.ls==="massing_box")return 1;
  return 2;
}
function stateLabel(b){return b.ls?STATE_NAMES[stateIdx(b)]:"n/a";}
var SIM_COLORS=[[34,197,94],[217,119,6],[148,163,184]];
var SIM_NAMES=["simulated (has EUI)","IDF only, not simulated","no IDF"];
function simIdx(b){
  if(b.ss==="simulated")return 0;
  if(b.ss==="idf_only")return 1;
  return 2;
}
function baseColor(b){
  if(b.c===1)return [96,104,118];
  if(mode==="p")return PROV[b.p];
  if(mode==="y"){if(!b.y)return [80,88,100];return ramp((b.y-ymin)/Math.max(1,ymax-ymin));}
  if(mode==="s")return SIM_COLORS[simIdx(b)];
  if(mode==="u"){if(b.eui==null)return [80,88,100];return ramp((b.eui-euimin)/Math.max(1,euimax-euimin));}
  return ramp(b.h/hmax);
}
var mode="h";

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
      "<br>footprint "+b.a.toFixed(0)+" m²"+
      (b.ls?"<br>layout: <b>"+stateLabel(b)+"</b>":"")+
      "<br><span style='color:#7fb3e0;font-size:10.5px;'>click for floor plan &rarr;</span>";
    tip.style.display="block";
    tip.style.left=Math.min(e.clientX+14,window.innerWidth-282)+"px";
    tip.style.top=(e.clientY+14)+"px";
    return;
  }
  hide();
}

var ZONE_COLORS=[
  "#287294",
  "#328452",
  "#937320",
  "#9e4438",
  "#7b5294",
  "#b35c34",
  "#2c8a85",
  "#8a4f7d",
  "#4f6b96",
  "#82802b",
  "#96425a",
  "#387680"
];

/* Floor Plan Modal Logic */
var modalBackdrop=document.getElementById("modal-backdrop"),
    modalClose=document.getElementById("modal-close"),
    mTitle=document.getElementById("m-title"),
    mSub=document.getElementById("m-sub"),
    mStatusBox=document.getElementById("m-status-box"),
    mStoreyBar=document.getElementById("m-storey-bar"),
    mZones=document.getElementById("m-zones"),
    fpLegend=document.getElementById("fp-legend"),
    fpCanvas=document.getElementById("fp-canvas"),
    fpCtx=fpCanvas.getContext("2d");

var currentModalBuilding=null;
var currentStoreyIndex=0;

function closePopup(){modalBackdrop.style.display="none";cv.focus();}
modalClose.onclick=closePopup;
modalBackdrop.onclick=function(e){if(e.target===modalBackdrop)closePopup();};
window.addEventListener("keydown",function(e){if(e.key==="Escape")closePopup();});

function openPopup(b){
  hide();
  currentModalBuilding=b;
  currentStoreyIndex=0;
  var prov=["measured (source)","from storeys × 3.0 m","assumed 9.0 m"][b.p];
  mTitle.textContent=b.id + (b.t ? " — " + b.t : "");

  var pl=b.pl;
  var storeys=pl ? pl.st : (b.l || "—");
  var dwellings=pl ? pl.dw : "—";
  var core=pl ? (pl.core ? "Yes" : "No") : "—";
  var areaStr=pl ? (pl.gm.toFixed(0) + " m² gross / " + pl.cm.toFixed(0) + " m² conditioned") : (b.a.toFixed(0) + " m² footprint");
  var circStr=(pl && pl.cp!==null && pl.cp!==undefined) ? (pl.cp.toFixed(1) + "%") : "—";

  mSub.innerHTML="<b>Storeys:</b> " + storeys + " &middot; " +
    "<b>Dwellings:</b> " + dwellings + " &middot; " +
    "<b>Unconditioned core:</b> " + core + " &middot; " +
    "<b>Circulation share:</b> " + circStr + "<br>" +
    "<b>Height:</b> " + b.h.toFixed(1) + " m <i>(" + prov + ")</i> &middot; " +
    "<b>Area:</b> " + areaStr;

  var statusHtml="";
  var bestEffortIds=(pl && pl.reason && pl.reason.indexOf("NOCORE_BEST_EFFORT_")===0)
    ? pl.reason.slice("NOCORE_BEST_EFFORT_".length).split("_").join(", ") : null;
  if(b.ls==="ruled" && bestEffortIds){
    statusHtml="<span class='m-badge fallback'>DIVIDED &mdash; BEST EFFORT (shape check failed: " + bestEffortIds + ")</span>";
    if(pl && pl.scheme) statusHtml += " <b>Scheme:</b> " + pl.scheme + ".";
    statusHtml += "<p style='color:#8b95a7;font-size:11.5px;margin-top:4px;'>D-EU-111: this cut failed a shape check (thin flat / short facade / pinch) but every dwelling is still drawn with real party walls. Zone geometry read directly from the emitted IDF, storey by storey.</p>";
  } else if(b.ls==="ruled"){
    statusHtml="<span class='m-badge emitted'>DWELLING LAYOUT &mdash; RULED (read from IDF)</span>";
    if(pl && pl.scheme) statusHtml += " <b>Scheme:</b> " + pl.scheme + ".";
    statusHtml += "<p style='color:#8b95a7;font-size:11.5px;margin-top:4px;'>Zone geometry read directly from the emitted IDF, storey by storey.</p>";
  } else if(b.ls==="massing_box"){
    statusHtml="<span class='m-badge fallback'>MASSING BOX (read from IDF)</span>";
    if(pl && pl.reason) statusHtml += " Reason: <code>" + pl.reason + "</code>.";
    statusHtml += "<p style='color:#8b95a7;font-size:11.5px;margin-top:4px;'>One undivided zone per storey. No interior partition exists in the IDF.</p>";
  } else {
    statusHtml="<span class='m-badge noidf'>NO IDF</span> " +
      (b.c===1 ? "Excluded / non-residential building." : "No IDF file exists for this building in the ceiling82 or EU-17 tree.") +
      "<p style='color:#8b95a7;font-size:11.5px;margin-top:4px;'>Showing footprint outline only.</p>";
  }
  if(pl && pl.f204){
    statusHtml += "<span class='m-badge finding'>FINDING 204</span> circulation outside the ruled 12.0&ndash;25.0 m&sup2; band<br>";
  }
  if(pl && pl.chk){
    var chipsHtml="";
    var failList=[];
    if(pl.chk.ch && pl.chk.ch.length>0){
      chipsHtml="<div class='checks'>";
      for(var ci=0; ci<pl.chk.ch.length; ci++){
        var cid=pl.chk.ch[ci][0], cval=pl.chk.ch[ci][1], cpass=pl.chk.ch[ci][2];
        var ccls=cpass?"ok":"bad";
        if(!cpass)failList.push(cid);
        chipsHtml += "<span class='chk " + ccls + "'>" + cid + " " + cval + "</span> ";
      }
      chipsHtml += "</div>";
    }
    if(pl.chk.v==="PASS"){
      statusHtml += "<span class='m-badge emitted'>PASS ALL 7 CHECKS</span> " +
        "<b>Scheme:</b> nocore equal-area cut.<br>" + chipsHtml;
    } else {
      statusHtml += "<span class='m-badge fallback'>FAIL</span> " +
        "<b>Failing checks:</b> " + (failList.length>0 ? failList.join(", ") : "see checks") + ".<br>" + chipsHtml;
    }
  }
  mStatusBox.innerHTML=statusHtml;

  var sf=(pl && pl.sf) ? pl.sf : [];
  if(sf.length>0){
    var sHtml="<span style='color:#8b95a7;margin-right:4px;'>Storey:</span> ";
    for(var s=0; s<sf.length; s++){
      sHtml += "<button class='storey-btn" + (s===0 ? " active" : "") + "' onclick='selectStorey(" + s + ")'>F" + sf[s].i + " (" + sf[s].z0.toFixed(1) + "–" + sf[s].z1.toFixed(1) + "m)</button> ";
    }
    mStoreyBar.innerHTML=sHtml;
    mStoreyBar.style.display="flex";
  } else {
    mStoreyBar.innerHTML="<span style='color:#8b95a7;'>No storey geometry available.</span>";
    mStoreyBar.style.display="flex";
  }

  drawFloorPlan(b, 0, -1);
  modalBackdrop.style.display="flex";
}

window.selectStorey=function(sIdx){
  currentStoreyIndex=sIdx;
  var btns=mStoreyBar.getElementsByClassName("storey-btn");
  for(var i=0; i<btns.length; i++){
    btns[i].classList.toggle("active", i===sIdx);
  }
  if(currentModalBuilding){
    drawFloorPlan(currentModalBuilding, sIdx, -1);
  }
};

window.highlightDwelling=function(zIdx){
  if(currentModalBuilding)drawFloorPlan(currentModalBuilding, currentStoreyIndex, zIdx);
};
window.unhighlightDwelling=function(){
  if(currentModalBuilding)drawFloorPlan(currentModalBuilding, currentStoreyIndex, -1);
};

function circLabelText(lbl){
  if(lbl==="core")return "Unconditioned stair core";
  if(lbl==="spine")return "Unconditioned circulation spine";
  return "Unconditioned circulation";
}

function drawFloorPlan(b, sIdx, hlIdx){
  if(hlIdx===undefined) hlIdx=-1;
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

  // Draw building footprint outline (dark ground, plans3D style)
  fpCtx.beginPath();
  for(var j=0;j<r.length;j++){
    var X=fx(r[j][0]), Y=fy(r[j][1]);
    if(j===0)fpCtx.moveTo(X,Y);else fpCtx.lineTo(X,Y);
  }
  fpCtx.closePath();
  fpCtx.fillStyle="rgba(255,255,255,0.04)";
  fpCtx.fill("evenodd");
  fpCtx.strokeStyle="#8b95a7";
  fpCtx.lineWidth=2;
  fpCtx.stroke();

  var pl=b.pl;
  var sf=(pl && pl.sf) ? pl.sf : [];
  var storey=sf[sIdx];
  var zonesTable="";
  var sawDwelling=false, sawCirc=false, sawWhole=false;

  if(storey){
    for(var z=0;z<storey.z.length;z++){
      var zn=storey.z[z];
      var isWhole=(zn.ki==="w");
      var zoneColor = isWhole ? "#e5e7eb" : ZONE_COLORS[(zn.di - 1) % ZONE_COLORS.length];
      fpCtx.beginPath();
      var zcx=0, zcy=0, nverts=0;
      for(var v=0;v<zn.r.length;v++){
        var ZX=fx(zn.r[v][0]), ZY=fy(zn.r[v][1]);
        if(v===0)fpCtx.moveTo(ZX,ZY);else fpCtx.lineTo(ZX,ZY);
        zcx += ZX; zcy += ZY; nverts++;
      }
      fpCtx.closePath();
      fpCtx.fillStyle = isWhole ? "rgba(255,255,255,0.07)" : zoneColor;
      fpCtx.fill();
      if(isWhole){
        fpCtx.strokeStyle="#8b95a7";
        fpCtx.lineWidth=2;
      } else if(hlIdx===z){
        fpCtx.strokeStyle="#ffffff";
        fpCtx.lineWidth=2.4;
      } else {
        fpCtx.strokeStyle="rgba(255,255,255,0.85)";
        fpCtx.lineWidth=1.4;
      }
      fpCtx.stroke();

      zcx /= nverts; zcy /= nverts;
      var label = isWhole ? "Undivided massing box" : ("D" + zn.di);
      if(isWhole){
        fpCtx.fillStyle="#c8d1de";
        fpCtx.font="bold 12px sans-serif";
        fpCtx.textAlign="center";
        fpCtx.textBaseline="middle";
        fpCtx.fillText(label, zcx, zcy);
      } else {
        fpCtx.save();
        fpCtx.shadowColor="rgba(0,0,0,0.85)";
        fpCtx.shadowBlur=4;
        fpCtx.fillStyle="#ffffff";
        fpCtx.font="bold 11px sans-serif";
        fpCtx.textAlign="center";
        fpCtx.textBaseline="middle";
        fpCtx.fillText(label, zcx, zcy);
        fpCtx.restore();
      }
      if(isWhole) sawWhole=true; else sawDwelling=true;

      var elev=storey.z0.toFixed(1)+"–"+storey.z1.toFixed(1)+" m";
      var swatch="<span style='display:inline-block;width:13px;height:13px;background:"+zoneColor+";border:1px solid rgba(255,255,255,0.7);border-radius:2px;vertical-align:middle;'></span>";
      var dwIdx = isWhole ? "—" : ("Dwelling " + zn.di);
      var rowAttrs = isWhole ? "" : " onmouseenter='highlightDwelling(" + z + ")' onmouseleave='unhighlightDwelling()' style='cursor:pointer'";
      zonesTable += "<tr" + rowAttrs + "><td><code>" + zn.nm + "</code></td><td>" + swatch + "</td><td>" + dwIdx + "</td><td>" + zn.a.toFixed(1) + " m&sup2;</td><td>" + elev + "</td></tr>";
    }

    if(storey.c){
      var cr=storey.c.r;
      fpCtx.beginPath();
      var ccx=0, ccy=0;
      for(var ci=0;ci<cr.length;ci++){
        var CX=fx(cr[ci][0]), CY=fy(cr[ci][1]);
        if(ci===0)fpCtx.moveTo(CX,CY);else fpCtx.lineTo(CX,CY);
        ccx += CX; ccy += CY;
      }
      fpCtx.closePath();
      fpCtx.fillStyle="#3a2410";
      fpCtx.fill();
      fpCtx.strokeStyle="#7a4b12";
      fpCtx.lineWidth=3;
      fpCtx.stroke();

      ccx /= cr.length; ccy /= cr.length;
      var clabel=circLabelText(storey.c.lbl);
      fpCtx.fillStyle="#f0c07a";
      fpCtx.font="bold 11px sans-serif";
      fpCtx.textAlign="center";
      fpCtx.textBaseline="middle";
      if(storey.c.lbl==="core"){
        fpCtx.fillText("Unconditioned",ccx,ccy-7);
        fpCtx.fillText("stair core",ccx,ccy+7);
      } else {
        fpCtx.fillText(clabel,ccx,ccy);
      }
      sawCirc=true;

      var celev=storey.z0.toFixed(1)+"–"+storey.z1.toFixed(1)+" m";
      var circSwatch="<span style='display:inline-block;width:13px;height:13px;background:#3a2410;border:1px solid rgba(255,255,255,0.7);border-radius:2px;vertical-align:middle;'></span>";
      zonesTable += "<tr><td>" + clabel + "</td><td>" + circSwatch + "</td><td>—</td><td>" + storey.c.a.toFixed(1) + " m&sup2;</td><td>" + celev + "</td></tr>";
    }
  }

  mZones.innerHTML = zonesTable
    ? "<table><thead><tr><th>Zone Name</th><th>Colour</th><th>Dwelling Index</th><th>Area</th><th>Storey elevation</th></tr></thead><tbody>" + zonesTable + "</tbody></table>"
    : "";

  var lg="";
  if(sawDwelling) lg += "<span class='sw'><i style='background:"+ZONE_COLORS[0]+";border:1px solid rgba(255,255,255,0.85)'></i>Dwelling zone</span>";
  if(sawCirc) lg += "<span class='sw'><i style='background:#3a2410;border:1px solid #7a4b12'></i>Circulation/core zone</span>";
  if(sawWhole) lg += "<span class='sw'><i style='background:rgba(255,255,255,0.07);border:1px solid #8b95a7'></i>Undivided massing box</span>";
  fpLegend.innerHTML=lg;

  // Draw Scale Bar (metric, light-on-dark)
  var barMeters=10;
  if(sc > 15) barMeters=5;
  if(sc > 35) barMeters=2;
  if(sc < 5) barMeters=20;
  if(sc < 2) barMeters=50;
  var barPx=barMeters * sc;
  var bx0=24, by0=ch-20;
  fpCtx.beginPath();
  fpCtx.moveTo(bx0, by0-4); fpCtx.lineTo(bx0, by0); fpCtx.lineTo(bx0+barPx, by0); fpCtx.lineTo(bx0+barPx, by0-4);
  fpCtx.strokeStyle="#c9d1d9";
  fpCtx.lineWidth=1.5;
  fpCtx.stroke();
  fpCtx.fillStyle="#8b95a7";
  fpCtx.font="10px monospace";
  fpCtx.textAlign="left";
  fpCtx.textBaseline="bottom";
  fpCtx.fillText(barMeters + " m", bx0, by0-6);

  // Draw North Arrow (light-on-dark)
  var nx0=cw-28, ny0=26;
  fpCtx.beginPath();
  fpCtx.moveTo(nx0, ny0-10); fpCtx.lineTo(nx0-5, ny0+6); fpCtx.lineTo(nx0, ny0+2); fpCtx.lineTo(nx0+5, ny0+6);
  fpCtx.closePath();
  fpCtx.fillStyle="#7fb3e0";
  fpCtx.fill();
  fpCtx.fillStyle="#7fb3e0";
  fpCtx.font="bold 10px sans-serif";
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
  } else if(mode==="u"){
    var stopsU=[];for(var iu=0;iu<=10;iu++){var cu=ramp(iu/10);stopsU.push("rgb("+(cu[0]|0)+","+(cu[1]|0)+","+(cu[2]|0)+") "+(iu*10)+"%");}
    lt.textContent="heating EUI (kWh/m²)";
    lb.innerHTML='<div id="bar" style="background:linear-gradient(90deg,'+stopsU.join(",")+')"></div>'+
      '<div class="lab"><span>'+Math.round(euimin)+'</span><span>'+Math.round(euimax)+'</span></div>'+
      "<div class='keys' style='margin-top:6px'><div><span class='sw' style='background:rgb(80,88,100)'></span>not simulated</div></div>";
  } else if(mode==="s"){
    lt.textContent="simulation state";
    var out2="<div class='keys'>";
    for(var i3=0;i3<3;i3++){var c3=SIM_COLORS[i3];
      out2+="<div><span class='sw' style='background:rgb("+c3+")'></span>"+SIM_NAMES[i3]+"</div>";}
    out2+="<div><span class='sw' style='background:rgb(96,104,118)'></span>excluded / non-residential</div></div>";
    lb.innerHTML=out2;
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
  mode=m;["bH","bP","bY","bS","bU"].forEach(function(id){document.getElementById(id).classList.remove("on");});
  btn.classList.add("on");legend();draw();
}
document.getElementById("bH").onclick=function(){setMode("h",this);};
document.getElementById("bP").onclick=function(){setMode("p",this);};
document.getElementById("bY").onclick=function(){setMode("y",this);};
document.getElementById("bS").onclick=function(){setMode("s",this);};
document.getElementById("bU").onclick=function(){setMode("u",this);};
document.getElementById("bE").onclick=function(){showExc=!showExc;this.classList.toggle("on",showExc);draw();};
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
    },
    "FR-LYO-HAUTCOEURPENTES": {
        "page_title": "OpenUBEM — Lyon — Haut Cœur des Pentes",
        "name": "Lyon — Haut Cœur des Pentes",
        "place": "Croix-Rousse, Lyon (FR)",
        "crs": "EPSG:32631",
        "licence": "Licence Ouverte / Open Licence 2.0 (Etalab)",
        "layer": "IGN — BD TOPO",
        "endpoint": "https://data.geopf.fr/wfs/ows",
    },
    "GB-LDN-STDUNSTANS": {
        "page_title": "OpenUBEM — London — St Dunstan's",
        "name": "London — St Dunstan's",
        "place": "Tower Hamlets, London (GB)",
        "crs": "EPSG:32630",
        "licence": "Open Database License (ODbL) v1.0",
        "layer": "OpenStreetMap building features",
        "endpoint": "https://overpass-api.de/api/interpreter",
    },
    "IT-BOL-GALVANI2": {
        "page_title": "OpenUBEM — Bologna — Galvani 2",
        "name": "Bologna — Galvani 2",
        "place": "Centro storico, Bologna (IT)",
        "crs": "EPSG:32632",
        "licence": "CC BY 4.0, Comune di Bologna",
        "layer": "Comune di Bologna — rifter_edif_pl",
        "endpoint": "https://opendata.comune.bologna.it/api/explore/v2.1/catalog/datasets/rifter_edif_pl/exports/geojson?limit=-1",
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


def _scene_ring(
    ring: tuple[tuple[float, float], ...], origin_xy: tuple[float, float], cx: float, cy: float
) -> list[list[float]]:
    """A zone ring in the same district-centred, 1 cm-rounded local-metre
    frame the footprint ring ``b.r`` already uses (dependency decision
    §4.4's ``local_ring_1cm`` convention), so the plan overlays the
    footprint exactly (T01). ``read_building_plan`` translates zone
    coordinates to a *building-local* origin (the storey-0 centroid,
    ``origin_xy``); this undoes that and re-expresses the ring in the
    district-frame the way the footprint ring is built (`:979`)."""
    ox, oy = origin_xy
    return [[round(x + ox - cx, 2), round(y + oy - cy, 2)] for x, y in ring]


def _storey_z_ranges(zone_max_z: dict[str, float], zones: tuple) -> dict[int, tuple[float, float]]:
    """Per-storey-group ``(z_floor, z_ceiling)`` read off the IDF's own
    measured surface heights (``zone_max_z``, from
    ``parse_idf_floor_zones``), not off a nominal ``FLOOR_TO_FLOOR_M``
    multiplication -- a group's ceiling is the tallest of its own zones,
    and groups stack bottom-up (dependency decision, this slice: group
    order is trusted, not its F-number's literal physical-storey value,
    since an absorbed group's F-number is only its ordinal position)."""
    groups = sorted({z.storey for z in zones})
    ranges: dict[int, tuple[float, float]] = {}
    z_prev = 0.0
    for g in groups:
        names_in_group = [z.name for z in zones if z.storey == g]
        z_top = max((zone_max_z.get(n, z_prev) for n in names_in_group), default=z_prev)
        ranges[g] = (z_prev, z_top)
        z_prev = z_top
    return ranges


def _circulation_label(rings: tuple[tuple[tuple[float, float], ...], ...]) -> str:
    """``core`` (point-block stair core) vs ``spine`` (double-loaded
    corridor) vs ``circulation`` (ambiguous), by the ring's own bounding-box
    aspect ratio -- T04 leaves the exact split to the executor; thresholds
    (<=1.6 core, >=2.75 spine, else ambiguous) are this task's own decision,
    not specified upstream."""
    minx = miny = 1e18
    maxx = maxy = -1e18
    for ring in rings:
        for x, y in ring:
            minx = min(minx, x)
            maxx = max(maxx, x)
            miny = min(miny, y)
            maxy = max(maxy, y)
    w = max(maxx - minx, 1e-6)
    h = max(maxy - miny, 1e-6)
    long_side, short_side = max(w, h), max(min(w, h), 1e-6)
    ratio = long_side / short_side
    if ratio <= 1.6:
        return "core"
    if ratio >= 2.75:
        return "spine"
    return "circulation"


def _load_eu17_sidecar(district: str, building_id: str) -> dict | None:
    path = EU17_ROOT / district / "layouts" / f"{building_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _load_eu11_eui(district: str) -> dict[str, float | None]:
    """``{building_id: eui_kwh_m2}`` from the EU-11 merged manifest
    (``_merged_2026-09-07``) when present, else the ceiling82 manifest
    (``_ceiling82_2026-09-05``, T01), mirroring ``_load_eu17_sidecar``'s
    per-district single-file load shape but for the CSV manifest, not a
    per-building JSON side-car. A building with no manifest row (excluded
    / no_idf / failed-on-Speed) is simply absent from the dict; a manifest
    row with a blank ``eui_kwh_m2`` maps to ``None`` rather than being
    dropped."""
    city_lower = district.lower().replace("-", "_")
    path = EU11_ROOT / f"{district}_merged_2026-09-07" / f"{city_lower}_manifest.csv"
    if not path.exists():
        path = EU11_ROOT / f"{district}_ceiling82_2026-09-05" / f"{city_lower}_manifest.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path, usecols=["building_id", "eui_kwh_m2"], dtype={"building_id": str})
    eui_by_id: dict[str, float | None] = {}
    for bid, eui in zip(df["building_id"], df["eui_kwh_m2"]):
        eui_by_id[bid] = float(eui) if pd.notna(eui) else None
    return eui_by_id


def _load_eu21_evidence(district: str) -> dict[str, dict[str, Any]]:
    """``{building_id: {"status", "verdict", "checks", "scheme"}}`` from the
    EU-21 no-core rules cutter's own evidence JSON (T03), mirroring
    ``_load_eu17_sidecar``'s per-district single-file load shape but for one
    JSON carrying a ``plates[]`` list rather than one file per building.
    Annotation only (hard rule 3): geometry never comes from here, and a
    building missing from this dict (or present with ``status`` other than
    ``"direct"``, e.g. ``GENERIC_NO_CENSUS``/``REFUSED_K_GT_12``, which carry
    no ``checks``) simply renders with no checks badge, never a fabricated
    one."""
    path = EU21_ROOT / f"{district}_nocore_2026-09-03_r5.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    evidence_by_id: dict[str, dict[str, Any]] = {}
    for plate in data.get("plates", []):
        bid = str(plate["building_id"])
        evidence_by_id[bid] = {
            "status": plate.get("status"),
            "verdict": plate.get("verdict"),
            "checks": plate.get("checks"),
            "scheme": plate.get("scheme"),
        }
    return evidence_by_id


def _build_plan_payload(
    plan: BuildingPlan, idf_path: Path, sidecar: dict | None, cx: float, cy: float
) -> dict[str, Any]:
    """The modal's entire per-building payload, built from the parsed IDF
    (T01): per-storey dwelling/whole zone rings, the circulation ring where
    present, storey z-ranges, dwelling count per storey, gross/conditioned
    area. ``scheme``/``reason``/``finding204`` are the only fields taken
    from the side-car, and only when the side-car's own ruled/massing-box
    claim agrees with what the IDF's zone kinds actually show -- never
    letting a side-car field decide a polygon (rule 3)."""
    _, _, zone_max_z = parse_idf_floor_zones(idf_path)
    z_ranges = _storey_z_ranges(zone_max_z, plan.zones)

    by_storey: dict[int, list] = {}
    for zone in plan.zones:
        by_storey.setdefault(zone.storey, []).append(zone)

    storeys_payload = []
    for storey in sorted(by_storey):
        z0, z1 = z_ranges.get(storey, (storey * 3.0, (storey + 1) * 3.0))
        zones_payload = []
        circ_payload = None
        n_dwellings = 0
        for zone in by_storey[storey]:
            rings_scene = [_scene_ring(ring, plan.origin_xy, cx, cy) for ring in zone.rings]
            ring_scene = rings_scene[0] if len(rings_scene) == 1 else [pt for ring in rings_scene for pt in ring]
            if zone.kind == "dwelling":
                n_dwellings += 1
                zones_payload.append({
                    "nm": zone.name,
                    "ki": "d",
                    "di": (zone.dwelling_index if zone.dwelling_index is not None else 0) + 1,
                    "r": ring_scene,
                    "a": round(zone.area_m2, 1),
                })
            elif zone.kind == "whole":
                zones_payload.append({
                    "nm": zone.name,
                    "ki": "w",
                    "di": None,
                    "r": ring_scene,
                    "a": round(zone.area_m2, 1),
                })
            else:  # circulation
                circ_payload = {
                    "r": ring_scene,
                    "a": round(zone.area_m2, 1),
                    "lbl": _circulation_label(zone.rings),
                }
        storeys_payload.append({
            "i": storey,
            "z0": round(z0, 1),
            "z1": round(z1, 1),
            "nd": n_dwellings,
            "z": zones_payload,
            "c": circ_payload,
        })

    idf_ruled = plan.is_ruled()
    sidecar_ruled = bool(
        sidecar and str(sidecar.get("geometry_outcome", "")).startswith("DWELLING_LAYOUT_EMITTED")
    )
    agrees = sidecar is not None and idf_ruled == sidecar_ruled
    circ_pct = (
        round(100.0 * plan.circulation_area_m2 / plan.gross_area_m2, 1) if plan.gross_area_m2 > 0 else None
    )

    return {
        "st": plan.storey_count,
        "dw": plan.dwelling_count,
        "gm": round(plan.gross_area_m2, 1),
        "cm": round(plan.conditioned_area_m2, 1),
        "cc": round(plan.circulation_area_m2, 1),
        "cp": circ_pct,
        "core": plan.has_unconditioned_core(),
        "scheme": (sidecar.get("scheme") if (agrees and sidecar) else None),
        "reason": (sidecar.get("fallback_reason") if (agrees and sidecar) else None),
        "f204": (bool(sidecar.get("circulation_outside_ruled_absolute_band")) if (agrees and sidecar) else None),
        "sf": storeys_payload,
    }


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

    # Geometry, read from the emitted IDFs -- rule 3: never the layout
    # side-cars. `read_district` walks `idfs/*.idf` once, keyed by the
    # building id `prepared_buildings.csv` maps each stem to.
    #
    # T01 (FINDING 259): resolve each building's IDF against the EU-11
    # ceiling82 tree first -- the tree that was actually simulated -- and
    # fall back to the EU-17 rebuild tree only where ceiling82 has no file
    # for that id. `idf_root_by_id` remembers which root each plan came
    # from so the idf_path built below (`:1110`, `:1116`) points at the
    # right `idfs/` directory.
    idf_evidence_root = EU17_ROOT / district
    ceiling82_root = EU11_ROOT / f"{district}_ceiling82_2026-09-05"
    plans_by_id: dict[str, BuildingPlan] = {p.building_id: p for p in read_district(district, idf_evidence_root)}
    idf_root_by_id: dict[str, Path] = {bid: idf_evidence_root for bid in plans_by_id}
    for p in read_district(district, ceiling82_root):
        plans_by_id[p.building_id] = p
        idf_root_by_id[p.building_id] = ceiling82_root

    for _tag in ("final_2026-09-07", "delta_2026-09-07"):
        _root = EU11_ROOT / f"{district}_{_tag}"
        if not (_root / "idfs").is_dir():
            continue
        for p in read_district(district, _root, skip_missing=True):
            plans_by_id[p.building_id] = p
            idf_root_by_id[p.building_id] = _root

    # EU-11 ceiling82 manifest EUI, loaded once per district (T01) -- joined
    # on the same `bid` used everywhere else in the `:1007` loop below. A
    # building present in this dict (whether or not its `eui_kwh_m2` is
    # null, e.g. an EnergyPlus severe/fatal-error run) has a manifest row
    # and counts against `population_run`; a building absent from it never
    # got a Speed job at all.
    eui_by_id = _load_eu11_eui(district)

    # EU-21 no-core cutter evidence (checks/status/verdict/scheme), loaded
    # once per district (T03) -- annotation only, joined on the same `bid`,
    # attached to `pl_obj` below (never to a `no_idf` building, rule 3).
    evidence_by_id = _load_eu21_evidence(district)
    chk_hit = chk_miss = 0

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
    ruled_count = massing_count = no_idf_count = 0
    simulated_count = idf_only_count = 0

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

        # Ring coords (footprint; EU-02 real-footprint perimeter, unrelated
        # to the layout side-car dispute rule 3 addresses)
        if i < len(existing_rings):
            ring = existing_rings[i]
        else:
            poly = row.geometry
            if poly.geom_type == "MultiPolygon":
                poly = max(poly.geoms, key=lambda pg: pg.area)
            poly_s = poly.simplify(0.05, preserve_topology=True)
            ring = [[round(pt[0] - cx, 2), round(pt[1] - cy, 2)] for pt in list(poly_s.exterior.coords)[:-1]]

        layout_state: str | None = None
        sim_state: str | None = None
        pl_obj: dict[str, Any] | None = None
        if is_res:
            plan = plans_by_id.get(bid)
            if plan is None or not plan.zones:
                layout_state = "no_idf"
                no_idf_count += 1
            elif plan.is_ruled():
                layout_state = "ruled"
                ruled_count += 1
                idf_path = idf_root_by_id[bid] / "idfs" / f"{plan.stem}.idf"
                sidecar = _load_eu17_sidecar(district, bid)
                pl_obj = _build_plan_payload(plan, idf_path, sidecar, cx, cy)
            else:
                layout_state = "massing_box"
                massing_count += 1
                idf_path = idf_root_by_id[bid] / "idfs" / f"{plan.stem}.idf"
                sidecar = _load_eu17_sidecar(district, bid)
                pl_obj = _build_plan_payload(plan, idf_path, sidecar, cx, cy)

            # T01 (FINDING 259): a fourth, orthogonal state -- was this
            # building actually simulated (has a manifest row in the
            # ceiling82 campaign, `bid in eui_by_id`, which equals
            # `population_run`, not `population_success` -- a severe/fatal
            # E+ error still counts as "run") vs. has an IDF but never got
            # a Speed job vs. no IDF anywhere.
            if layout_state == "no_idf":
                sim_state = "no_idf"
            elif bid in eui_by_id:
                sim_state = "simulated"
                simulated_count += 1
            else:
                sim_state = "idf_only"
                idf_only_count += 1

        if pl_obj is not None:
            evidence = evidence_by_id.get(bid)
            chk_obj: dict[str, Any] | None = None
            if evidence is None:
                chk_miss += 1
            else:
                chk_hit += 1
                if evidence.get("status") == "direct":
                    checks_raw = evidence.get("checks") or {}
                    ch = [
                        [
                            cid,
                            checks_raw.get(cid, {}).get("show", ""),
                            1 if checks_raw.get(cid, {}).get("pass") else 0,
                        ]
                        for cid in CHECK_IDS
                    ]
                    chk_obj = {"v": evidence.get("verdict"), "ch": ch}
            pl_obj["chk"] = chk_obj

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
            "ls": layout_state,
            "ss": sim_state,
            "pl": pl_obj,
            "eui": eui_by_id.get(bid),
        }
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
            "layout_state": layout_state if layout_state is not None else "",
            "storey_count": pl_obj["st"] if pl_obj else "",
            "dwelling_count": pl_obj["dw"] if pl_obj else "",
            "gross_area_m2": pl_obj["gm"] if pl_obj else "",
            "conditioned_area_m2": pl_obj["cm"] if pl_obj else "",
            "circulation_pct": pl_obj["cp"] if pl_obj else "",
        })

    n_res = len(res_gdf)
    n_exc = len(exc_gdf)

    layout_counts = {
        "ruled": ruled_count,
        "massing_box": massing_count,
        "no_idf": no_idf_count,
    }

    # T01 (FINDING 259): the fourth HUD state -- distinguishes "was actually
    # simulated" (`bid in eui_by_id`, ceiling82 tree) from "has an IDF but
    # was never run" (idf_only, EU-17-only fallback) from "no IDF anywhere".
    # `no_idf` is shared with `layout_counts` above -- both now read the
    # same ceiling82-first / EU-17-fallback `plans_by_id`, so "no IDF" means
    # the same population under either axis.
    sim_counts = {
        "simulated": simulated_count,
        "idf_only": idf_only_count,
        "no_idf": no_idf_count,
    }

    geometry_note = (
        f"<b>Geometry for {n_res:,} residential buildings, read from the emitted IDFs "
        f"(EU-11 ceiling82 tree first, EU-17 rebuild tree as fallback).</b> "
        f"{simulated_count:,} were actually simulated (have an EUI, matching "
        f"<code>summary.json</code>'s <code>population_run</code>), {idf_only_count:,} have an "
        f"IDF but were never run, {no_idf_count:,} have no IDF in either tree and are shown grey. "
        f"Of the {simulated_count + idf_only_count:,} with an IDF, {ruled_count:,} carry a dwelling "
        f"layout ruled from their own IDF zones and {massing_count:,} are a massing box (one "
        "undivided zone per storey). Zone polygons drawn in the floor-plan modal come directly "
        "from these IDFs, never from the layout side-cars."
    )

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
        "sim_counts": sim_counts,
        "data_dir": data_dir_name,
        "geometry_note": geometry_note,
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
    print(f"[{district}] EU-21 checks join: {chk_hit} hit, {chk_miss} miss (of {chk_hit + chk_miss} buildings with pl_obj)")

    # Write buildings.csv
    b_df = pd.DataFrame(buildings_csv_rows)
    buildings_csv_path = target_data_dir / "buildings.csv"
    b_df.to_csv(buildings_csv_path, index=False)
    print(f"[{district}] Written buildings.csv: {len(b_df)} rows")

    # Energy side files (results.csv / results_source.csv) are gone entirely
    # -- D-EU-59 forbids any emitted CSV side file carrying EUI/E+ output,
    # and that was their only content.
    for stale in ("results.csv", "results_source.csv"):
        stale_path = target_data_dir / stale
        if stale_path.exists():
            stale_path.unlink()

    # Copy the EU-17 layout side-cars (same rebuild tree the IDFs came from,
    # used only as narrow annotation per rule 3 -- never the EU-11 side-cars
    # this arc's own FINDING 213/215 found disagreeing with the IDFs).
    eu17_layouts_dir = idf_evidence_root / "layouts"
    target_layouts_dir = target_data_dir / "layouts"
    n_sidecars = sum(1 for _ in eu17_layouts_dir.glob("**/*.json")) if eu17_layouts_dir.exists() else 0
    if eu17_layouts_dir.exists() and n_sidecars > 0:
        if target_layouts_dir.exists():
            shutil.rmtree(target_layouts_dir)
        shutil.copytree(eu17_layouts_dir, target_layouts_dir)
        print(f"[{district}] Copied {n_sidecars} EU-17 layout side-cars to {target_layouts_dir}")

    # Construct sources.json
    generated_from = [
        f"openubem/outputs/eu02/{district}/01_source.json",
        f"openubem/outputs/eu02/{district}/02_residential_manifest.gpkg",
        f"openubem/outputs/eu02/{district}/02_excluded_manifest.gpkg",
        f"openubem/outputs/eu_evidence/EU-17/{district}/prepared_buildings.csv",
    ]
    sha256_map = {
        "01_source.json": _file_sha256(src_json_path),
        "02_residential_manifest.gpkg": _file_sha256(res_gpkg_path),
        "02_excluded_manifest.gpkg": _file_sha256(exc_gpkg_path),
        "prepared_buildings.csv": _file_sha256(idf_evidence_root / "prepared_buildings.csv"),
    }

    sources_dict: dict[str, Any] = {
        "cell": district,
        "viewer": viewer_name,
        "generated_from": generated_from,
        "sha256": sha256_map,
        "idf_source_directory": f"openubem/outputs/eu_evidence/EU-17/{district}/idfs",
        "layout_counts": layout_counts,
        "layouts_coverage": (
            f"{ruled_count} dwelling layout ruled, {massing_count} massing box, "
            f"{no_idf_count} no IDF of {n_res} residential"
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
    if target_layouts_dir.exists() and n_sidecars > 0:
        files_list_html.append(f'<li><a href="layouts/">layouts/</a> <span>{n_sidecars} side-car JSON files</span></li>')
    files_list_html.append(f'<li><a href="sources.json">sources.json</a> <span>{_format_file_size(sources_json_path.stat().st_size)}</span></li>')

    callout_html = geometry_note

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
