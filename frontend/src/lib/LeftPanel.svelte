<script>
  import { selectedPoint, currentVar, currentPeriodo, VAR_CONFIG, PERIODO_CONFIG } from '../stores/mapState.js';

  const API = 'http://localhost:8000';

  let punto = null;
  let varActiva = 't2m', periodo = '1997';
  let cfg = VAR_CONFIG['t2m'];
  let ranking = null;
  let rankingUnidades = '';
  let canvasPunto;

  selectedPoint.subscribe(v => {
    punto = v;
    if (v) setTimeout(() => drawPunto(), 60);
  });

  currentVar.subscribe(v => {
    varActiva = v;
    cfg = VAR_CONFIG[v];
    if (punto) setTimeout(() => drawPunto(), 60);
    cargarRanking();
  });

  currentPeriodo.subscribe(p => {
    periodo = p;
    cargarRanking();
  });

  async function cargarRanking() {
    try {
      const r = await fetch(`${API}/api/provincias/resumen?var=${varActiva}&periodo=${periodo}`);
      const data = await r.json();
      ranking = data.ranking.slice(0, 5);
      rankingUnidades = data.unidades;
    } catch (_) { ranking = null; }
  }

  function fmtVal(x) {
    if (varActiva === 'tp' && punto) return (x * 1000).toFixed(2);
    return x.toFixed(1);
  }

  function etiquetasMeses() {
    // 1997: may-dic | 2023/2024: ene-dic
    return periodo === '1997' ? ['may','ago','dic'] : ['ene','jun','dic'];
  }

  function drawPunto() {
    if (!canvasPunto || !punto) return;
    const ctx = canvasPunto.getContext('2d');
    const W = canvasPunto.offsetWidth || 240;
    const H = canvasPunto.offsetHeight || 90;
    canvasPunto.width = W; canvasPunto.height = H;
    const pad = { t:8, r:8, b:16, l:38 };
    ctx.clearRect(0,0,W,H);

    let vals = punto.serie;
    if (punto.variable === 'tp') vals = vals.map(x => x * 1000);
    const n = vals.length;
    const minV = Math.min(...vals), maxV = Math.max(...vals);
    const rango = (maxV - minV) || 1;
    const toX = i => pad.l+(i/(n-1))*(W-pad.l-pad.r);
    const toY = v => H-pad.b-((v-minV)/rango)*(H-pad.t-pad.b);

    const color = (VAR_CONFIG[punto.variable] || cfg).accent;

    const g = ctx.createLinearGradient(0,pad.t,0,H);
    g.addColorStop(0, color + '38'); g.addColorStop(1, color + '05');
    ctx.beginPath();
    ctx.moveTo(toX(0),toY(vals[0]));
    vals.forEach((v,i) => ctx.lineTo(toX(i),toY(v)));
    ctx.lineTo(toX(n-1),H-pad.b); ctx.lineTo(toX(0),H-pad.b); ctx.closePath();
    ctx.fillStyle=g; ctx.fill();

    ctx.beginPath();
    vals.forEach((v,i) => i===0?ctx.moveTo(toX(i),toY(v)):ctx.lineTo(toX(i),toY(v)));
    ctx.strokeStyle=color; ctx.lineWidth=1.5; ctx.lineJoin='round'; ctx.stroke();

    ctx.strokeStyle='#e2e8f0'; ctx.lineWidth=1;
    ctx.beginPath(); ctx.moveTo(pad.l,pad.t); ctx.lineTo(pad.l,H-pad.b); ctx.stroke();
    ctx.fillStyle='#94a3b8'; ctx.font='10px sans-serif'; ctx.textAlign='right';
    [minV,maxV].forEach(v=>ctx.fillText(v.toFixed(1),pad.l-4,toY(v)+3));
    ctx.textAlign='center';
    etiquetasMeses().forEach((m,i)=>{
      ctx.fillText(m, toX(Math.round(i*(n-1)/2)), H-4);
    });
  }
</script>

