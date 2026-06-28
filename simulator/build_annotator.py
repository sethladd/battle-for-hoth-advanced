"""Generate the Hoth scenario map-annotation webapp (single self-contained HTML)."""
import pdfplumber, base64, io, json, numpy as np, cv2
from PIL import Image

PDF = 'source/DOWSWB0101_EN_BATTLEOFHOTH_SCENARIO_WEB.pdf'
OUT = '../tools/hoth_map_annotator.html'

R = 150
# Each page is cropped relative to its detected Imperial-cog corner so every board
# lands in an IDENTICAL pixel frame (odd & even pages alike) -> one calibration fits all.
PADX, CW, CH = 44, 500, 364     # crop = (cog_x-PADX, cog_y-47, +CW, +CH) in points
# default grid geometry (POINTY-TOP, odd ROWS offset right). Pixels. User calibrates once.
GEO = dict(x0=180, dx=92, y0=78, dy=82, off=46, cols=10, rows=7)

names = {
 1:'Imperial Scout Mission',2:'Snowspeeder Counter-Attack',3:'Enemy Spotted',
 4:'Successful Landings',5:'Hill Alpha Defense',6:'Retrieve Imperial Data',
 7:'Outpost Attack',8:'Medevac!',9:'Securing Defensive Positions',
 10:'Target the Shield Generators',11:'Rebel Breakout',12:'Under Siege',
 13:'Enter Echo Base',14:'Protect Rebel Transports',15:'South Gate Retreat',
 16:'Echo Base Evacuation',17:'Last Stand'}

# guide rosters (reconstructed from narratives; user corrects against the map)
rosters = {
 1:'R: echo x4  |  E: snowtrooper x4, droid x2',
 2:'R: speeder x3, echo x2  |  E: snowtrooper x5, AT-AT x1',
 3:'R: echo x5, speeder x2  |  E: AT-AT x1, snowtrooper x3, droid x2',
 4:'R: echo x5, speeder x1, artillery x1  |  E: AT-AT x2, snowtrooper x4',
 5:'R: artillery x2, echo x4, speeder x1  |  E: AT-AT x1, snowtrooper x6',
 6:'R: echo x4, speeder x1  |  E: snowtrooper x6, droid x2',
 7:'R: echo x4, artillery x1, speeder x2  |  E: snowtrooper x5, droid x2',
 8:'R: echo x3, speeder x2 (+officer)  |  E: snowtrooper x4, AT-AT x1',
 9:'R: echo x5  |  E: snowtrooper x5 (+E-Web), AT-AT x1',
 10:'R: artillery x2, echo x5, speeder x1 (+2 shield gens)  |  E: AT-AT x2, snowtrooper x3',
 11:'R: echo x6, speeder x1  |  E: snowtrooper x5 (+E-Web), droid x1',
 12:'R: speeder x2, echo x4  |  E: AT-AT x2, snowtrooper x5',
 13:'R: artillery x2, speeder x2, echo x4  |  E: AT-AT x3, snowtrooper x4',
 14:'R: artillery x1, echo x5, speeder x1 (+ion cannon)  |  E: AT-AT x1, snowtrooper x7',
 15:'R: artillery x1, speeder x1, echo x5  |  E: snowtrooper x4, AT-AT x1, droid x1',
 16:'R: echo x5, speeder x1  |  E: AT-AT x1, snowtrooper x6',
 17:'R: artillery x1, echo x6  |  E: snowtrooper x5, AT-AT x1, droid x1, E-Web',
}

pdf = pdfplumber.open(PDF)

# --- detect the Imperial cog (top-left board corner) on each page ---
def _gray(idx, box):
    return np.asarray(pdf.pages[idx].crop(box).to_image(resolution=300).original.convert('L'))
COG = _gray(1, (117, 104, 139, 126))
def find_cog(idx):
    region = _gray(idx, (15, 95, 220, 155))
    res = cv2.matchTemplate(region, COG, cv2.TM_CCOEFF_NORMED)
    _, mx, _, loc = cv2.minMaxLoc(res)
    cx = 15 + (loc[0] + COG.shape[1] / 2) / (300 / 72.0)
    cy = 95 + (loc[1] + COG.shape[0] / 2) / (300 / 72.0)
    return cx, cy, mx

