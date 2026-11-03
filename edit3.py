S='/home/claude/site/index.html'
t=open(S).read()
def rep(o,n):
    global t; assert o in t,o[:70]; t=t.replace(o,n,1)
rep('const NOEMBED=["studiobinder.com","metrotrains.com.au"];','const NOEMBED=["studiobinder.com","metrotrains.com.au","youtube.com"];')
rep("return`https://www.youtube.com/embed/${m[1]}?autoplay=1&rel=0`;","{const s=u.match(/[?&]t=(\\d+)/);return`https://www.youtube.com/embed/${m[1]}?autoplay=1&rel=0${s?'&start='+s[1]:''}`}")
rep("const ICON={video:'🎬',audio:'🎧',pdf:'📄',file:'📎',link:'🔗',image:'🖼️',set:'🖼️'};","const blocked=it=>it.embed===false||NOEMBED.some(h=>it.src.includes(h));\nconst isSite=it=>it.type==='link'&&!embedUrl(it.src);\nconst ICON={video:'🎬',audio:'🎧',pdf:'📄',file:'📎',link:'▶',image:'🖼️',set:'🖼️'};")
rep("const d=el('div','th',`<span>${ICON[it.type]||'📎'}</span>`);","const d=el('div','th',`<span>${isSite(it)?'🌐':ICON[it.type]||'📎'}</span>`);if(isSite(it))d.append(el('em','',esc(new URL(it.src).hostname.replace(/^www\\./,''))));")
rep("n.autoplay=!!play;n.src=it.src}","n.autoplay=!!play;n.src=it.src;if(play)Promise.resolve(n.play()).catch(()=>{n.muted=true;n.play().catch(()=>{})})}")
rep("n.src=embedUrl(it.src).replace('autoplay=1','autoplay='+(play?1:0))}","n.src=embedUrl(it.src).replace('autoplay=1','autoplay='+(play?1:0))}\n else if(it.type==='link'&&!blocked(it))n=viewer([],it.src);")
rep("<big>${it.type==='link'?'🔗':'📎'}</big><strong>${esc(it.title)}</strong>`);","<big>${it.type==='link'?'🌐':'📎'}</big><strong>${esc(it.title)}</strong>${it.type==='link'?'<span>This website does not allow embedding, so it opens in a new tab.</span>':''}`);")
rep("const root=el('div','iv'),all=forms.flatMap(f=>(INSPO[f]||[]).map(x=>({...x,form:f})));","""const root=el('div','iv'),M=new Map();
 forms.forEach(f=>(INSPO[f]||[]).forEach(x=>{const k=x.srcs?x.srcs[0]:x.src,m=M.get(k);
  if(m){m.forms.push(f);x.cats.forEach(c=>{if(!m.cats.some(d=>d[0]===c[0]&&d[1]===c[1]))m.cats.push([...c])})}
  else M.set(k,{...x,cats:x.cats.map(c=>[...c]),forms:[f]})}));
 const all=[...M.values()];""")
rep("const inForm=x=>fsel==='all'||x.form===fsel;","const inForm=x=>fsel==='all'||x.forms.includes(fsel);")
rep("all.filter(x=>x.form===k).length","all.filter(x=>x.forms.includes(k)).length")
rep("if(forms.length>1){const fs=el('span','',PAGES[it.form].n);fs.style.cssText=`background:${PAGES[it.form].c};color:#1c2239`;$g.append(fs)}","if(forms.length>1)it.forms.forEach(k=>{const fs=el('span','',PAGES[k].n);fs.style.cssText=`background:${PAGES[k].c};color:#1c2239`;$g.append(fs)});")
rep(" function rand(){"," const pickable=()=>{const L=list.filter(x=>!isSite(x));return L.length?L:list};\n function rand(){")
rep("deck=[...list];","deck=[...pickable()];")
rep("function refresh(){list=pool();deck=[];filters();cur=list.includes(cur)?cur:null;strip();if(!cur)show(list[0]||null,false);else upd()}","function refresh(play=true){list=pool();deck=[];filters();cur=list.includes(cur)?cur:null;strip();if(!cur){const P=pickable();show(P.length?P[Math.random()*P.length|0]:null,play)}else upd()}")
rep("q=e.target.value.trim().toLowerCase();refresh()}","q=e.target.value.trim().toLowerCase();refresh(false)}")
rep("show(list[Math.random()*list.length|0],false);","{const P=pickable();show(P[Math.random()*P.length|0],true)}")
rep(".nohead>h2{display:none}",".nohead>h2{display:none}\n.sc .th em{position:absolute;bottom:3px;left:5px;right:5px;font-size:10.5px;color:#fff;opacity:.85;font-style:normal;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n.aud span{max-width:44ch;opacity:.85}")
open(S,'w').write(t)
