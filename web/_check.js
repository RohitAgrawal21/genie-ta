
const $q=document.getElementById('q'), $drop=document.getElementById('drop'),
      $go=document.getElementById('go'), $out=document.getElementById('out');
let items=[], active=-1, chosen=null, tmr=null;

function hideDrop(){$drop.style.display='none';active=-1;}
function renderDrop(){
  if(!items.length){hideDrop();return;}
  $drop.innerHTML=items.map((x,i)=>
    `<div class="opt${i===active?' active':''}" data-i="${i}">
       <span class="sym">${x.s} <span class="exch ${(x.exch||'NSE').toLowerCase()}">${x.exch||'NSE'}</span></span>
       <span class="nm">${x.n}</span></div>`).join('');
  $drop.style.display='block';
  [...$drop.children].forEach(el=>el.onclick=()=>choose(+el.dataset.i));
}
function choose(i){chosen=items[i]; $q.value=items[i].s+' — '+items[i].n; hideDrop(); analyze();}

$q.addEventListener('input',()=>{
  chosen=null; const q=$q.value.trim();
  clearTimeout(tmr);
  if(q.length<1){hideDrop();return;}
  tmr=setTimeout(async()=>{
    try{ items=await (await fetch('/api/suggest?q='+encodeURIComponent(q))).json();
         active=-1; renderDrop(); }catch(e){hideDrop();}
  },120);
});
$q.addEventListener('keydown',e=>{
  if($drop.style.display==='block'&&items.length){
    if(e.key==='ArrowDown'){active=(active+1)%items.length;renderDrop();e.preventDefault();return;}
    if(e.key==='ArrowUp'){active=(active-1+items.length)%items.length;renderDrop();e.preventDefault();return;}
    if(e.key==='Enter'&&active>=0){choose(active);e.preventDefault();return;}
  }
  if(e.key==='Enter'){analyze();}
});
document.addEventListener('click',e=>{if(!$drop.contains(e.target)&&e.target!==$q)hideDrop();});
$go.onclick=analyze;

function selFromInput(){
  // returns {t: ticker to send, n: name, label: for display}
  if(chosen) return {t:chosen.t, n:chosen.n, label:chosen.s};
  const v=$q.value.trim();
  if(items.length){ const x=items[0];
    if(v.toUpperCase()===x.s.toUpperCase()||v.toLowerCase().includes(x.n.toLowerCase()))
      return {t:x.t, n:x.n, label:x.s}; }
  const raw=v.split(' ')[0].toUpperCase();
  return {t:raw, n:null, label:raw};
}

function loadingMsg(msg){ $out.innerHTML=`<div class="loading"><div class="spin"></div>${msg}</div>`; }

async function fetchAnalyze(sel){
  const c=new AbortController(); const t=setTimeout(()=>c.abort(),95000);
  let url='/api/analyze?symbol='+encodeURIComponent(sel.t);
  if(sel.n) url+='&name='+encodeURIComponent(sel.n);
  try{ const res=await fetch(url,{signal:c.signal}); return await res.json(); }
  finally{ clearTimeout(t); }
}

async function analyze(){
  const sel=selFromInput(); if(!sel.t){return;}
  hideDrop(); $go.disabled=true;
  loadingMsg(`Reading the charts for <b>${sel.label}</b>… (first load can take a few seconds)`);
  let r=null;
  for(let attempt=1; attempt<=3; attempt++){
    try{ r=await fetchAnalyze(sel); break; }
    catch(e){
      if(attempt<3){ loadingMsg(`Server is waking up — retrying <b>${sel.label}</b> (${attempt}/2)…`);
                     await new Promise(s=>setTimeout(s,4000)); }
    }
  }
  if(r){
    render(r);
    if(r.ok && window.goatcounter && window.goatcounter.count){
      window.goatcounter.count({path:'analyze/'+r.symbol, title:'Analyze '+(r.name||r.symbol), event:true});
    }
  } else {
    $out.innerHTML=`<div class="err">The server is waking up or busy. Please wait ~30 seconds and click Analyze again.</div>`;
  }
  $go.disabled=false;
}

function bandColor(s){ if(s==null) return 'var(--mut)'; if(s>=70) return 'var(--good)'; if(s>=45) return '#2f6bff'; if(s>=30) return 'var(--warn)'; return 'var(--bad)'; }
const FAC_LABELS={Momentum:'Momentum',Trend:'Trend',RelativeStrength:'Rel. Strength',LowVolatility:'Low Volatility',Value:'Value',Quality:'Quality'};
const FAC_ORDER=['Momentum','Trend','RelativeStrength','LowVolatility','Value','Quality'];

