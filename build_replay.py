"""Generate a self-contained HTML replay viewer for one simulated Battle of Hoth game."""
import json, sys, importlib
import hoth_engine, hoth_sim, hoth_scenarios
for m in (hoth_engine, hoth_sim, hoth_scenarios):
    importlib.reload(m)
import hoth_sim as S, hoth_scenarios as HS

SCN = int(sys.argv[1]) if len(sys.argv) > 1 else 1
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 7
RLEAD = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != '-' else None
ELEAD = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != '-' else None
OUT = '/sessions/gracious-admiring-mccarthy/mnt/BattleForHothAdvanced/hoth_game_replay.html'

POS = json.load(open('hoth_scenario_positions.json'))
annot = POS.get(str(SCN))
scn = HS.SCENARIOS[SCN]
res = S.play_game(seed=SEED, basic=False, scenario=scn, annot=annot,
                  rebel_leader=RLEAD, emp_leader=ELEAD, record=True)

CARD_TEXT = {
 # section cards (shared)
 'Recon Probe': 'Order 2 units in one section.',
 'Sector Assault': 'Order 3 units in one section.',
 'General Advance': 'Order ALL units in one section.',
 'Recon in Force': 'Order 1 unit in each section (left, center, right).',
 'Pincer Movement': 'Order 2 units in each flank (left and right).',
 'Coordinated Command': 'Order up to 4 units anywhere on the board.',
 'Grand Offensive': 'Order ALL units in one flank; they gain +1 movement.',
 # rebel tactics
 'Speeder Strike': 'Order up to 2 Snowspeeders; each may move 1 hex AFTER attacking (hit-and-run).',
 'Trench Fighting': 'Order up to 3 infantry; +1 attack die and ignore terrain attack penalties.',
 'Artillery Barrage': 'Order 1 artillery unit; it attacks twice.',
 'Focus Fire': 'Order up to 3 units; +1 die for each unit after the first to attack the SAME target.',
 'Desperate Valor': 'Order up to 2 units; +1 die for each medal the enemy has scored (max +3).',
 'Forward Command': 'Order 1 unit; draw 2 extra command cards.',
 'Regroup': 'Order up to 2 units; each ordered unit that does not attack returns 1 lost figure.',
 'Evasive Maneuvers': 'REACTION — when an enemy attacks your Snowspeeder, it first moves 1 hex (dodge).',
 'Ambush': 'REACTION — when an enemy ends its move adjacent to your unit, that unit attacks at once.',
 # imperial tactics
 'Armored Advance': 'Order up to 2 AT-AT units; +1 movement and +1 close-combat die.',
 'Trooper Assault': 'Order up to 3 infantry; +1 attack die.',
 'Concentrated Fire': 'Order up to 3 units; 2nd to hit the same target +1 die, 3rd +2 dice.',
 'Hold the Line': 'Order up to 3 units; they may not move but gain +1 close-combat die.',
 'Probe Recon': 'Order up to 2 probe droids; +1 movement; allies +1 die vs targets a droid can see.',
 'Crush Them': 'Order up to 3 units; +1 die for each enemy unit below half strength (max +3).',
 'Suppressing Fire': 'REACTION — when an enemy attacks your infantry in cover, attacker rolls 1 fewer die.',
 'Imperial Ambush': 'REACTION — when an enemy ends its move adjacent to your unit, that unit attacks at once.',
 # leaders
 'Coordinated Defense': '[Leia] Order up to 3 units; non-attacking units return 1 figure.',
 'New Hope': '[Leia] Order up to 4 units; +1 attack die.',
 'Deploy the Fleet': '[Leia] Order 1 unit; draw 3 extra command cards.',
 'Force Push': '[Luke] Order 1 unit; on its attack, retreats also count as hits.',
 'Trust Your Feelings': '[Luke] Order up to 2 units; +1 die and reroll missed dice.',
 'Heroic Resolve': '[Luke] Order 1 unit; it attacks twice.',
 'Never Tell Me the Odds': '[Han] Order 2 units in different sections; +2 movement.',
 'Surprise Attack': '[Han] Order 1 unit; it may move its full distance and still attack, +1 die.',
 'Covering Fire': '[Han] Order up to 3 units; focus fire (+1 die per extra attacker on a target).',
 'Force Choke': '[Vader] Order 1 unit; +1 die and retreats also count as hits.',
 'Lack of Faith': '[Vader] Order up to 2 units; +1 die; the enemy may play no reactions this turn.',
 'Power of the Dark Side': '[Vader] Order 1 unit; it attacks twice with +1 die.',
 'Concentrate All Fire': '[Veers] Order 1 AT-AT; it attacks twice.',
 'Maximum Firepower': '[Veers] Order up to 2 vehicles; +1 die and +1 movement.',
 'Break Their Lines': '[Veers] Order up to 3 units; each may move 1 hex after attacking (breakthrough).',
 'Orbital Bombardment': '[Piett] Roll 2 dice against each of up to 3 enemy units (ignores cover & LOS).',
 'Tactical Redeployment': '[Piett] Order up to 4 units; +1 movement.',
 'Special Orders': '[Piett] Order 1 unit; draw 2 extra command cards.',
 'Initial deployment': 'Starting positions from the scenario setup.',
}

