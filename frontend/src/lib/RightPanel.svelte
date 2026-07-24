<script>
  import { onMount } from 'svelte';
  import { currentVar, currentPeriodo, VAR_CONFIG, PERIODO_CONFIG } from '../stores/mapState.js';

  const API = 'http://localhost:8000';
  const NOMBRES_MES = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];

  let mensual = null, oniData = null;
  let cfg = VAR_CONFIG['t2m'];
  let varActiva = 't2m', periodo = '1997';
  let disponibles = {};
  let canvasMes, canvasOni;

  currentVar.subscribe(v => {
    varActiva = v; cfg = VAR_CONFIG[v];
    cargarMensual();
  });
  currentPeriodo.subscribe(p => {
    periodo = p;
    cargarMensual();
    if (oniData) setTimeout(() => drawOni(), 60);
  });

  async function cargarMensual() {
    try {
      const r = await fetch(`${API}/api/stats/mensual?var=${varActiva}&periodo=${periodo}`);
      mensual = await r.json();
      setTimeout(() => drawMensual(), 60);
    } catch (_) {}
  }

  onMount(async () => {
    try {
      const [r1, r2] = await Promise.all([
        fetch(`${API}/api/oni`).then(r => r.json()),
        fetch(`${API}/api/periodos`).then(r => r.json()),
      ]);
      oniData = r1;
      disponibles = r2;
      setTimeout(() => drawOni(), 60);
    } catch (_) {}
  });

  function elegirPeriodo(p) {
    if (disponibles[p]) currentPeriodo.set(p);
  }

  function rr(ctx,x,y,w,h,r){
    ctx.beginPath();
    ctx.moveTo(x+r,y); ctx.lineTo(x+w-r,y);
    ctx.arcTo(x+w,y,x+w,y+r,r); ctx.lineTo(x+w,y+h);
    ctx.lineTo(x,y+h); ctx.lineTo(x,y+r);
    ctx.arcTo(x,y,x+r,y,r); ctx.closePath();
  }

  function drawMensual() {
    if (!canvasMes || !mensual) return;
    const ctx = canvasMes.getContext('2d');
    const W = canvasMes.offsetWidth||240, H = canvasMes.offsetHeight||110;
    canvasMes.width=W; canvasMes.height=H;
    const pad={t:30,r:6,b:24,l:36};
    ctx.clearRect(0,0,W,H);

    const vals=mensual.valores, meses=mensual.meses, n=vals.length;
    const minV=Math.min(...vals)*0.94, maxV=Math.max(...vals)*1.08;
    const bW=(W-pad.l-pad.r)/n;
    const maxI=vals.indexOf(Math.max(...vals));
    const accent = cfg.accent;

    [.33,.66].forEach(f=>{
      const y=pad.t+f*(H-pad.t-pad.b);
      ctx.strokeStyle='#eef1f4'; ctx.lineWidth=1;
      ctx.beginPath(); ctx.moveTo(pad.l,y); ctx.lineTo(W-pad.r,y); ctx.stroke();
    });

    const mostrarVal = n <= 9;   // con 12 meses los numeros no caben
    vals.forEach((v,i)=>{
      const x=pad.l+i*bW+1.5;
      const bh=((v-minV)/(maxV-minV))*(H-pad.t-pad.b);
      const y=H-pad.b-bh;
      const t = (v - Math.min(...vals)) / ((Math.max(...vals) - Math.min(...vals)) || 1);
      ctx.fillStyle = i===maxI ? accent : cfg.accentSoft;
      ctx.globalAlpha = i===maxI ? 1 : 0.45 + 0.5 * t;
      rr(ctx,x,y,Math.max(bW-3,2),bh,2); ctx.fill();
      ctx.globalAlpha=1;
      if (mostrarVal || i===maxI) {
        ctx.fillStyle=i===maxI?accent:'#64748b';
        ctx.font=`${i===maxI?'bold ':''}9px sans-serif`;
        ctx.textAlign='center';
        // La barra pico deja 14px extra encima para el numero, y el
        // rotulo "PICO" va aparte, mas arriba, sin solaparse nunca.
        ctx.fillText(v.toFixed(1),x+(bW-3)/2,i===maxI ? y-14 : y-3);
      }
      ctx.fillStyle=i===maxI?'#1e293b':'#94a3b8';
      ctx.font='8px sans-serif'; ctx.textAlign='center';
      ctx.fillText(NOMBRES_MES[parseInt(meses[i].slice(5,7),10)-1],x+(bW-3)/2,H-pad.b+11);
    });
    if(maxI>=0){
      ctx.fillStyle=accent; ctx.font='bold 8px sans-serif'; ctx.textAlign='center';
      ctx.fillText('▲ PICO',pad.l+maxI*bW+bW/2,pad.t-18);
    }
    ctx.strokeStyle='#e2e8f0'; ctx.lineWidth=1;
    ctx.beginPath(); ctx.moveTo(pad.l,pad.t); ctx.lineTo(pad.l,H-pad.b); ctx.stroke();
    ctx.fillStyle='#94a3b8'; ctx.font='9px sans-serif'; ctx.textAlign='right';
    const dec = (maxV - minV) < 5 ? 1 : 0;
    [minV,maxV].forEach(v=>{
      const y=H-pad.b-((v-minV)/(maxV-minV))*(H-pad.t-pad.b);
      ctx.fillText(v.toFixed(dec),pad.l-3,y+3);
    });
  }

  function drawOni() {
    if (!canvasOni || !oniData) return;
    const ctx=canvasOni.getContext('2d');
    const W=canvasOni.offsetWidth||240, H=canvasOni.offsetHeight||100;
    canvasOni.width=W; canvasOni.height=H;
    const pad={t:6,r:6,b:18,l:28};
    ctx.clearRect(0,0,W,H);

    // Ventana centrada en el periodo seleccionado: [anio-4, anio+3]
    const anio = PERIODO_CONFIG[periodo]?.anio ?? 1997;
    const anios = oniData.anios;
    let i0 = anios.findIndex(a => a >= anio - 4);
    let i1 = anios.findIndex(a => a > anio + 3);
    if (i0 < 0) i0 = 0;
    if (i1 < 0) i1 = anios.length;
    const sub  = oniData.serie.slice(i0, i1);
    const subA = anios.slice(i0, i1);
    const ns = sub.length;
    if (!ns) return;

    const minV=-2.8, maxV=3;
    const toX=i=>pad.l+(i/(ns-1))*(W-pad.l-pad.r);
    const toY=v=>H-pad.b-((v-minV)/(maxV-minV))*(H-pad.t-pad.b);
    const y0=toY(0);

    // Banda del anio del evento
    const e0 = subA.findIndex(a => a === anio);
    let e1 = subA.findIndex(a => a === anio + 2);   // evento cruza el anio siguiente
    if (e1 < 0) e1 = ns - 1;
    if (e0 >= 0) {
      ctx.fillStyle = 'rgba(255,193,7,.12)';
      ctx.fillRect(toX(e0), pad.t, toX(e1)-toX(e0), H-pad.t-pad.b);
    }

    const gP=ctx.createLinearGradient(0,pad.t,0,y0);
    gP.addColorStop(0,'rgba(198,40,40,.35)'); gP.addColorStop(1,'rgba(198,40,40,.02)');
    ctx.beginPath(); ctx.moveTo(toX(0),y0);
    sub.forEach((v,i)=>ctx.lineTo(toX(i),toY(Math.max(0,v))));
    ctx.lineTo(toX(ns-1),y0); ctx.closePath(); ctx.fillStyle=gP; ctx.fill();

    const gN=ctx.createLinearGradient(0,y0,0,H-pad.b);
    gN.addColorStop(0,'rgba(21,101,192,.02)'); gN.addColorStop(1,'rgba(21,101,192,.35)');
    ctx.beginPath(); ctx.moveTo(toX(0),y0);
    sub.forEach((v,i)=>ctx.lineTo(toX(i),toY(Math.min(0,v))));
    ctx.lineTo(toX(ns-1),y0); ctx.closePath(); ctx.fillStyle=gN; ctx.fill();

    ctx.beginPath();
    sub.forEach((v,i)=>i===0?ctx.moveTo(toX(i),toY(v)):ctx.lineTo(toX(i),toY(v)));
    ctx.strokeStyle='#64748b'; ctx.lineWidth=1.1; ctx.lineJoin='round'; ctx.stroke();

    [.5,-.5].forEach(v=>{
      ctx.strokeStyle='#cbd5e1'; ctx.setLineDash([3,2]); ctx.lineWidth=.7;
      ctx.beginPath(); ctx.moveTo(pad.l,toY(v)); ctx.lineTo(W-pad.r,toY(v)); ctx.stroke();
      ctx.setLineDash([]);
    });
    ctx.strokeStyle='#94a3b8'; ctx.lineWidth=1;
    ctx.beginPath(); ctx.moveTo(pad.l,y0); ctx.lineTo(W-pad.r,y0); ctx.stroke();

    // Eje X: anios
    ctx.fillStyle='#94a3b8'; ctx.font='8px sans-serif'; ctx.textAlign='center';
    let ultimo = null;
    subA.forEach((a,i) => {
      if (a !== ultimo && a % 2 === 0) {
        ctx.fillText(a, toX(i), H-6);
        ultimo = a;
      } else if (a !== ultimo) { ultimo = a; }
    });

    ctx.fillStyle='#94a3b8'; ctx.font='9px sans-serif'; ctx.textAlign='right';
    [-2,0,2].forEach(v=>ctx.fillText(v,pad.l-3,toY(v)+3));
  }
