<script>
  import { onMount } from 'svelte';
  import { selectedPoint } from '../stores/mapState.js';

  const API = 'http://localhost:8000';

  let mensual   = null;
  let oniData   = null;
  let punto     = null;

  let canvasMes, canvasPunto, canvasOni;

  const unsubPunto = selectedPoint.subscribe(v => {
    punto = v;
    if (v && canvasPunto) drawPunto();
  });

  onMount(async () => {
    const [r1, r2] = await Promise.all([
      fetch(`${API}/api/stats/t2m/mensual`).then(r => r.json()),
      fetch(`${API}/api/oni`).then(r => r.json()),
    ]);
    mensual = r1;
    oniData = r2;
    await new Promise(r => setTimeout(r, 60));
    drawMensual();
    drawOni();
  });

  $: if (punto && canvasPunto) drawPunto();

  // ── PALETA temperatura ────────────────────────────────────────────────────
  function tColor(norm) {
    const t = Math.max(0, Math.min(1, norm));
    if (t < 0.5) {
      const s = t * 2;
      return `rgb(${Math.round(49+206*s)},${Math.round(54+201*s)},${Math.round(149+106*s)})`;
    }
    const s = (t - 0.5) * 2;
    return `rgb(255,${Math.round(255-146*s)},${Math.round(191-191*s)})`;
  }

  function drawMensual() {
    if (!canvasMes || !mensual) return;
    const ctx = canvasMes.getContext('2d');
    const W = canvasMes.width, H = canvasMes.height;
    const pad = { t:8, r:8, b:32, l:38 };
    ctx.clearRect(0,0,W,H);

    const vals = mensual.t2m_mean;
    const meses = mensual.meses;
    const n = vals.length;
    const minV = Math.min(...vals) - 0.5;
    const maxV = Math.max(...vals) + 0.5;
    const bW = (W - pad.l - pad.r) / n;

    // Barras
    vals.forEach((v, i) => {
      const x  = pad.l + i * bW;
      const bh = ((v - minV) / (maxV - minV)) * (H - pad.t - pad.b);
      const y  = H - pad.b - bh;
      const norm = (v - 7.5) / (28 - 7.5);
      ctx.fillStyle = tColor(norm);
      ctx.fillRect(x + 2, y, bW - 4, bh);
      // Valor encima
      ctx.fillStyle = '#ccc';
      ctx.font = '9px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(v.toFixed(1), x + bW/2, y - 2);
    });

    // Eje X — mes/año
    ctx.fillStyle = '#666';
    ctx.font = '9px sans-serif';
    ctx.textAlign = 'center';
    meses.forEach((m, i) => {
      ctx.fillText(m.slice(5), pad.l + i*bW + bW/2, H - pad.b + 12);
    });

    // Eje Y
    ctx.strokeStyle = '#222'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(pad.l, pad.t); ctx.lineTo(pad.l, H-pad.b); ctx.stroke();
    [minV, (minV+maxV)/2, maxV].forEach(v => {
      const y = H - pad.b - ((v-minV)/(maxV-minV))*(H-pad.t-pad.b);
      ctx.fillStyle = '#555'; ctx.font = '9px sans-serif'; ctx.textAlign = 'right';
      ctx.fillText(v.toFixed(0)+'°', pad.l-3, y+3);
    });

    // Linea de max
    const maxI = vals.indexOf(Math.max(...vals));
    const xMax = pad.l + maxI*bW + bW/2;
    ctx.strokeStyle = '#e05c3a'; ctx.setLineDash([3,2]); ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(xMax, pad.t); ctx.lineTo(xMax, H-pad.b); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = '#e05c3a'; ctx.font = '9px sans-serif'; ctx.textAlign = 'center';
    ctx.fillText('↑ pico', xMax, pad.t+8);
  }

  function drawPunto() {
    if (!canvasPunto || !punto) return;
    const ctx = canvasPunto.getContext('2d');
    const W = canvasPunto.width, H = canvasPunto.height;
    const pad = { t:14, r:8, b:28, l:38 };
    ctx.clearRect(0,0,W,H);

    const vals = punto.t2m;
    const n = vals.length;
    const minV = Math.min(...vals) - 0.5;
    const maxV = Math.max(...vals) + 0.5;
    const toX = i => pad.l + (i/(n-1))*(W-pad.l-pad.r);
    const toY = v => H - pad.b - ((v-minV)/(maxV-minV))*(H-pad.t-pad.b);

    // Area
    ctx.beginPath();
    ctx.moveTo(toX(0), toY(vals[0]));
    vals.forEach((v,i) => ctx.lineTo(toX(i), toY(v)));
    ctx.lineTo(toX(n-1), H-pad.b);
    ctx.lineTo(toX(0),   H-pad.b);
    ctx.closePath();
    ctx.fillStyle = 'rgba(224,92,58,.2)';
    ctx.fill();

    // Linea
    ctx.beginPath();
    ctx.moveTo(toX(0), toY(vals[0]));
    vals.forEach((v,i) => ctx.lineTo(toX(i), toY(v)));
    ctx.strokeStyle = '#e05c3a'; ctx.lineWidth = 1.5; ctx.stroke();

    // Eje
    ctx.strokeStyle = '#222'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(pad.l, pad.t); ctx.lineTo(pad.l, H-pad.b);
    ctx.lineTo(W-pad.r, H-pad.b); ctx.stroke();

    // Y labels
    [minV, maxV].forEach(v => {
      const y = toY(v);
      ctx.fillStyle='#555'; ctx.font='9px sans-serif'; ctx.textAlign='right';
      ctx.fillText(v.toFixed(1)+'°', pad.l-3, y+3);
    });

    // titulo
    ctx.fillStyle='#aaa'; ctx.font='9px sans-serif'; ctx.textAlign='center';
    ctx.fillText(`${punto.lat.toFixed(2)}°, ${punto.lon.toFixed(2)}°  ·  media ${punto.mean.toFixed(1)}°C`, W/2, 9);
  }

  function drawOni() {
    if (!canvasOni || !oniData) return;
    const ctx = canvasOni.getContext('2d');
    const W = canvasOni.width, H = canvasOni.height;
    const pad = { t:8, r:30, b:28, l:32 };
    ctx.clearRect(0,0,W,H);

    const serie = oniData.serie;
    const n = serie.length;
    // Tomamos los ultimos 60 valores (~5 años) para mostrar variacion
    const chunk = 60;
    const sub   = serie.slice(Math.max(0, n - chunk));
    const ns    = sub.length;
    const minV  = -2, maxV = 3;
    const toX   = i => pad.l + (i/(ns-1))*(W-pad.l-pad.r);
    const toY   = v => H - pad.b - ((v-minV)/(maxV-minV))*(H-pad.t-pad.b);
    const y0    = toY(0);

    // Relleno positivo (El Nino)
    ctx.beginPath();
    ctx.moveTo(toX(0), y0);
    sub.forEach((v,i) => ctx.lineTo(toX(i), toY(Math.max(0,v))));
    ctx.lineTo(toX(ns-1), y0); ctx.closePath();
    ctx.fillStyle = 'rgba(224,92,58,.3)'; ctx.fill();

    // Relleno negativo (La Nina)
    ctx.beginPath();
    ctx.moveTo(toX(0), y0);
    sub.forEach((v,i) => ctx.lineTo(toX(i), toY(Math.min(0,v))));
    ctx.lineTo(toX(ns-1), y0); ctx.closePath();
    ctx.fillStyle = 'rgba(58,139,224,.3)'; ctx.fill();

    // Linea ONI
    ctx.beginPath();
    sub.forEach((v,i) => i===0 ? ctx.moveTo(toX(i),toY(v)) : ctx.lineTo(toX(i),toY(v)));
    ctx.strokeStyle='#aaa'; ctx.lineWidth=1.2; ctx.stroke();

    // Linea 0
    ctx.strokeStyle='#333'; ctx.setLineDash([3,2]); ctx.lineWidth=1;
    ctx.beginPath(); ctx.moveTo(pad.l,y0); ctx.lineTo(W-pad.r,y0); ctx.stroke();
    ctx.setLineDash([]);

    // Umbrales +0.5 / -0.5
    [0.5, -0.5].forEach(v => {
      const y = toY(v);
      ctx.strokeStyle='#444'; ctx.setLineDash([2,3]); ctx.lineWidth=.5;
      ctx.beginPath(); ctx.moveTo(pad.l,y); ctx.lineTo(W-pad.r,y); ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle='#555'; ctx.font='8px sans-serif'; ctx.textAlign='right';
      ctx.fillText((v>0?'+':'')+v, pad.l-3, y+3);
    });

    // Eje Y
    ctx.fillStyle='#555'; ctx.font='9px sans-serif'; ctx.textAlign='right';
    [minV, maxV].forEach(v => ctx.fillText(v+'°', pad.l-3, toY(v)+3));

    // Leyenda
    ctx.fillStyle='#e05c3a'; ctx.fillRect(W-28, 6, 8, 6);
    ctx.fillStyle='#aaa'; ctx.font='8px sans-serif'; ctx.textAlign='left';
    ctx.fillText('El Niño', W-18, 12);
    ctx.fillStyle='#3a8be0'; ctx.fillRect(W-28, 15, 8, 6);
    ctx.fillStyle='#aaa'; ctx.fillText('La Niña', W-18, 21);
  }