replay = dict(
    scenario=SCN, name=scn.name, first=scn.first,
    win_targets=res['win_targets'], winner=res['winner'],
    rules=scn.rules_text, terrain=res['terrain'], frames=res['frames'],
    card_text=CARD_TEXT)
print(f'scenario {SCN} "{scn.name}" seed {SEED}: winner={res["winner"]} '
      f'medals R{res["medals"]["rebel"]}/E{res["medals"]["empire"]} frames={len(res["frames"])}')

DATA = json.dumps(replay)

HTML = r'''<!DOCTYPE html><html><head><meta charset="utf-8"><title>Battle of Hoth — Game Replay</title>
<style>
 body{margin:0;font-family:system-ui,Arial,sans-serif;background:#0b1622;color:#e6edf3}
 header{background:#13243a;padding:9px 16px;border-bottom:2px solid #2b4a6f}
 h1{font-size:17px;margin:0}.sub{font-size:12px;color:#9fb3c8;margin-top:2px}
 .wrap{display:flex;gap:14px;padding:14px;flex-wrap:wrap}
 .board{flex:1;min-width:560px;max-width:820px}
 svg{width:100%;height:auto;background:#0e2233;border-radius:8px}
 .side{width:320px;background:#13243a;border-radius:8px;padding:12px}
 .ctl{display:flex;gap:6px;align-items:center;margin:10px 0;flex-wrap:wrap}
 button{font-size:14px;padding:6px 11px;border-radius:6px;border:1px solid #2b4a6f;background:#1d3a5c;color:#e6edf3;cursor:pointer}
 button:hover{background:#27507d}
 input[type=range]{vertical-align:middle}
 .medbar{display:flex;justify-content:space-between;font-size:13px;margin:6px 0}
 .reb{color:#ff6b6b}.emp{color:#74b9ff}
 .card{font-size:15px;font-weight:bold;margin:6px 0;padding:6px 8px;border-radius:6px;background:#1d3a5c}
 .log{font-size:12px;line-height:1.55;max-height:340px;overflow:auto;background:#0e2233;border-radius:6px;padding:8px}
 .face{display:inline-block;width:16px;height:16px;line-height:16px;text-align:center;border-radius:3px;font-size:10px;font-weight:bold;margin:0 1px;color:#000}
 .f-inf{background:#9be09b}.f-veh{background:#9bc6e0}.f-blast{background:#ffd166}.f-retreat{background:#ff9b9b}.f-miss{background:#5a6b7a;color:#cfd8e0}
 .kill{color:#ffd166}
 .pill{display:inline-block;padding:1px 6px;border-radius:9px;font-size:11px;font-weight:bold}
 .hands{display:flex;gap:10px;padding:0 14px 14px}
 .handcol{flex:1;background:#13243a;border-radius:8px;padding:10px}
 .handcol h3{margin:0 0 6px;font-size:13px}
 .chip{display:inline-block;margin:3px;padding:4px 8px;border-radius:6px;font-size:11px;background:#1d3a5c;border:1px solid #2b4a6f}
 .chip.played{background:#ffd166;color:#10243a;font-weight:bold;border-color:#ffd166}
 .chip.react{border-style:dashed;color:#9fb3c8}
</style></head><body>
<header><h1>Battle of Hoth — Simulator Replay</h1>
<div class="sub" id="subt"></div></header>
<div class="wrap">
 <div class="board"><svg id="bd" viewBox="0 0 720 470"></svg>
   <div class="ctl">
     <button onclick="step(-1)">◀ Prev</button>
     <button id="play" onclick="toggle()">▶ Play</button>
     <button onclick="step(1)">Next ▶</button>
     <input type="range" id="sl" min="0" value="0" oninput="goto(+this.value)" style="flex:1">
     <span id="fno" style="font-size:12px"></span>
     speed <input type="range" id="spd" min="200" max="1600" value="700" step="100">
   </div>
 </div>
 <div class="side">
   <div class="medbar"><span class="reb" id="mr"></span><span class="emp" id="me"></span></div>
   <div class="card" id="cardx"></div>
   <div id="cardtext" style="font-size:12px;color:#cfe3ff;background:#0e2233;border-left:3px solid #5aa0e0;padding:6px 9px;border-radius:4px;margin:-2px 0 10px"></div>
   <div style="font-size:11px;color:#9fb3c8;margin-bottom:4px">Turn events</div>
   <div class="log" id="log"></div>
   <div style="font-size:11px;color:#9fb3c8;margin-top:10px" id="rules"></div>
 </div>
</div>
<div class="hands">
 <div class="handcol"><h3 class="reb">Rebel hand</h3><div id="handR"></div></div>
 <div class="handcol"><h3 class="emp">Empire hand</h3><div id="handE"></div></div>
</div>
<script>
const R=__DATA__;
const NS='http://www.w3.org/2000/svg';
// display geometry: engine row 0 = Rebel baseline (bottom); row 6 = Empire (top)
const X0=58,DX=66,OFF=33,Y0=46,DY=58,HR=30;
function valid(c,r){return (r%2)? c<9 : c<10;}
function cx(c,r){return X0+DX*c+((r%2)?OFF:0);}
function cy(c,r){return Y0+DY*(6-r);}   // flip so row6 on top
function hexPts(x,y){let p='';for(let i=0;i<6;i++){const a=Math.PI/180*(60*i-90);p+=(x+HR*Math.cos(a))+','+(y+HR*Math.sin(a))+' ';}return p;}
function starPts(x,y,ro,ri,n){let p='';for(let i=0;i<n*2;i++){const r=i%2?ri:ro;const a=Math.PI/n*i-Math.PI/2;p+=(x+r*Math.cos(a))+','+(y+r*Math.sin(a))+' ';}return p;}
function impact(bd,c,r,hits){const x=cx(c,r),y=cy(c,r);
 const s=document.createElementNS(NS,'polygon');s.setAttribute('points',starPts(x,y,26,11,12));
 s.setAttribute('fill','rgba(255,70,70,.55)');s.setAttribute('stroke','#ff3b3b');s.setAttribute('stroke-width','2');bd.appendChild(s);
 const t=document.createElementNS(NS,'text');t.setAttribute('x',x);t.setAttribute('y',y-22);t.setAttribute('text-anchor','middle');
 t.setAttribute('font-size','15');t.setAttribute('font-weight','bold');t.setAttribute('fill','#ff5b5b');t.setAttribute('stroke','#000');t.setAttribute('stroke-width','.6');
 t.textContent='-'+hits+' HIT'+(hits>1?'S':'');bd.appendChild(t);}
function miss(bd,c,r){const x=cx(c,r),y=cy(c,r);
 const ring=document.createElementNS(NS,'circle');ring.setAttribute('cx',x);ring.setAttribute('cy',y);ring.setAttribute('r',22);
 ring.setAttribute('fill','none');ring.setAttribute('stroke','#9fb3c8');ring.setAttribute('stroke-width','2');ring.setAttribute('stroke-dasharray','3 4');ring.setAttribute('opacity','.85');bd.appendChild(ring);
 const t=document.createElementNS(NS,'text');t.setAttribute('x',x);t.setAttribute('y',y-22);t.setAttribute('text-anchor','middle');
 t.setAttribute('font-size','13');t.setAttribute('font-weight','bold');t.setAttribute('fill','#cfd8e0');t.setAttribute('stroke','#000');t.setAttribute('stroke-width','.6');t.textContent='MISS';bd.appendChild(t);}
function ko(bd,c,r){const x=cx(c,r),y=cy(c,r);
 const s=document.createElementNS(NS,'polygon');s.setAttribute('points',starPts(x,y,30,13,14));
 s.setAttribute('fill','rgba(255,209,102,.85)');s.setAttribute('stroke','#ff8c00');s.setAttribute('stroke-width','2.5');bd.appendChild(s);
 const t=document.createElementNS(NS,'text');t.setAttribute('x',x);t.setAttribute('y',y+5);t.setAttribute('text-anchor','middle');
 t.setAttribute('font-size','14');t.setAttribute('font-weight','bold');t.setAttribute('fill','#7a2e00');t.textContent='KO';bd.appendChild(t);}
const TCOL={open:'#16334d',rocks:'#5b6b7b',ridge:'#6b8ea0',trenches:'#7a5a64',buildings:'#4a4a52',wreckage:'#6e4a33',crevasse:'#0a1a2a',serac:'#bfe6f5',structure:'#7a3a52'};
const TLAB={rocks:'rk',ridge:'rg',trenches:'tr',buildings:'bd',wreckage:'wr',crevasse:'cv',serac:'sr',structure:'st'};
const UCOL={rebel:'#c0392b',empire:'#274472'};
const UK={echo:'T',speeder:'S',tauntaun:'Tn',artillery:'A',snowtroop:'T',atat:'W',atst:'St',droid:'D',eweb:'E',vader:'V',shieldgen:'SG',ioncannon:'IC'};
let terr={}; R.terrain.forEach(t=>terr[t.col+','+t.row]=t.type);
let i=0, timer=null;
function draw(){
 const f=R.frames[i]; const bd=document.getElementById('bd'); bd.innerHTML='';
 // hexes + terrain
 for(let c=0;c<10;c++)for(let r=0;r<7;r++){if(!valid(c,r))continue;
   const x=cx(c,r),y=cy(c,r); const tp=terr[c+','+r]||'open';
   const pg=document.createElementNS(NS,'polygon'); pg.setAttribute('points',hexPts(x,y));
   pg.setAttribute('fill',TCOL[tp]); pg.setAttribute('stroke','#2b4a6f'); pg.setAttribute('stroke-width','1'); bd.appendChild(pg);
   if(TLAB[tp]){const t=document.createElementNS(NS,'text');t.setAttribute('x',x);t.setAttribute('y',y+HR-6);
     t.setAttribute('text-anchor','middle');t.setAttribute('font-size','9');t.setAttribute('fill','#cdd9e5');t.textContent=TLAB[tp];bd.appendChild(t);}
 }
 // arrowhead marker (defined once)
 const defs=document.createElementNS(NS,'defs');
 defs.innerHTML='<marker id="ah" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#9be09b"/></marker>'
   +'<marker id="ahr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#ff7a7a"/></marker>';
 bd.appendChild(defs);
 // event overlays (move trails, attack lines)
 (f.events||[]).forEach(e=>{
   if(e.type=='move'){const a=e.frm,b=e.to;
     // ghost at origin + arrow to destination
     const gh=document.createElementNS(NS,'circle');gh.setAttribute('cx',cx(a[0],a[1]));gh.setAttribute('cy',cy(a[0],a[1]));
     gh.setAttribute('r',16);gh.setAttribute('fill','none');gh.setAttribute('stroke',e.side=='rebel'?'#ff8c7a':'#9ec5ff');
     gh.setAttribute('stroke-width','2');gh.setAttribute('stroke-dasharray','3 3');gh.setAttribute('opacity','.7');bd.appendChild(gh);
     const ln=document.createElementNS(NS,'line');ln.setAttribute('x1',cx(a[0],a[1]));ln.setAttribute('y1',cy(a[0],a[1]));
     ln.setAttribute('x2',cx(b[0],b[1]));ln.setAttribute('y2',cy(b[0],b[1]));
     ln.setAttribute('stroke','#9be09b');ln.setAttribute('stroke-width','2.5');ln.setAttribute('marker-end','url(#ah)');ln.setAttribute('opacity','.85');bd.appendChild(ln);}
   if(e.type=='retreat'){const a=e.frm,b=e.to;
     const gh=document.createElementNS(NS,'circle');gh.setAttribute('cx',cx(a[0],a[1]));gh.setAttribute('cy',cy(a[0],a[1]));
     gh.setAttribute('r',16);gh.setAttribute('fill','none');gh.setAttribute('stroke','#ff7a7a');gh.setAttribute('stroke-width','2');gh.setAttribute('stroke-dasharray','3 3');gh.setAttribute('opacity','.7');bd.appendChild(gh);
     const ln=document.createElementNS(NS,'line');ln.setAttribute('x1',cx(a[0],a[1]));ln.setAttribute('y1',cy(a[0],a[1]));
     ln.setAttribute('x2',cx(b[0],b[1]));ln.setAttribute('y2',cy(b[0],b[1]));
     ln.setAttribute('stroke','#ff7a7a');ln.setAttribute('stroke-width','2.5');ln.setAttribute('marker-end','url(#ahr)');ln.setAttribute('opacity','.9');bd.appendChild(ln);}
   if(e.type=='attack'){const a=e.from,b=e.to;
     const ln=document.createElementNS(NS,'line');ln.setAttribute('x1',cx(a[0],a[1]));ln.setAttribute('y1',cy(a[0],a[1]));
     ln.setAttribute('x2',cx(b[0],b[1]));ln.setAttribute('y2',cy(b[0],b[1]));
     ln.setAttribute('stroke',e.hits>0?'#ffd166':'#5a6b7a');ln.setAttribute('stroke-width','2');ln.setAttribute('stroke-dasharray','4 3');bd.appendChild(ln);
   }
 });
 // units
 f.units.forEach(u=>{const x=cx(u.col,u.row),y=cy(u.col,u.row);
   const g=document.createElementNS(NS,'circle');g.setAttribute('cx',x);g.setAttribute('cy',y);g.setAttribute('r',19);
   g.setAttribute('fill',UCOL[u.side]);g.setAttribute('stroke',u.side=='rebel'?'#ff8c7a':'#9ec5ff');g.setAttribute('stroke-width','2.5');bd.appendChild(g);
   const t=document.createElementNS(NS,'text');t.setAttribute('x',x);t.setAttribute('y',y-2);t.setAttribute('text-anchor','middle');
   t.setAttribute('font-size','13');t.setAttribute('font-weight','bold');t.setAttribute('fill','#fff');t.textContent=UK[u.kind];bd.appendChild(t);
   const n=document.createElementNS(NS,'text');n.setAttribute('x',x);n.setAttribute('y',y+12);n.setAttribute('text-anchor','middle');
   n.setAttribute('font-size','11');n.setAttribute('fill','#ffe');n.textContent='x'+u.figs;bd.appendChild(n);
   if(u.leader){const ring=document.createElementNS(NS,'circle');ring.setAttribute('cx',x);ring.setAttribute('cy',y);
     ring.setAttribute('r',23);ring.setAttribute('fill','none');ring.setAttribute('stroke','#ffd700');ring.setAttribute('stroke-width','3');bd.appendChild(ring);
     const lt=document.createElementNS(NS,'text');lt.setAttribute('x',x);lt.setAttribute('y',y-20);lt.setAttribute('text-anchor','middle');
     lt.setAttribute('font-size','12');lt.setAttribute('font-weight','bold');lt.setAttribute('fill','#ffd700');lt.setAttribute('stroke','#000');lt.setAttribute('stroke-width','.5');
     lt.textContent='★'+u.leader;bd.appendChild(lt);}
 });
 // hit / miss / KO markers drawn ON TOP of units so they're clearly visible
 (f.events||[]).forEach(e=>{
   if(e.type=='attack' && e.hits>0){impact(bd,e.to[0],e.to[1],e.hits);}
   else if(e.type=='attack' && e.hits==0){miss(bd,e.to[0],e.to[1]);}
   if(e.type=='eliminate'){ko(bd,e.pos[0],e.pos[1]);}
   if(e.type=='retreat'){const x=cx(e.to[0],e.to[1]),y=cy(e.to[0],e.to[1]);
     const t=document.createElementNS(NS,'text');t.setAttribute('x',x);t.setAttribute('y',y-22);t.setAttribute('text-anchor','middle');
     t.setAttribute('font-size','13');t.setAttribute('font-weight','bold');t.setAttribute('fill','#ff7a7a');t.setAttribute('stroke','#000');t.setAttribute('stroke-width','.6');t.textContent='RETREAT';bd.appendChild(t);}
 });
 // side panel
 const wt=R.win_targets;
 document.getElementById('mr').textContent='Rebel  '+f.medals.rebel+' / '+wt.rebel+' medals';
 document.getElementById('me').textContent='Empire '+f.medals.empire+' / '+wt.empire;
 const sideTag=f.side=='-'?'':('<span class="pill" style="background:'+(f.side=='rebel'?'#c0392b':'#274472')+'">'+f.side.toUpperCase()+'</span> ');
 const phaseCol={Move:'#5aa0e0',Fire:'#ffb84d',Retreat:'#ff9b9b',Pass:'#7a8a99',Setup:'#9fb3c8'}[f.phase]||'#9fb3c8';
 const phaseTag=f.phase?('<span class="pill" style="background:'+phaseCol+';color:#10243a;margin-left:4px">'+f.phase.toUpperCase()+'</span>'):'';
 document.getElementById('cardx').innerHTML='Turn '+f.turn+': '+sideTag+(f.card||'')+phaseTag;
 const desc=(R.card_text||{})[f.card];
 const ct=document.getElementById('cardtext');
 if(desc){ct.style.display='block';ct.textContent=desc;}else{ct.style.display='none';}
 let html='';
 (f.events||[]).forEach(e=>{
   if(e.type=='move'){html+='<span style="color:#9be09b">➤ '+e.kind+' '+JSON.stringify(e.frm)+' → '+JSON.stringify(e.to)+'</span><br>';}
   else if(e.type=='retreat'){html+='<span style="color:#ff9b9b">↩ '+e.kind+' retreats '+JSON.stringify(e.frm)+' → '+JSON.stringify(e.to)+'</span><br>';}
   else if(e.type=='attack'){html+=e.atk_kind+' '+JSON.stringify(e.from)+' → '+e.tgt_kind+' '+JSON.stringify(e.to)+': ';
     e.faces.forEach(ff=>{const lab={inf:'I',veh:'V',blast:'B',retreat:'R',miss:'·'}[ff];html+='<span class="face f-'+ff+'">'+lab+'</span>';});
     html+=' &rarr; '+e.hits+' hit'+(e.hits==1?'':'s')+(e.retreats?', '+e.retreats+' retreat':'')+'<br>';}
   else if(e.type=='eliminate'){html+='<span class="kill">✪ '+e.kind+' '+JSON.stringify(e.pos)+' eliminated by '+e.by+(e.medal?(' (+'+e.medal+' medal)'):'')+'</span><br>';}
 });
 document.getElementById('log').innerHTML=html||'<i style="color:#7a8a99">(maneuver only)</i>';
 document.getElementById('fno').textContent=i+' / '+(R.frames.length-1);
 document.getElementById('sl').value=i;
 // hands: highlight the chosen card for the side to act this frame
 function renderHand(elid, sideName){
   const cards=(f.hands&&f.hands[sideName])||[]; let h='';
   let playedShown=false;
   cards.forEach(c=>{
     const isPlay=(sideName===f.side)&&!playedShown&&c.name===f.card;
     if(isPlay)playedShown=true;
     const cls='chip'+(isPlay?' played':'')+(c.type==='reaction'?' react':'');
     const tip=((R.card_text||{})[c.name]||'').replace(/"/g,'&quot;');
     h+='<span class="'+cls+'" title="'+tip+'">'+c.name+(c.type==='reaction'?' ⚡':'')+'</span>';
   });
   document.getElementById(elid).innerHTML=h||'<i style="color:#7a8a99">—</i>';
 }
 renderHand('handR','rebel'); renderHand('handE','empire');
}
function goto(n){i=Math.max(0,Math.min(R.frames.length-1,n));draw();}
function step(d){goto(i+d);}
function toggle(){const b=document.getElementById('play');
 if(timer){clearInterval(timer);timer=null;b.textContent='▶ Play';}
 else{b.textContent='⏸ Pause';timer=setInterval(()=>{if(i>=R.frames.length-1){clearInterval(timer);timer=null;b.textContent='▶ Play';return;}step(1);},+document.getElementById('spd').value);}}
document.getElementById('spd').oninput=()=>{if(timer){clearInterval(timer);timer=null;toggle();}};
document.getElementById('sl').max=R.frames.length-1;
const nturns=Math.max(...R.frames.map(f=>f.turn||0));
document.getElementById('subt').textContent='Scenario '+R.scenario+': '+R.name+'  •  '+R.first+' moves first  •  result: '+R.winner.toUpperCase()+' victory  ('+nturns+' turns, '+(R.frames.length-1)+' steps)';
document.getElementById('rules').textContent=R.rules||'';
draw();
</script></body></html>'''

with open(OUT, 'w') as f:
    f.write(HTML.replace('__DATA__', DATA))
import os
print('wrote', OUT, round(os.path.getsize(OUT) / 1024), 'KB')