</script>

<div class="panel">

  <div class="section grow">
    <p class="section-title">{cfg.tituloMensual}</p>
    <p class="subtitle">{mensual ? `Agregado mensual · ${mensual.unidades} · ${PERIODO_CONFIG[periodo]?.rango ?? periodo}` : ''}</p>
    {#if mensual}
      <canvas bind:this={canvasMes} class="chart"></canvas>
    {:else}
      <p class="loading">Cargando…</p>
    {/if}
  </div>

  <div class="section grow">
    <p class="section-title">Ciclo El Niño / La Niña</p>
    <p class="subtitle">Índice ONI · umbral ±0.5 °C · NOAA · ventana del periodo</p>
    <canvas bind:this={canvasOni} class="chart"></canvas>
    <div class="legend-row">
      <span class="leg"><span class="lsq" style="background:#c62828"></span>El Niño</span>
      <span class="leg"><span class="lsq" style="background:#1565c0"></span>La Niña</span>
      <span class="leg"><span class="lsq" style="background:#ffc107;opacity:.5"></span>Periodo visualizado</span>
    </div>
  </div>

  <div class="section">
    <p class="section-title">Explorar periodo</p>
    <div class="per-list">
      {#each Object.entries(PERIODO_CONFIG) as [pid, pc]}
        {@const activo = pid === periodo}
        {@const existe = !!disponibles[pid]}
        <button class="per-btn" class:activo class:falta={!existe}
          on:click={() => elegirPeriodo(pid)} disabled={!existe}>
          <span class="per-nombre">{pc.etiqueta}</span>
          <span class="per-sub">{existe ? pc.sub : 'datos no descargados'}</span>
          {#if activo}<span class="per-check">●</span>{/if}
        </button>
      {/each}
    </div>
    <p class="ev-note">Cada periodo carga su propio cubo ERA5. Comparar qué provincias se repiten en el ranking entre eventos revela las zonas de vulnerabilidad estructural.</p>
  </div>

</div>

<style>
  .panel { display:flex; flex-direction:column; height:100%; overflow:hidden; }

  .section { padding:.8rem 1rem; border-bottom:1px solid #eef1f4;
             display:flex; flex-direction:column; flex-shrink:0; }
  .section.grow { flex:1; min-height:0; }
  .section:last-child { border-bottom:none; }

  .section-title { font-size:12.5px; font-weight:700; color:#1e293b; margin:0 0 .1rem; flex-shrink:0; }
  .subtitle { font-size:9.5px; color:#94a3b8; text-transform:uppercase;
              letter-spacing:.05em; margin:0 0 .4rem; flex-shrink:0; }
  .loading { font-size:11px; color:#94a3b8; }

  .chart { flex:1; min-height:60px; width:100%; display:block; }

  .legend-row { display:flex; gap:12px; margin-top:.3rem; flex-shrink:0; flex-wrap:wrap; }
  .leg  { display:flex; align-items:center; gap:4px; font-size:9.5px; color:#64748b; }
  .lsq  { width:9px; height:6px; border-radius:1px; }

  .per-list { display:flex; flex-direction:column; gap:6px; }
  .per-btn {
    display:flex; flex-direction:column; align-items:flex-start; position:relative;
    border:1px solid #e2e8f0; border-radius:8px; background:#fff;
    padding:.5rem .7rem; cursor:pointer; font-family:inherit; text-align:left;
    transition:all .12s;
  }
  .per-btn:hover:not(:disabled) { border-color:#0079c1; background:#f8fbff; }
  .per-btn.activo { border-color:#0079c1; background:#f0f7ff; }
  .per-btn.falta  { opacity:.45; cursor:not-allowed; }
  .per-nombre { font-size:12px; font-weight:700; color:#1e293b; }
  .per-sub    { font-size:9.5px; color:#94a3b8; }
  .per-check  { position:absolute; right:.7rem; top:50%; transform:translateY(-50%);
                color:#0079c1; font-size:11px; }
  .ev-note { font-size:9.5px; color:#94a3b8; margin:.55rem 0 0; line-height:1.55; }
</style>