function factorBars(sub){
  return FAC_ORDER.map(k=>{ const v=sub?sub[k]:null; const w=(v==null)?0:v;
    return `<div class="fbar"><span class="flab">${FAC_LABELS[k]}</span>
      <span class="ftrack"><span class="ffill" style="width:${w}%;background:${bandColor(v)}"></span></span>
      <span class="fval" style="color:${bandColor(v)}">${v==null?'n/a':Math.round(v)}</span></div>`;
  }).join('');
}
function miniFactors(sub){
  return '<span class="mini">'+FAC_ORDER.map(k=>{const v=sub?sub[k]:null;
    return `<i style="background:${bandColor(v)}" title="${FAC_LABELS[k]}: ${v==null?'n/a':Math.round(v)}"></i>`;}).join('')+'</span>';
}
function fundTable(f, meta){
  f=f||{};
  const rows=[['P/E (TTM)',f.pe],['Forward P/E',f.forward_pe],['Price / Book',f.price_to_book],
    ['ROE',f.roe_pct!=null?f.roe_pct+'%':null],['Net margin',f.net_margin_pct!=null?f.net_margin_pct+'%':null],
    ['Debt / Equity',f.debt_to_equity],['Div. yield',f.dividend_yield_pct!=null?f.dividend_yield_pct+'%':null],
    ['Mkt cap (₹cr)',f.market_cap_cr!=null?Number(f.market_cap_cr).toLocaleString('en-IN'):null],
    ['Sector',f.sector]];
  const cells=rows.map(([k,val])=>`<div class="fund-cell"><span class="fk">${k}</span><span class="fv">${val==null?'<span class=muted>n/a</span>':val}</span></div>`).join('');
  const src=(meta&&meta.source)?`Source: ${meta.source} · as of ${meta.as_of}. Every value reconciled (P/E × EPS = price); blank = unavailable or failed validation — never estimated.`:'Fundamentals unavailable for this stock.';
  return `<div class="fund-grid">${cells}</div><div class="fund-src">${src}</div>`;
}

