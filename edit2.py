S='/home/claude/site/index.html'
t=open(S).read()
def rep(o,n):
    global t; assert o in t,o[:60]; t=t.replace(o,n,1)
# CSS
a=t.index('/* inspiration */');b=t.index('.tags span{');b=t.index('\n',b)+1
CSS=r'''/* inspiration viewer */
.iv{flex:1;min-height:0;display:flex;flex-direction:column;gap:10px}
.itop{display:flex;gap:10px;align-items:center;flex:none;flex-wrap:wrap}
.itop .go{border:0;border-radius:99px;padding:12px 30px;font:700 22px Fredoka,'DM Sans',sans-serif;background:var(--ac);color:#1c2239;box-shadow:0 4px 0 rgba(0,0,0,.25)}
.itop .go:active{transform:translateY(3px);box-shadow:none}
.itop .pv{border:0;border-radius:99px;padding:9px 16px;font-weight:700;background:var(--navy);color:#fff}.itop .pv:disabled{opacity:.4;cursor:default}
.rc{color:var(--mute);font-size:14px}
.q{margin-left:auto;border:2px solid var(--line);border-radius:99px;padding:6px 14px;background:var(--card);color:var(--ink);font:inherit;font-size:14px;width:230px;max-width:100%}
.ibody{flex:1;min-height:0;display:grid;grid-template-columns:230px 1fr;gap:14px}
.ifilter{overflow:auto;border:2px solid var(--line);border-radius:14px;background:var(--card);padding:8px}
.ifilter h4{margin:8px 6px 4px;font:700 12px 'DM Sans',sans-serif;text-transform:uppercase;letter-spacing:.06em;color:var(--mute)}
.ifilter button{display:flex;justify-content:space-between;gap:8px;width:100%;text-align:left;border:0;background:none;padding:6px 10px;border-radius:8px;font-size:14px}
.ifilter button:hover{background:var(--paper)}
.ifilter button.on{background:var(--ac);color:#1c2239;font-weight:700}
.ifilter button.s{padding-left:24px;font-size:13px}.ifilter button:disabled{opacity:.4;cursor:default}
.ifilter button i{font-style:normal;color:var(--mute);font-size:12px}.ifilter button.on i{color:#1c2239}
.imain{display:flex;flex-direction:column;gap:8px;min-width:0;min-height:0}
.tags{display:flex;gap:6px;flex-wrap:wrap;align-items:center;flex:none}
.tags .tt{font:700 18px Fredoka,'DM Sans',sans-serif;margin-right:6px}
.tags span:not(.tt){background:var(--navy);color:#fff;border-radius:99px;padding:2px 12px;font-size:13px;font-weight:700}
.istage{flex:1;min-height:0;position:relative;background:#111;border-radius:14px;overflow:hidden}
.istage>*{position:absolute;inset:0;width:100%;height:100%;border:0;object-fit:contain}
.istage>.viewer{border-radius:0;border:0}
.aud{display:grid;place-content:center;justify-items:center;gap:10px;color:#fff;text-align:center;padding:20px}.aud big{font-size:60px}
.aud .dl{background:var(--yellow);color:var(--navy);padding:8px 18px;border-radius:99px;font-weight:700}
.istrip{flex:none;display:flex;gap:8px;overflow-x:auto;padding:3px 3px 5px}
.sc{flex:none;width:150px;border:2px solid var(--line);border-radius:10px;background:var(--card);padding:0;overflow:hidden;text-align:left}
.sc.on{border-color:var(--ac);box-shadow:0 0 0 2px var(--ac)}
.sc .th{position:relative;aspect-ratio:16/9;background:var(--navy);display:grid;place-items:center;font-size:22px}
.sc .th img,.sc .th video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.sc .bd{position:absolute;right:4px;bottom:4px;background:rgba(0,0,0,.7);color:#fff;font-size:11px;padding:1px 6px;border-radius:6px;z-index:1}
.sc .ttl{display:block;padding:4px 8px;font-size:12.5px;line-height:1.25;height:2.7em;overflow:hidden}
.nohead>h2{display:none}
@media(max-width:760px){.ibody{grid-template-columns:1fr;grid-template-rows:150px 1fr}}
'''
t=t[:a]+CSS+t[b:]
# JS
a=t.index('function card(it,now){');b=t.index('function home(app){')
JS=r'''const ICON={video:'🎬',audio:'🎧',pdf:'📄',file:'📎',link:'🔗',image:'🖼️',set:'🖼️'};
function thumb(it){
 const d=el('div','th',`<span>${ICON[it.type]||'📎'}</span>`);
 if(it.srcs)d.append(el('b','bd','▦ '+it.srcs.length));
 d._f=()=>{if(it.type==='video'){const n=el('video');n.muted=true;n.preload='metadata';n.playsInline=true;n.src=it.src+'#t=0.3';d.append(n)}
  else if(it.type==='image'||it.type==='set'){const i=el('img');i.loading='lazy';i.alt='';i.src=it.srcs?it.srcs[0]:it.src;d.append(i)}};
 io.observe(d);return d}
function media(it,play){
 let n;
 if(it.type==='video'){n=el('video');n.controls=true;n.playsInline=true;n.autoplay=!!play;n.src=it.src}
 else if(it.type==='audio'){n=el('div','aud',`<big>🎧</big><strong>${esc(it.title)}</strong>`);const a=el('audio');a.controls=true;a.autoplay=!!play;a.src=it.src;n.append(a)}
 else if(it.type==='image'){n=el('img');n.alt=it.title;n.src=it.src}
 else if(it.type==='set')n=viewer(it.srcs);
 else if(it.type==='pdf'){n=el('iframe');n.title=it.title;n.src=it.src}
 else if(it.type==='link'&&embedUrl(it.src)){n=el('iframe');n.allow='autoplay; fullscreen';n.allowFullscreen=true;n.src=embedUrl(it.src).replace('autoplay=1','autoplay='+(play?1:0))}
 else{n=el('div','aud',`<big>${it.type==='link'?'🔗':'📎'}</big><strong>${esc(it.title)}</strong>`);const a=el('a','dl',it.type==='link'?'Open link ↗':'Open / download');a.href=it.src;if(it.type==='link'){a.target='_blank';a.rel='noopener'}else a.download='';n.append(a)}
 return n}
function inspoViewer(forms){
 const root=el('div','iv'),all=forms.flatMap(f=>(INSPO[f]||[]).map(x=>({...x,form:f})));
 if(!all.length){root.className='empty';root.innerHTML=`<big>✨</big><strong>${forms.length>1?'Inspiration':PAGES[forms[0]].n+' inspiration'} is on its way</strong><p>Add files to the <code>inspiration/${forms.length>1?'&lt;media form&gt;':forms[0]}/</code> folder in the repo and they will appear here.</p>`;return root}
 let fsel='all',f={cat:'',sub:''},q='',list=[],cur=null,hist=[],deck=[];
 root.innerHTML='<div class="itop"><button class="go">🎲 Inspire me</button><button class="pv">← Previous</button><span class="rc"></span><input class="q" type="search" placeholder="Search" aria-label="Search inspirations"></div><div class="ibody"><nav class="ifilter" aria-label="Filters"></nav><div class="imain"><div class="tags"></div><div class="istage"></div><div class="istrip"></div></div></div>';
 const $f=$('.ifilter',root),$s=$('.istage',root),$t=$('.istrip',root),$g=$('.tags',root);
 const inForm=x=>fsel==='all'||x.form===fsel;
 const pool=()=>all.filter(x=>inForm(x)&&(!q||(x.title+' '+x.cats.map(c=>c.join(' ')).join(' ')).toLowerCase().includes(q))&&(!f.cat||x.cats.some(c=>c[0]===f.cat&&(!f.sub||c[1]===f.sub))));
 const btn=(h,on,fn,cls)=>{const b=el('button',(on?'on ':'')+(cls||''),h);b.onclick=fn;return b};
 function filters(){
  $f.replaceChildren();
  if(forms.length>1){$f.append(el('h4','','Media form'));
   [['all','All media forms',all.length],...forms.map(k=>[k,PAGES[k].n,all.filter(x=>x.form===k).length])].forEach(([k,n,c])=>{const b=btn(`${n}<i>${c}</i>`,fsel===k,()=>{fsel=k;f={cat:'',sub:''};refresh()});b.disabled=!c;$f.append(b)});
   $f.append(el('h4','','Category'))}
  const T={},base=all.filter(inForm);
  base.forEach(x=>x.cats.forEach(([c,s])=>{T[c]=T[c]||{ids:new Set(),s:{}};T[c].ids.add(x);if(s){(T[c].s[s]=T[c].s[s]||new Set()).add(x)}}));
  $f.append(btn(`All<i>${base.length}</i>`,!f.cat,()=>{f={cat:'',sub:''};refresh()}));
  Object.keys(T).sort((a,b)=>a.localeCompare(b)).forEach(c=>{
   $f.append(btn(`${esc(c)}<i>${T[c].ids.size}</i>`,f.cat===c&&!f.sub,()=>{f={cat:c,sub:''};refresh()}));
   Object.keys(T[c].s).sort().forEach(s=>$f.append(btn(`${esc(s)}<i>${T[c].s[s].size}</i>`,f.cat===c&&f.sub===s,()=>{f={cat:c,sub:s};refresh()},'s')))})}
 function strip(){$t.replaceChildren();list.forEach(it=>{const b=el('button','sc'+(it===cur?' on':''),`<span class="ttl">${esc(it.title)}</span>`);b.prepend(thumb(it));b._it=it;b.onclick=()=>show(it,true);$t.append(b)})}
 function upd(){$('.pv',root).disabled=hist.length<2;$('.rc',root).textContent=`${list.length} item${list.length===1?'':'s'}`}
 function show(it,play,back){
  cur=it;if(it&&!back&&hist[hist.length-1]!==it)hist.push(it);
  $s.replaceChildren();$g.replaceChildren();
  if(!it){$s.append(el('div','aud','<big>🔎</big><strong>Nothing matches</strong>'));upd();return}
  $s.append(media(it,play));
  $g.append(el('span','tt',esc(it.title)));
  if(forms.length>1)$g.append(el('span','',PAGES[it.form].n)).lastChild.style.cssText=`background:${PAGES[it.form].c};color:#1c2239`;
  it.cats.forEach(c=>$g.append(el('span','',esc(c.filter(Boolean).join(' / ')))));
  $t.querySelectorAll('.sc').forEach(b=>{const on=b._it===it;b.classList.toggle('on',on);if(on)b.scrollIntoView({block:'nearest',inline:'center'})});
  upd()}
 function refresh(){list=pool();deck=[];filters();cur=list.includes(cur)?cur:null;strip();if(!cur)show(list[0]||null,false);else upd()}
 function rand(){if(!list.length)return;if(!deck.length){deck=[...list];for(let i=deck.length-1;i>0;i--){const j=Math.random()*(i+1)|0;[deck[i],deck[j]]=[deck[j],deck[i]]}}
  let it=deck.pop();if(it===cur&&deck.length)it=deck.pop();show(it,true)}
 $('.go',root).onclick=rand;
 $('.pv',root).onclick=()=>{if(hist.length>1){hist.pop();show(hist[hist.length-1],true,true)}};
 $('.q',root).oninput=e=>{q=e.target.value.trim().toLowerCase();refresh()};
 list=pool();filters();strip();show(list[Math.random()*list.length|0],false);
 return root}

'''
t=t[:a]+JS+t[b:]
# remove old card helpers left between? (esc, io kept before 'function card')
rep("else if(tab.inspo)pane.append(p==='sat'?randomiser():gallery(p));","else if(tab.inspo)pane.append(inspoViewer(p==='sat'?Object.keys(PAGES).filter(k=>k!=='sat'):[p]));")
rep("const pane=$('.pane',app);","const pane=$('.pane',app);if(tab.inspo)pane.classList.add('nohead');")
open(S,'w').write(t)