images = {}
W = H = None
for n in range(1, 18):
    cx, cy, conf = find_cog(n)
    crop = (cx - PADX, cy - 47, cx - PADX + CW, cy - 47 + CH)
    im = pdf.pages[n].crop(crop).to_image(resolution=R).original.convert('RGB')
    if W is None:
        W, H = im.size
    elif im.size != (W, H):
        im = im.resize((W, H))   # guarantee identical frame size
    buf = io.BytesIO(); im.save(buf, 'JPEG', quality=72)
    images[n] = base64.b64encode(buf.getvalue()).decode()
    print(f'scn {n:2}: cog=({cx:.0f},{cy:.0f}) conf={conf:.2f} crop_x0={crop[0]:.0f}')
print('img size', W, H)

meta = {str(n): {'name': names[n], 'roster': rosters[n], 'img': images[n]} for n in range(1, 18)}

HTML = r'''<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Battle of Hoth — Scenario Map Annotator</title>
<style>
 body{font-family:system-ui,Arial,sans-serif;margin:0;background:#0d1b2a;color:#e0e6ed}
 header{background:#1b263b;padding:10px 16px;border-bottom:2px solid #415a77}
 h1{font-size:18px;margin:0}
 .sub{font-size:12px;color:#9fb3c8;margin-top:3px}
 .wrap{display:flex;gap:14px;padding:14px;align-items:flex-start;flex-wrap:wrap}
 .left{flex:1;min-width:420px}
 .right{width:320px;background:#1b263b;border-radius:8px;padding:12px;font-size:13px}
 select,button{font-size:13px;padding:5px 8px;border-radius:5px;border:1px solid #415a77;background:#22303f;color:#e0e6ed;cursor:pointer}
 button:hover{background:#2d4257}
 .boardbox{position:relative;width:100%;max-width:860px}
 svg{width:100%;height:auto;display:block;border-radius:6px;background:#000}
 .pal{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin:6px 0 12px}
 .pal button{text-align:left;font-size:12px;padding:6px}
 .pal button.sel{outline:3px solid #ffd166;background:#34495e}
 .seclabel{font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:#9fb3c8;margin:8px 0 3px}
 .roster{background:#22303f;border-radius:6px;padding:8px;font-size:12px;line-height:1.5}
 textarea{width:100%;height:120px;background:#0d1b2a;color:#9fb3c8;border:1px solid #415a77;border-radius:6px;font-family:monospace;font-size:11px}
 .hint{font-size:11px;color:#9fb3c8;margin:4px 0}
 .count{font-size:11px;color:#ffd166}
 circle.hx{fill:transparent;stroke:rgba(255,255,255,.12);stroke-width:1;cursor:pointer}
 circle.hx:hover{stroke:#ffd166;stroke-width:2}
</style></head><body>
<header>
 <h1>Battle of Hoth — Scenario Map Annotator</h1>
 <div class="sub">Click a hex to place the selected token. Click the same hex again to clear that layer. Row 0 (top) = Empire baseline. Export sends the data back to Claude.</div>
</header>
<div class="wrap">
 <div class="left">
   <div style="margin-bottom:8px">
     <label>Scenario:
       <select id="scn"></select></label>
     &nbsp; <button onclick="prevS()">◀ Prev</button>
     <button onclick="nextS()">Next ▶</button>
     &nbsp; <label><input type="checkbox" id="lbls" onchange="render()"> show hex labels</label>
     &nbsp; <span id="hx" style="color:#ffd166;font-size:12px"></span>
   </div>
   <div class="boardbox">
     <svg id="ov" viewBox="0 0 ''' + str(W) + ' ' + str(H) + r'''"></svg>
   </div>
   <div class="roster" id="roster"></div>
 </div>
 <div class="right">
   <div class="seclabel">Brush</div>
   <div class="pal" id="pal"></div>
   <div class="seclabel">Actions</div>
   <button onclick="startCalib()" style="width:100%;margin-bottom:6px;background:#e76f51">🎯 Calibrate grid (4 clicks)</button>
   <div class="hint">If the hex ring doesn't track the hexes, click Calibrate and follow the prompt (top of board). Calibrate once — it's saved for every scenario.</div>
   <button onclick="clearScn()" style="width:100%;margin:6px 0">Clear this scenario</button>
   <button onclick="doExport()" style="width:100%;margin-bottom:6px;background:#2a9d8f">⤓ Export ALL (download + copy)</button>
   <div class="hint">After export, paste the text below into the chat, OR save the downloaded file into the project folder.</div>
   <textarea id="out" placeholder="exported JSON appears here"></textarea>
   <div class="seclabel">Resume previous work</div>
   <div class="hint">Paste a previous export and click Load.</div>
   <button onclick="doImport()" style="width:100%">⤴ Load from text above</button>
 </div>
</div>
<script>
let GEO=''' + json.dumps(GEO) + r''';
try{const g=localStorage.getItem('hothgeo2'); if(g)GEO=JSON.parse(g);}catch(e){}
const META=''' + json.dumps(meta) + r''';
const PALETTE=[
 {k:'echo',     lay:'unit',side:'rebel', c:'#e63946',t:'Rebel Trooper'},
 {k:'speeder',  lay:'unit',side:'rebel', c:'#ff7b00',t:'Rebel Snowspeeder'},
 {k:'tauntaun', lay:'unit',side:'rebel', c:'#e9a23b',t:'Tauntaun Scout'},
 {k:'artillery',lay:'unit',side:'rebel', c:'#c1121f',t:'Rebel Artillery'},
 {k:'snowtroop',lay:'unit',side:'empire',c:'#4895ef',t:'Snowtrooper'},
 {k:'atat',     lay:'unit',side:'empire',c:'#3a0ca3',t:'AT-AT'},
 {k:'atst',     lay:'unit',side:'empire',c:'#5566aa',t:'AT-ST Walker'},
 {k:'droid',    lay:'unit',side:'empire',c:'#4361ee',t:'Probe Droid'},
 {k:'eweb',     lay:'unit',side:'empire',c:'#7209b7',t:'E-Web (snowtrooper)'},
 {k:'rocks',    lay:'terr',c:'#8d99ae',t:'Rocks'},
 {k:'ridge',    lay:'terr',c:'#a8dadc',t:'Ridge'},
 {k:'trenches', lay:'terr',c:'#b5838d',t:'Trenches'},
 {k:'buildings',lay:'terr',c:'#6c757d',t:'Buildings'},
 {k:'wreckage', lay:'terr',c:'#9c6644',t:'Wreckage'},
 {k:'crevasse', lay:'terr',c:'#1d3557',t:'Crevasse'},
 {k:'serac',    lay:'terr',c:'#caf0f8',t:'Serac'},
 {k:'shieldgen',lay:'mark',c:'#06d6a0',t:'Shield Generator'},
 {k:'ioncannon',lay:'mark',c:'#ef476f',t:'Ion Cannon'},
 {k:'objective',lay:'mark',c:'#ffd166',t:'Objective / medal hex'},
 {k:'exit',     lay:'mark',c:'#00b4d8',t:'Exit hex'},
 {k:'leader_luke', lay:'mark',c:'#ffd700',t:'★ Leader: Luke (on this unit)'},
 {k:'leader_han',  lay:'mark',c:'#ffd700',t:'★ Leader: Han (on this unit)'},
 {k:'leader_leia', lay:'mark',c:'#ffd700',t:'★ Leader: Leia (on this unit)'},
 {k:'leader_vader',lay:'mark',c:'#ff4d4d',t:'★ Leader: Vader (on this unit)'},
 {k:'leader_veers',lay:'mark',c:'#ff4d4d',t:'★ Leader: Veers (on this unit)'},
];
let cur='1', brush=PALETTE[0];
let calib=null;
const CALSTEPS=[
 'TOP-LEFT hex  (col 0, row 0)',
 'TOP-RIGHT hex (col 9, row 0)',
 'BOTTOM-LEFT hex (col 0, row 6)',
 'LEFTMOST hex of the SECOND row (col 0, row 1) — the inset one'];
function startCalib(){calib=[];showCalib();render();}
function showCalib(){document.getElementById('hx').textContent=
 'CALIBRATE — click the center of: '+CALSTEPS[calib.length];}
function calibClick(x,y){calib.push([x,y]);
 if(calib.length<4){showCalib();render();return;}
 const [p00,p90,p06,p01]=calib;
 GEO={cols:10,rows:7,
   x0:p00[0], dx:(p90[0]-p00[0])/9,
   y0:p00[1], dy:(p06[1]-p00[1])/6, off:(p01[0]-p00[0])};
 try{localStorage.setItem('hothgeo2',JSON.stringify(GEO));}catch(e){}
 calib=null;document.getElementById('hx').textContent='Calibrated ✓ (saved for all scenarios)';
 render();}
// state[scn][ "c,r" ] = {unit:{k,side}, terr:k, mark:k}
let state={};
function valid(c,r){return c>=0 && r>=0 && r<GEO.rows && ((r%2)? c<GEO.cols-1 : c<GEO.cols);}
function ctr(c,r){return [GEO.x0+GEO.dx*c+((r%2)?GEO.off:0), GEO.y0+GEO.dy*r];}
function load(){try{const s=localStorage.getItem('hothann'); if(s)state=JSON.parse(s);}catch(e){}}
function save(){try{localStorage.setItem('hothann',JSON.stringify(state));}catch(e){}}
function cellOf(scn){state[scn]=state[scn]||{}; return state[scn];}

function buildPal(){const p=document.getElementById('pal');p.innerHTML='';
 PALETTE.forEach((it,i)=>{const b=document.createElement('button');
  b.innerHTML='<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:'+it.c+';margin-right:5px"></span>'+it.t;
  b.onclick=()=>{brush=it;[...p.children].forEach(x=>x.classList.remove('sel'));b.classList.add('sel');};
  if(i==0)b.classList.add('sel');p.appendChild(b);});}

function buildSel(){const s=document.getElementById('scn');s.innerHTML='';
 for(let n=1;n<=17;n++){const o=document.createElement('option');o.value=n;o.text=n+'. '+META[n].name;s.appendChild(o);}
 s.onchange=()=>{cur=s.value;render();};}

const IMGW=''' + str(W) + r''', IMGH=''' + str(H) + r''';
function svgXY(evt){const svg=document.getElementById('ov');const pt=svg.createSVGPoint();
 pt.x=evt.clientX;pt.y=evt.clientY;const p=pt.matrixTransform(svg.getScreenCTM().inverse());return [p.x,p.y];}
function nearest(x,y){let bc=0,br=0,bd=1e18;
 for(let c=0;c<GEO.cols;c++)for(let r=0;r<GEO.rows;r++){if(!valid(c,r))continue;const [cx,cy]=ctr(c,r);
   const d=(x-cx)*(x-cx)+(y-cy)*(y-cy); if(d<bd){bd=d;bc=c;br=r;}} return [bc,br];}
function hover(c,r){const ov=document.getElementById('ov');let h=document.getElementById('hoverring');
 const NS='http://www.w3.org/2000/svg';
 if(!h){h=document.createElementNS(NS,'circle');h.id='hoverring';h.setAttribute('r',26);
  h.setAttribute('fill','rgba(255,209,102,.18)');h.setAttribute('stroke','#ffd166');h.setAttribute('stroke-width','3');
  h.style.pointerEvents='none';ov.appendChild(h);}
 const [x,y]=ctr(c,r);h.setAttribute('cx',x);h.setAttribute('cy',y);
 document.getElementById('hx').textContent='hex '+c+','+r;}
function render(){
 const cells=cellOf(cur);
 const ov=document.getElementById('ov');ov.innerHTML='';
 const showL=document.getElementById('lbls').checked;
 const NS='http://www.w3.org/2000/svg';
 // background board image lives INSIDE the svg => one coordinate system
 const img=document.createElementNS(NS,'image');
 img.setAttributeNS('http://www.w3.org/1999/xlink','href','data:image/jpeg;base64,'+META[cur].img);
 img.setAttribute('href','data:image/jpeg;base64,'+META[cur].img);
 img.setAttribute('x',0);img.setAttribute('y',0);img.setAttribute('width',IMGW);img.setAttribute('height',IMGH);
 ov.appendChild(img);
 ov.onclick=(e)=>{const [x,y]=svgXY(e); if(calib){calibClick(x,y);return;} const [c,r]=nearest(x,y);place(c,r);};
 ov.onmousemove=(e)=>{const [x,y]=svgXY(e); if(calib){return;} const [c,r]=nearest(x,y);hover(c,r);};
 const cnt={};
 for(let c=0;c<GEO.cols;c++)for(let r=0;r<GEO.rows;r++){
   if(!valid(c,r))continue;
   const [x,y]=ctr(c,r); const key=c+','+r; const cell=cells[key]||{};
   const dot=document.createElementNS(NS,'circle');
   dot.setAttribute('cx',x);dot.setAttribute('cy',y);dot.setAttribute('r',3);
   dot.setAttribute('fill','rgba(255,255,255,.35)');dot.style.pointerEvents='none';ov.appendChild(dot);
   if(cell.terr){const it=PALETTE.find(p=>p.k==cell.terr);
     const h=document.createElementNS(NS,'circle');h.setAttribute('cx',x);h.setAttribute('cy',y);
     h.setAttribute('r',GEO.dx/2.3);h.setAttribute('fill',it.c);h.setAttribute('fill-opacity','.35');
     h.setAttribute('stroke',it.c);h.setAttribute('stroke-width','2');h.style.pointerEvents='none';ov.appendChild(h);}
   if(cell.mark){const it=PALETTE.find(p=>p.k==cell.mark);
     const lead=cell.mark.indexOf('leader_')==0;
     const m=document.createElementNS(NS,'rect');m.setAttribute('x',x-16);m.setAttribute('y',y-16);
     m.setAttribute('width',32);m.setAttribute('height',32);m.setAttribute('fill','none');
     m.setAttribute('stroke',it.c);m.setAttribute('stroke-width','3');m.setAttribute('rx',lead?16:3);m.style.pointerEvents='none';ov.appendChild(m);
     const lbl={objective:'OBJ',exit:'EXIT',shieldgen:'SHLD',ioncannon:'ION',
       leader_luke:'★L',leader_han:'★H',leader_leia:'★Le',leader_vader:'★V',leader_veers:'★Ve'}[cell.mark]||'';
     if(lbl){const t=document.createElementNS(NS,'text');t.setAttribute('x',x);t.setAttribute('y',y-19);
       t.setAttribute('text-anchor','middle');t.setAttribute('font-size','13');t.setAttribute('font-weight','bold');
       t.setAttribute('fill',it.c);t.setAttribute('stroke','#000');t.setAttribute('stroke-width','.5');t.style.pointerEvents='none';t.textContent=lbl;ov.appendChild(t);}}
   if(cell.unit){const it=PALETTE.find(p=>p.k==cell.unit.k);
     const u=document.createElementNS(NS,'circle');u.setAttribute('cx',x);u.setAttribute('cy',y);
     u.setAttribute('r',13);u.setAttribute('fill',it.c);u.setAttribute('stroke','#fff');u.setAttribute('stroke-width','2');
     u.style.pointerEvents='none';ov.appendChild(u);
     const tx=document.createElementNS(NS,'text');tx.setAttribute('x',x);tx.setAttribute('y',y+4);
     tx.setAttribute('text-anchor','middle');tx.setAttribute('font-size','12');tx.setAttribute('fill','#fff');
     tx.style.pointerEvents='none';tx.textContent=it.k[0].toUpperCase();ov.appendChild(tx);
     cnt[it.k]=(cnt[it.k]||0)+1;}
   if(showL){const t=document.createElementNS(NS,'text');t.setAttribute('x',x);t.setAttribute('y',y-14);
     t.setAttribute('text-anchor','middle');t.setAttribute('font-size','9');t.setAttribute('fill','rgba(255,255,255,.5)');
     t.style.pointerEvents='none';t.textContent=c+','+r;ov.appendChild(t);}
 }
 if(calib){calib.forEach((p,i)=>{const g=document.createElementNS(NS,'circle');
   g.setAttribute('cx',p[0]);g.setAttribute('cy',p[1]);g.setAttribute('r',10);
   g.setAttribute('fill','#39ff14');g.setAttribute('stroke','#000');g.style.pointerEvents='none';ov.appendChild(g);
   const t=document.createElementNS(NS,'text');t.setAttribute('x',p[0]);t.setAttribute('y',p[1]-12);
   t.setAttribute('text-anchor','middle');t.setAttribute('fill','#39ff14');t.setAttribute('font-size','16');
   t.style.pointerEvents='none';t.textContent=(i+1);ov.appendChild(t);});}
 let placed=Object.entries(cnt).map(([k,v])=>k+'×'+v).join(', ')||'(nothing placed yet)';
 document.getElementById('roster').innerHTML='<b>Booklet roster (guide):</b> '+META[cur].roster+
   '<br><span class="count">Placed: '+placed+'</span>';
 document.getElementById('scn').value=cur;
}
function place(c,r){const cells=cellOf(cur);const key=c+','+r;const cell=cells[key]||{};
 if(brush.lay=='unit'){ if(cell.unit&&cell.unit.k==brush.k)delete cell.unit; else cell.unit={k:brush.k,side:brush.side}; }
 else if(brush.lay=='terr'){ if(cell.terr==brush.k)delete cell.terr; else cell.terr=brush.k; }
 else { if(cell.mark==brush.k)delete cell.mark; else cell.mark=brush.k; }
 if(Object.keys(cell).length)cells[key]=cell; else delete cells[key];
 save();render();}
function prevS(){if(+cur>1){cur=''+(+cur-1);render();}}
function nextS(){if(+cur<17){cur=''+(+cur+1);render();}}
function clearScn(){if(confirm('Clear all placements for scenario '+cur+'?')){state[cur]={};save();render();}}
function doExport(){const data={_geo:GEO};for(const s in state){data[s]={units:[],terrain:[],markers:[]};
  for(const key in state[s]){const [c,r]=key.split(',').map(Number);const cell=state[s][key];
    if(cell.unit)data[s].units.push({kind:cell.unit.k,side:cell.unit.side,col:c,row:r});
    if(cell.terr)data[s].terrain.push({type:cell.terr,col:c,row:r});
    if(cell.mark)data[s].markers.push({type:cell.mark,col:c,row:r});}}
 const txt=JSON.stringify(data,null,1);document.getElementById('out').value=txt;
 try{navigator.clipboard.writeText(txt);}catch(e){}
 const blob=new Blob([txt],{type:'application/json'});const a=document.createElement('a');
 a.href=URL.createObjectURL(blob);a.download='hoth_scenario_positions.json';a.click();}
function doImport(){try{state=JSON.parse(document.getElementById('out').value)&&convertIn(document.getElementById('out').value);save();render();alert('Loaded.');}catch(e){alert('Could not parse: '+e);}}
function convertIn(txt){const d=JSON.parse(txt);const st={};
 if(d._geo){GEO=d._geo;try{localStorage.setItem('hothgeo2',JSON.stringify(GEO));}catch(e){}}
 for(const s in d){if(!/^[0-9]+$/.test(s))continue;st[s]={};const o=d[s];
   (o.units||[]).forEach(u=>{const k=u.col+','+u.row;st[s][k]=st[s][k]||{};st[s][k].unit={k:u.kind,side:u.side};});
   (o.terrain||[]).forEach(u=>{const k=u.col+','+u.row;st[s][k]=st[s][k]||{};st[s][k].terr=u.type;});
   (o.markers||[]).forEach(u=>{const k=u.col+','+u.row;st[s][k]=st[s][k]||{};st[s][k].mark=u.type;});}
 return st;}
load();buildPal();buildSel();render();
</script></body></html>'''

with open(OUT, 'w') as f:
    f.write(HTML)
import os
print('wrote', OUT, round(os.path.getsize(OUT)/1024), 'KB')