function render(r){
  if(!r.ok){ $out.innerHTML=`<div class="err">⚠️ ${r.error||'Could not analyze.'}</div>`; return; }
  const v=r.verdict, L=r.levels, sc=r.score;
  const rupee=(x)=> (x===null||x===undefined) ? '<span class="muted">—</span>' : '₹'+x;
  const cards=r.cards.map(c=>
    `<div class="card ${c.tone}"><div class="lab"><span class="dot ${c.tone}"></span>${c.label}</div>
     <div class="mn">${c.meaning}</div></div>`).join('');
  const rules=r.rules.length ? r.rules.map(x=>
    `<div class="rule"><span>${x.id} · ${x.name}</span><span class="tag ${x.signal}">${x.signal.toUpperCase()}</span></div>`).join('')
    : '<div class="mn">No individual signals firing today.</div>';
  const riskBanner = r.limited_history ?
    `<div class="risk">⚠️ <b>Limited history:</b> ${r.history_note}</div>` : '';
  const hasScore = sc && sc.genie_score!=null;
  const topPct = (hasScore && sc.rank) ? Math.max(1,Math.round(sc.rank/sc.rank_total*100)) : null;
  const scoreCard = hasScore ? `
    <div class="score-card">
      <div class="dial" style="--c:${bandColor(sc.genie_score)};--pct:${sc.genie_score}">
        <div class="dial-in"><span class="dial-num" style="color:${bandColor(sc.genie_score)}">${Math.round(sc.genie_score)}</span><span class="dial-max">/ 100</span></div>
      </div>
      <div class="score-meta">
        <div class="score-title">Genie Score</div>
        <div class="score-sub">${sc.rank?`Rank #${sc.rank} of ${sc.rank_total}${topPct?` · top ${topPct}%`:''}`:`scored vs ${sc.rank_total} tracked stocks`}</div>
        <div class="score-hint">6-factor blend, 0–100</div>
      </div>
    </div>` : '';
  const verdictCard = `
    <div class="verdict ${v.tone}">
      <div><span class="badge">${v.action}</span><span class="conf">confidence: ${v.confidence}</span></div>
      <div class="headline">${v.headline}</div>
      <div class="reason">${v.reason}</div>
    </div>`;
  const betaTxt = r.beta_vs_nifty!=null ? ` · β ${r.beta_vs_nifty} vs Nifty` : '';
  $out.innerHTML=`
    <div class="${hasScore?'topgrid':''}">${scoreCard}${verdictCard}</div>
    ${riskBanner}
    <div class="meta"><b>${r.name||r.symbol}</b> (${r.symbol})${r.in_universe===false&&hasScore?' · <span class=muted>not in daily leaderboard — scored live</span>':''} · ₹${r.price}${betaTxt} · as of ${r.as_of}</div>
    ${hasScore?`<div class="sec-h">📊 Factor breakdown</div><div class="factors">${factorBars(sc.subscores)}</div>`:''}
    <div class="sec-h">📄 Fundamentals</div>${fundTable(r.fundamentals, r.fundamentals_meta)}
    <div class="sec-h">🔍 What's going on</div>
    <div class="cards">${cards}</div>
    <div class="levels"><h3>🧭 Simple price map</h3>
      <div class="lvrow"><span class="lvtag">Buy above</span><span class="lvval good">${rupee(L.buy_above)}</span>
        <span class="lvdesc">a confirmed move over this = strength returning</span></div>
      <div class="lvrow"><span class="lvtag">Now</span><span class="lvval">${rupee(L.price)}</span>
        <span class="lvdesc">current price</span></div>
      <div class="lvrow"><span class="lvtag">Support</span><span class="lvval">${rupee(L.support)}</span>
        <span class="lvdesc">first floor it should hold</span></div>
      <div class="lvrow"><span class="lvtag">Get out below</span><span class="lvval bad">${rupee(L.stop_below)}</span>
        <span class="lvdesc">breaking this = thesis is wrong, exit</span></div>
      <div class="lvrow"><span class="lvtag">Overhead</span><span class="lvval">${rupee(L.resistance)}</span>
        <span class="lvdesc">bigger ceiling further up (200-day avg; blank if too new)</span></div>
    </div>
    <details><summary>See the technical signals behind this (${r.rules.length})</summary>${rules}</details>
    <div class="disc">${r.disclaimer}</div>`;
  window.scrollTo({top:0,behavior:'smooth'});
}

async function showLeaderboard(){
  hideDrop();
  $out.innerHTML=`<div class="loading"><div class="spin"></div>Loading Top Picks…</div>`;
  try{
    const d=await (await fetch('/api/leaderboard?limit=100')).json();
    if(!d.rows||!d.rows.length){ $out.innerHTML=`<div class="risk">The daily leaderboard isn't ready yet — check back shortly.</div>`; return; }
    const rows=d.rows.map(r=>{
      const nm=(r.n||'').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
      return `<tr onclick="quickAnalyze('${r.s.replace(/'/g,'')}','${nm}')">
        <td>${r.rank}</td><td><b>${r.s}</b></td><td class="nm-cell">${r.n||''}</td>
        <td class="lb-score" style="color:${bandColor(r.score)}">${Math.round(r.score)}</td>
        <td>${miniFactors(r.sub)}</td><td>${r.pe==null?'—':r.pe}</td></tr>`;}).join('');
    $out.innerHTML=`<div class="sec-h">🏆 Top Picks — highest Genie Scores</div>
      <div class="meta">${d.total} stocks ranked by the balanced 6-factor score · as of ${d.as_of} · click any row for the full analysis</div>
      <div class="lb"><table><thead><tr><th>#</th><th>Ticker</th><th>Company</th><th>Score</th><th>Mom·Trd·RS·LVol·Val·Qual</th><th>P/E</th></tr></thead><tbody>${rows}</tbody></table></div>
      <div class="disc">Genie Score is a cross-sectional percentile blend of Momentum, Trend, Relative-Strength, Low-Volatility, Value and Quality. All price factors are computed exactly; fundamentals are reconciled. Educational only, not advice.</div>`;
    window.scrollTo({top:0,behavior:'smooth'});
  }catch(e){ $out.innerHTML=`<div class="err">Couldn't load Top Picks. The server may be waking up — try again in ~30s.</div>`; }
}
function quickAnalyze(s,n){ chosen={s:s,n:n,t:s,exch:'NSE'}; $q.value=s+' — '+n; analyze(); }
