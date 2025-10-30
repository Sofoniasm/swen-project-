(function(){
  const statusEl = document.getElementById('status');
  const telemetryTableBody = document.querySelector('#telemetry-table tbody');
  const decisionsList = document.getElementById('decisions-list');
  const metricSpend = document.getElementById('metric-spend');
  const metricLatency = document.getElementById('metric-latency');
  const metricServices = document.getElementById('metric-services');
  const metricConfidence = document.getElementById('metric-confidence');
  const econ1h = document.getElementById('econ-1h');
  const econSave = document.getElementById('econ-save');
  const dbgWs = (typeof document !== 'undefined') ? document.getElementById('dbg-ws-val') : null;
  const dbgPoll = (typeof document !== 'undefined') ? document.getElementById('dbg-poll-val') : null;
  const dbgLast = (typeof document !== 'undefined') ? document.getElementById('dbg-last-val') : null;
  const dbgRows = (typeof document !== 'undefined') ? document.getElementById('dbg-rows-val') : null;
  const dbgRenderMs = (typeof document !== 'undefined') ? document.getElementById('dbg-render-ms') : null;
  const statusBadge = (typeof document !== 'undefined') ? document.getElementById('status') : null;
  const dbgForce = (typeof document !== 'undefined') ? document.getElementById('dbg-force') : null;
  const dbgTestBtn = (typeof document !== 'undefined') ? document.getElementById('dbg-test-api') : null;
  const dbgTelemetryCount = (typeof document !== 'undefined') ? document.getElementById('dbg-telemetry-count') : null;
  const dbgDecisionsCount = (typeof document !== 'undefined') ? document.getElementById('dbg-decisions-count') : null;
  const deployForm = document.getElementById('deploy-form');
  const dfService = document.getElementById('df-service');
  const dfSize = document.getElementById('df-size');
  const dfRegion = document.getElementById('df-region');
  const dfSubmit = document.getElementById('df-submit');
  const dfPriceBtn = document.getElementById('df-price');
  const dfResult = document.getElementById('df-result');
  const dfPrices = document.getElementById('df-prices');

  let latestTelemetry = [];
  let latestDecisions = [];

  function setStatus(s){ statusEl.textContent = s; }

  // set badge color helper
  function setStatusBadge(state){
    try{
      if(!statusBadge) return;
      if(state === 'connected (ws)' || state === 'connected (poll)'){
        statusBadge.style.background = '#16a34a'; // green
        statusBadge.style.color = '#fff';
      }else if(state === 'demo mode'){
        statusBadge.style.background = '#f59e0b'; // amber
        statusBadge.style.color = '#042';
      }else{
        statusBadge.style.background = '#cfcfcf'; // gray
        statusBadge.style.color = '#012';
      }
      statusBadge.textContent = s;
    }catch(e){/*noop*/}
  }

  function renderTelemetry(rows){
    // Use requestAnimationFrame to avoid blocking the main thread during heavy updates
    const start = performance.now();
    window.requestAnimationFrame(()=>{
      telemetryTableBody.innerHTML = '';
      rows.forEach(r=>{
        const tr = document.createElement('tr');
        const time = new Date(r.timestamp || Date.now()).toLocaleTimeString();
        tr.innerHTML = `<td>${time}</td>
          <td>${r.service||'-'}</td>
          <td>${r.provider||'-'}</td>
          <td>${r.region||'-'}</td>
          <td>${(r.cpu||0).toFixed(2)}</td>
          <td>${(r.memory||0).toFixed(2)}</td>
          <td>${r.latency_ms||'-'}</td>
          <td>$${(r.cost_per_min||0).toFixed(5)}</td>`;
        telemetryTableBody.appendChild(tr);
      });
      // update debug rows count
      try{ if(dbgRows) dbgRows.textContent = rows.length; }catch(e){}
      const dur = Math.max(0, Math.round(performance.now() - start));
      try{ if(dbgRenderMs) dbgRenderMs.textContent = dur + 'ms'; }catch(e){}
    });
  }

  function renderDecisions(list){
    decisionsList.innerHTML = '';
    list.forEach(d=>{
      const el = document.createElement('div');
      el.className = 'decision';
      const time = new Date(d.timestamp || Date.now()).toLocaleTimeString();
      el.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center"><strong>${d.service||'service'}</strong><span style="font-size:12px;color:var(--muted)">${time}</span></div>
        <div style="margin-top:6px">from <strong>${d.current_provider}</strong> → <strong>${d.recommended_provider}</strong></div>
        <div style="margin-top:6px;color:var(--muted);font-size:13px">${d.reason || ''} · confidence ${d.confidence ?? '-'} </div>`;
      decisionsList.appendChild(el);
    });
  }

  function computeMetrics(telemetry, decisions){
    const spend = telemetry.reduce((s,t)=> s + (parseFloat(t.cost_per_min)||0), 0);
    const latency = telemetry.length ? Math.round(telemetry.reduce((s,t)=> s + (t.latency_ms||0),0)/telemetry.length) : 0;
    const services = new Set(telemetry.map(t=>t.service)).size || 0;
    const avgConf = decisions.length ? (decisions.reduce((s,d)=> s + (d.confidence||0),0)/decisions.length) : null;
    return { spend, latency, services, avgConf };
  }

  function applyTelemetryUpdate(tail){
    try{
      // simple change-detection key to avoid unnecessary re-renders
      latestTelemetry = tail.slice(-200);
      const top = latestTelemetry.slice().reverse().slice(0,30);
      const key = `${top.length}:${top[0]?.timestamp||''}`;
      if(applyTelemetryUpdate._lastKey === key){
        // nothing new
        return;
      }
      applyTelemetryUpdate._lastKey = key;
      renderTelemetry(top);
    const m = computeMetrics(latestTelemetry, latestDecisions);
      metricSpend.textContent = `$${m.spend.toFixed(5)}`;
    metricLatency.textContent = `${m.latency}`;
    metricServices.textContent = `${m.services}`;
    metricConfidence.textContent = m.avgConf ? `${(m.avgConf*100).toFixed(0)}%` : '—';
    econ1h.textContent = `$${(m.spend*60).toFixed(3)}`;
      econSave.textContent = '—';
      // debug: last update and rows
      try{ if(dbgLast) dbgLast.textContent = new Date().toLocaleTimeString(); }catch(e){}
      try{ if(dbgRows) dbgRows.textContent = latestTelemetry.length; }catch(e){}
    }catch(e){ console.error('applyTelemetryUpdate failed', e); }
  }

  function applyDecisionUpdate(tail){
    latestDecisions = tail.slice(-30);
    renderDecisions(latestDecisions.slice().reverse());
    // update confidence metric
    const m = computeMetrics(latestTelemetry, latestDecisions);
    metricConfidence.textContent = m.avgConf ? `${(m.avgConf*100).toFixed(0)}%` : '—';
  }

  // handle deploy form submission
  if(deployForm){
    deployForm.addEventListener('submit', async (ev)=>{
      ev.preventDefault();
      dfResult.textContent = 'Requesting recommendation...';
      // size mapping
      const size = dfSize.value;
      let cpu = 0, memory = 0;
      if(size === 'small'){ cpu = 0.5; memory = 128; }
      else if(size === 'medium'){ cpu = 1; memory = 256; }
      else if(size === 'large'){ cpu = 2; memory = 512; }

      const payload = {
        service: dfService.value || '',
        cpu: cpu,
        memory: memory,
        region: dfRegion.value || undefined
      };
      try{
  const resp = await fetch((API_BASE || '') + '/deploy_request', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) });
        if(!resp.ok) throw new Error('request failed');
        const j = await resp.json();
        // show result summary
        dfResult.innerHTML = `Recommended: <strong>${j.recommended_provider}</strong> — est $${(j.estimated_cost_per_min||0).toFixed(6)}/min`;
        // prepend to decisions list UI immediately
        try{ applyDecisionUpdate([...(latestDecisions||[]), j]); }catch(e){}
      }catch(e){
        dfResult.textContent = 'Request failed — see console';
        console.error(e);
      }
    });
  }

  // Get Price button - fetch prices for all providers for selected size
  if(dfPriceBtn){
    dfPriceBtn.addEventListener('click', async ()=>{
      dfPrices.textContent = 'Checking prices...';
      const size = dfSize.value;
      let cpu = 0, memory = 0;
      if(size === 'small'){ cpu = 0.5; memory = 128; }
      else if(size === 'medium'){ cpu = 1; memory = 256; }
      else if(size === 'large'){ cpu = 2; memory = 512; }
      if(!cpu){ dfPrices.textContent = 'Please select a size.'; return; }
      try{
  const resp = await fetch((API_BASE || '') + '/price', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({cpu: cpu, memory: memory, region: dfRegion.value||undefined}) });
        if(!resp.ok) throw new Error('price request failed');
        const j = await resp.json();
        // j is an object keyed by provider
        const parts = Object.keys(j).map(k => `${k}: $${(j[k].cost_per_min||0).toFixed(6)}/min`);
        dfPrices.innerHTML = parts.join('<br/>');
      }catch(e){ dfPrices.textContent = 'Price lookup failed'; console.error(e); }
    });
  }

  // Decide API base: when frontend is served on port 8000 (docker compose), the backend is on 8001.
  // When backend serves the frontend directly (same origin) API_BASE should be empty (relative).
  const API_BASE = (location.port === '8000') ? (location.protocol + '//' + location.hostname + ':8001') : '';

  // WebSocket connection (use backend host when frontend is served separately)
  // Robust reconnect with backoff; if WS is unavailable we fall back to polling.
  (function setupTransport(){
    const base = API_BASE || '';
    const host = location.hostname;
    const wsHostPort = API_BASE ? '' : (location.port ? ':' + location.port : '');
    const wsPath = (location.protocol === 'https:' ? 'wss://' : 'ws://') + host + (API_BASE ? '' : '') + '/ws';

    let ws = null;
    let reconnectMs = 1000;
    let wsClosedByApp = false;

    function connectWS(){
      try{
        // prefer same-origin ws endpoint; allow API proxy if needed
        const url = (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.hostname + (API_BASE ? '' : '') + '/ws';
        ws = new WebSocket(url);
        ws.addEventListener('open', ()=>{
          reconnectMs = 1000;
          setStatus('connected (ws)');
          setStatusBadge('connected (ws)');
          try{ if(dbgWs) dbgWs.textContent = 'open'; }catch(e){}
        });
        ws.addEventListener('close', ()=>{
          try{ if(dbgWs) dbgWs.textContent = 'closed'; }catch(e){}
          if(!wsClosedByApp){
            setStatus('ws disconnected');
            setStatusBadge('ws disconnected');
            // try reconnect with backoff
            setTimeout(()=>{ reconnectMs = Math.min(30000, reconnectMs * 1.8); connectWS(); }, reconnectMs);
          }
        });
        ws.addEventListener('error', (e)=>{ console.warn('ws error', e); try{ if(dbgWs) dbgWs.textContent = 'error'; }catch(err){} ws.close(); });
        ws.addEventListener('message', (ev)=>{
          try{
            const data = JSON.parse(ev.data);
            if(data.telemetry_tail){ applyTelemetryUpdate(data.telemetry_tail); stopDemoTelemetry(); try{ if(dbgLast) dbgLast.textContent = new Date().toLocaleTimeString(); }catch(e){} }
            if(data.decisions_tail){ applyDecisionUpdate(data.decisions_tail); stopDemoTelemetry(); try{ if(dbgLast) dbgLast.textContent = new Date().toLocaleTimeString(); }catch(e){} }
          }catch(e){ console.error('ws parse', e); }
        });
      }catch(e){ console.warn('ws setup failed', e); }
    }

  // start ws and also start polling fallback (poll will be quiet if ws delivers data)
  connectWS();

    // polling fallback: use interval so it runs reliably even if a fetch delays
    async function pollOnce(){
      try{
        const telemetryResp = await fetch((API_BASE || '') + '/telemetry');
        if(telemetryResp.ok){ const t = await telemetryResp.json(); if(t && t.length){ applyTelemetryUpdate(t); stopDemoTelemetry(); setStatus('connected (poll)'); try{ if(dbgPoll) dbgPoll.textContent = 'ok'; }catch(e){} return; } }
        const decisionsResp = await fetch((API_BASE || '') + '/decisions');
        if(decisionsResp.ok){ const d = await decisionsResp.json(); if(d && d.length){ applyDecisionUpdate(d); stopDemoTelemetry(); setStatus('connected (poll)'); try{ if(dbgPoll) dbgPoll.textContent = 'ok'; }catch(e){} return; } }
        // if no telemetry returned, leave demo mode running (demoCheckLoop handles start/stop)
      }catch(e){ console.debug('poll failed', e); try{ if(dbgPoll) dbgPoll.textContent = 'fail'; }catch(err){} }
    }
  // initial poll after short delay then regular polling
  setTimeout(pollOnce, 1200);
  setInterval(pollOnce, 4000);

    // expose a graceful close if needed
    window.__swendemo_close_ws = ()=>{ wsClosedByApp = true; if(ws){ ws.close(); } };
  })();

  // --- Demo telemetry fallback: when backend returns no telemetry, simulate live data ---
  let _demoInterval = null;
  function rand(min, max){ return Math.random()*(max-min)+min; }
  function sampleChoice(arr){ return arr[Math.floor(Math.random()*arr.length)]; }
  function generateDemoEntry(baseTimestamp){
    const services = ['fetcher','indexer','ranker','ingestor','api'];
    const providers = ['aws','gcp','azure','oracle'];
    const regions = ['us-east-1','eu-west-1','ap-south-1','us-west-2'];
    const service = sampleChoice(services);
    const provider = sampleChoice(providers);
    const region = sampleChoice(regions);
    const cpu = +(rand(0.1,2).toFixed(2));
    const memory = +(rand(32,1024).toFixed(2));
    const latency_ms = Math.round(rand(10,350));
    const cost_per_min = +( (cpu * 0.005 + memory/1024 * 0.002 + latency_ms/10000) ).toFixed(6);
    return {
      timestamp: baseTimestamp || Date.now(),
      service, provider, region,
      cpu, memory, latency_ms, cost_per_min
    };
  }

  function generateDemoTelemetry(n){
    const now = Date.now();
    const arr = [];
    for(let i=0;i<n;i++) arr.push(generateDemoEntry(now - (n-i)*1000));
    return arr;
  }

  function startDemoTelemetry(){
    if(_demoInterval) return;
    latestTelemetry = generateDemoTelemetry(8);
    applyTelemetryUpdate(latestTelemetry.slice());
    setStatus('demo mode');
    _demoInterval = setInterval(()=>{
      // roll and add a new entry to simulate live flow
      latestTelemetry.push(generateDemoEntry());
      if(latestTelemetry.length>200) latestTelemetry.shift();
      applyTelemetryUpdate(latestTelemetry.slice());
    }, 4500);
  }

  function stopDemoTelemetry(){
    if(dbgForce && dbgForce.checked) return; // honor forced demo toggle
    if(_demoInterval){ clearInterval(_demoInterval); _demoInterval = null; setStatus('connected'); }
  }

  // periodically check if we have live telemetry; if none, start demo mode
  (function demoCheckLoop(){
    try{
      const hasLive = (latestTelemetry && latestTelemetry.length>0);
      if(!hasLive) startDemoTelemetry(); else stopDemoTelemetry();
    }catch(e){/*ignore*/}
    setTimeout(demoCheckLoop, 5000);
  })();

  // wire debug controls (force demo toggle and test API button)
  if(dbgForce){
    dbgForce.addEventListener('change', ()=>{
      if(dbgForce.checked) startDemoTelemetry(); else stopDemoTelemetry();
    });
  }

  if(dbgTestBtn){
    dbgTestBtn.addEventListener('click', async ()=>{
      try{
        const tr = await fetch((API_BASE||'') + '/telemetry');
        const dr = await fetch((API_BASE||'') + '/decisions');
        if(tr.ok){ const t = await tr.json(); if(dbgTelemetryCount) dbgTelemetryCount.textContent = (Array.isArray(t)?t.length:'-'); }
        if(dr.ok){ const d = await dr.json(); if(dbgDecisionsCount) dbgDecisionsCount.textContent = (Array.isArray(d)?d.length:'-'); }
        try{ if(dbgPoll) dbgPoll.textContent = (tr.ok && dr.ok) ? 'ok' : 'partial'; }catch(e){}
      }catch(e){ try{ if(dbgPoll) dbgPoll.textContent = 'fail'; }catch(_){} }
    });
  }

})();