</script>

<div class="panel">

  <!-- PREGUNTA 1: Donde alertar -->
  <div class="pregunta">
    <div class="pregunta-header">
      <span class="num">1</span>
      <span class="titulo">¿Dónde alertar?</span>
    </div>
    <p class="instruccion">Haz clic en cualquier punto del mapa para ver su temperatura durante el evento.</p>

    {#if punto}
      <div class="kpi-row">
        <div class="kpi">
          <span class="kpi-l">Media</span>
          <span class="kpi-v" style="color:#e05c3a">{punto.mean.toFixed(1)}°C</span>
        </div>
        <div class="kpi">
          <span class="kpi-l">Máx</span>
          <span class="kpi-v">{punto.max.toFixed(1)}°C</span>
        </div>
        <div class="kpi">
          <span class="kpi-l">Mín</span>
          <span class="kpi-v">{punto.min.toFixed(1)}°C</span>
        </div>
      </div>
      <p class="chart-lbl">Temperatura en este punto — may a dic 1997</p>
      <canvas bind:this={canvasPunto} width="240" height="100" style="width:100%;height:100px;display:block;background:#0f1117;border-radius:6px"></canvas>
    {:else}
      <div class="placeholder">Ningún punto seleccionado</div>
    {/if}
  </div>

  <!-- PREGUNTA 2: Cuando fue mas intenso -->
  <div class="pregunta">
    <div class="pregunta-header">
      <span class="num">2</span>
      <span class="titulo">¿Cuándo fue más intenso?</span>
    </div>
    {#if mensual}
      {@const maxVal = Math.max(...mensual.t2m_mean)}
      {@const maxMes = mensual.meses[mensual.t2m_mean.indexOf(maxVal)]}
      <div class="alerta">
        <span class="alerta-ico">⚠</span>
        <span>Pico de temperatura en <strong>{maxMes}</strong> — {maxVal.toFixed(1)} °C promedio</span>
      </div>
      <p class="chart-lbl">Temperatura media mensual (°C)</p>
      <canvas bind:this={canvasMes} width="240" height="120" style="width:100%;height:120px;display:block;background:#0f1117;border-radius:6px"></canvas>
    {:else}
      <div class="placeholder">Cargando...</div>
    {/if}
  </div>

  <!-- PREGUNTA 3: Comparacion con otros eventos -->
  <div class="pregunta">
    <div class="pregunta-header">
      <span class="num">3</span>
      <span class="titulo">¿Cómo se compara con otros eventos?</span>
    </div>
    <div class="eventos-compare">
      <div class="ev-item ev-fuerte"><span class="ev-dot" style="background:#e05c3a"></span>1982-83 <span class="ev-tag">muy fuerte</span></div>
      <div class="ev-item ev-fuerte ev-activo"><span class="ev-dot" style="background:#ff8c42"></span>1997-98 <span class="ev-tag ev-tag-act">visualizando</span></div>
      <div class="ev-item ev-fuerte"><span class="ev-dot" style="background:#e05c3a"></span>2015-16 <span class="ev-tag">muy fuerte</span></div>
    </div>
    <p class="chart-lbl">Índice ONI histórico (últimos datos disponibles)</p>
    <canvas bind:this={canvasOni} width="240" height="100" style="width:100%;height:100px;display:block;background:#0f1117;border-radius:6px"></canvas>
    <p class="nota">El 1997-98 fue el evento más intenso del siglo XX. Los tres superaron el umbral crítico de +1.5 °C durante al menos 5 trimestres consecutivos.</p>
  </div>

</div>

<style>
  .panel        { display:flex; flex-direction:column; gap:0; overflow-y:auto; height:100%; }
  .pregunta     { padding:1rem; border-bottom:1px solid #1a1d27; }
  .pregunta-header { display:flex; align-items:center; gap:.5rem; margin-bottom:.5rem; }
  .num          { width:20px; height:20px; border-radius:50%; background:#4a9eff;
                  color:#fff; font-size:11px; font-weight:600; display:flex;
                  align-items:center; justify-content:center; flex-shrink:0; }
  .titulo       { font-size:13px; font-weight:500; color:#e0e0e0; font-family:sans-serif; }
  .instruccion  { font-size:11px; color:#555; margin-bottom:.5rem; font-family:sans-serif; }
  .chart-lbl    { font-size:10px; color:#555; margin:.5rem 0 .25rem; font-family:sans-serif; }
  .placeholder  { font-size:11px; color:#333; padding:.5rem 0; font-family:sans-serif; }
  .kpi-row      { display:grid; grid-template-columns:repeat(3,1fr); gap:6px; margin-bottom:.5rem; }
  .kpi          { background:#1a1d27; border-radius:6px; padding:.4rem .5rem; display:flex; flex-direction:column; }
  .kpi-l        { font-size:9px; color:#555; font-family:sans-serif; }
  .kpi-v        { font-size:16px; font-weight:500; color:#e0e0e0; font-family:sans-serif; }
  .alerta       { background:#1e1710; border:1px solid #3a2a10; border-radius:6px;
                  padding:.4rem .6rem; font-size:11px; color:#d4915a; display:flex;
                  gap:.4rem; align-items:flex-start; margin-bottom:.4rem; font-family:sans-serif; }
  .alerta-ico   { font-size:13px; flex-shrink:0; }
  .alerta strong { color:#e05c3a; }
  .eventos-compare { display:flex; flex-direction:column; gap:4px; margin-bottom:.5rem; }
  .ev-item      { display:flex; align-items:center; gap:.4rem; font-size:11px;
                  color:#888; padding:3px 0; border-bottom:1px solid #111; font-family:sans-serif; }
  .ev-dot       { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
  .ev-tag       { margin-left:auto; font-size:9px; color:#444; }
  .ev-tag-act   { color:#4a9eff; }
  .ev-activo    { color:#ccc; }
  .nota         { font-size:10px; color:#444; line-height:1.5; margin-top:.5rem; font-family:sans-serif; }
</style>