<div class="panel">

  <div class="section grow">
    <p class="section-title">Zona seleccionada · {cfg.nombre}</p>

    {#if punto}
      <p class="coords">{punto.lat.toFixed(2)}°, {punto.lon.toFixed(2)}° · {PERIODO_CONFIG[periodo]?.rango ?? periodo}</p>
      <div class="kpis">
        <div class="kpi">
          <span class="kpi-l">Media</span>
          <span class="kpi-v" style="color:{cfg.accent}">{fmtVal(punto.mean)}<s>{cfg.unidades}</s></span>
        </div>
        <div class="kpi">
          <span class="kpi-l">Máxima</span>
          <span class="kpi-v">{fmtVal(punto.max)}<s>{cfg.unidades}</s></span>
        </div>
        <div class="kpi">
          <span class="kpi-l">Mínima</span>
          <span class="kpi-v" style="color:#64748b">{fmtVal(punto.min)}<s>{cfg.unidades}</s></span>
        </div>
      </div>
      <canvas bind:this={canvasPunto} class="chart"></canvas>
    {:else}
      <div class="empty">
        <span class="pin">◎</span>
        <p><strong>Toca cualquier punto del mapa</strong><br/>para el perfil de {cfg.nombre.toLowerCase()} de esa zona en {PERIODO_CONFIG[periodo]?.etiqueta ?? periodo}</p>
      </div>
    {/if}
  </div>

  <div class="section grow">
    <p class="section-title">Provincias más afectadas · {cfg.nombre}</p>
    {#if ranking}
      {@const maxVal = ranking[0]?.valor || 1}
      <div class="prov-list">
        {#each ranking as p, i}
          <div class="prow" class:top={i === 0}>
            <span class="pnum">{i + 1}</span>
            <span class="pname">{p.provincia}</span>
            <div class="ptrack">
              <div class="pfill" style="width:{(p.valor / maxVal * 100).toFixed(0)}%;
                background:{i === 0 ? cfg.accent : i < 3 ? cfg.accentSoft : '#cbd5e1'}"></div>
            </div>
            <span class="pval" style={i === 0 ? `color:${cfg.accent};font-weight:700` : ''}>{p.valor}</span>
          </div>
        {/each}
      </div>
      <p class="prov-note">Promedio {PERIODO_CONFIG[periodo]?.rango ?? periodo} por provincia · {rankingUnidades} · ERA5 + geoBoundaries</p>
    {:else}
      <p class="loading">Cargando ranking…</p>
    {/if}
  </div>

  <div class="section">
    <p class="section-title">Lectura del mapa · {cfg.nombre}</p>
    <div class="gradient-legend">
      <span class="gl-label">{cfg.min}</span>
      <div class="gl-bar" style="background:{cfg.gradiente}"></div>
      <span class="gl-label">{cfg.max}</span>
    </div>
    <div class="gl-hints">
      <span class="gl-hint">{cfg.hintMin}</span>
      <span class="gl-hint" style="margin-left:auto">{cfg.hintMax}</span>
    </div>
  </div>

</div>

<style>
  .panel { display:flex; flex-direction:column; height:100%; overflow:hidden; }

  .section { display:flex; flex-direction:column; padding:.9rem 1.15rem;
             border-bottom:1px solid #eef1f4; flex-shrink:0; }
  .section.grow { flex:1; min-height:0; }
  .section:last-child { border-bottom:none; }

  .section-title {
    font-size:11.5px; font-weight:700; color:#334155;
    text-transform:uppercase; letter-spacing:.05em;
    margin:0 0 .55rem; flex-shrink:0;
  }
  .coords { font-size:11px; color:#94a3b8; margin:0 0 .45rem; flex-shrink:0; }
  .loading { font-size:11px; color:#94a3b8; }

  .kpis { display:grid; grid-template-columns:repeat(3,1fr); gap:7px;
          margin-bottom:.55rem; flex-shrink:0; }
  .kpi  { background:#f8fafc; border:1px solid #e8ecf0; border-radius:7px;
          padding:.45rem .55rem; display:flex; flex-direction:column; }
  .kpi-l { font-size:9px; color:#94a3b8; text-transform:uppercase; }
  .kpi-v { font-size:20px; font-weight:700; color:#1e293b; line-height:1.15; }
  .kpi-v s { font-size:10px; font-weight:400; color:#94a3b8; text-decoration:none; }

  .chart { flex:1; min-height:65px; width:100%; display:block; }

  .empty { display:flex; flex-direction:column; align-items:center; justify-content:center;
           gap:.5rem; flex:1; padding:.5rem; text-align:center; }
  .pin   { font-size:26px; color:#cbd5e1; }
  .empty p { font-size:11.5px; color:#94a3b8; line-height:1.6; margin:0; }
  .empty strong { color:#475569; }

  .prov-list { display:flex; flex-direction:column; gap:6px; overflow:hidden; }
  .prow { display:flex; align-items:center; gap:.5rem; }
  .prow.top .pname { font-weight:700; color:#1e293b; }
  .pnum  { font-size:10px; color:#94a3b8; width:14px; text-align:right; flex-shrink:0; }
  .pname { font-size:11.5px; color:#475569; width:100px; flex-shrink:0;
           white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .ptrack { flex:1; height:8px; background:#eef1f4; border-radius:4px; overflow:hidden; }
  .pfill  { height:100%; border-radius:4px; }
  .pval   { font-size:11px; color:#64748b; width:44px; text-align:right;
            font-variant-numeric:tabular-nums; }
  .prov-note { font-size:9px; color:#b6c2cf; margin:.5rem 0 0; }

  .gradient-legend { display:flex; align-items:center; gap:.5rem; margin-bottom:.35rem; }
  .gl-label { font-size:11px; color:#64748b; white-space:nowrap; }
  .gl-bar   { flex:1; height:10px; border-radius:5px; }
  .gl-hints { display:flex; }
  .gl-hint  { font-size:10px; color:#94a3b8; }
</style>
