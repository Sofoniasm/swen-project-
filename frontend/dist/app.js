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

  function renderTelemetry(rows){
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
    latestTelemetry = tail.slice(-50);
    renderTelemetry(latestTelemetry.slice().reverse().slice(0,30));
    const m = computeMetrics(latestTelemetry, latestDecisions);
    metricSpend.textContent = `$${m.spend.toFixed(5)}`;
    metricLatency.textContent = `${m.latency}`;
    metricServices.textContent = `${m.services}`;
    metricConfidence.textContent = m.avgConf ? `${(m.avgConf*100).toFixed(0)}%` : '—';
    econ1h.textContent = `$${(m.spend*60).toFixed(3)}`;
    econSave.textContent = '—';
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
        const resp = await fetch('/deploy_request', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) });
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
        const resp = await fetch('/price', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({cpu: cpu, memory: memory, region: dfRegion.value||undefined}) });
        if(!resp.ok) throw new Error('price request failed');
        const j = await resp.json();
        // j is an object keyed by provider
        const parts = Object.keys(j).map(k => `${k}: $${(j[k].cost_per_min||0).toFixed(6)}/min`);
        dfPrices.innerHTML = parts.join('<br/>');
      }catch(e){ dfPrices.textContent = 'Price lookup failed'; console.error(e); }
    });
  }

  // WebSocket connection
  try{
    const ws = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws');
    ws.addEventListener('open', ()=> setStatus('connected (ws)'));
    ws.addEventListener('close', ()=> setStatus('disconnected'));
    ws.addEventListener('message', (ev)=>{
      try{
        const data = JSON.parse(ev.data);
        if(data.telemetry_tail) applyTelemetryUpdate(data.telemetry_tail);
        if(data.decisions_tail) applyDecisionUpdate(data.decisions_tail);
      }catch(e){ console.error('ws parse', e); }
    });
  }catch(e){ console.warn('ws failed', e); setStatus('ws failed'); }

  // polling fallback
  async function poll(){
    try{
      const [rt, rd] = await Promise.all([fetch('/telemetry'), fetch('/decisions')]);
      if(rt.ok){ const t = await rt.json(); applyTelemetryUpdate(t); }
      if(rd.ok){ const d = await rd.json(); applyDecisionUpdate(d); }
      setStatus('connected (poll)');
    }catch(e){ setStatus('disconnected'); }
    setTimeout(poll, 4000);
  }
  setTimeout(poll, 1000);

})();
