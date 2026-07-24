<script>
  import { onMount } from 'svelte';

  const API = 'http://localhost:8000';

  let resumen  = null;
  let histData = null;
  let serieData = null;
  let canvasHist;
  let canvasSerie;

  onMount(async () => {
    const [r1, r2, r3] = await Promise.all([
      fetch(`${API}/api/stats/t2m/resumen`).then(r => r.json()),
      fetch(`${API}/api/stats/t2m/histograma?bins=15`).then(r => r.json()),
      fetch(`${API}/api/stats/t2m/serie_temporal`).then(r => r.json()),
    ]);
    resumen   = r1;
    histData  = r2;
    serieData = r3;

    // Esperar a que el DOM este listo
    await new Promise(r => setTimeout(r, 50));
    drawHist();
    drawSerie();
  });

  function drawHist() {
    if (!canvasHist || !histData) return;
    const ctx = canvasHist.getContext('2d');
    const w = canvasHist.width, h = canvasHist.height;
    const pad = { t:10, r:10, b:30, l:36 };
    ctx.clearRect(0, 0, w, h);

    const counts = histData.counts;
    const edges  = histData.edges;
    const maxC   = Math.max(...counts);
    const n      = counts.length;
    const barW   = (w - pad.l - pad.r) / n;

    counts.forEach((c, i) => {
      const x = pad.l + i * barW;
      const bh = ((h - pad.t - pad.b) * c) / maxC;
      const y  = h - pad.b - bh;

      // Color por temperatura
      const t = edges[i];
      const norm = (t - 7.5) / (28 - 7.5);
      ctx.fillStyle = tempColor(norm);
      ctx.fillRect(x + 1, y, barW - 2, bh);
    });

    // Ejes
    ctx.strokeStyle = '#333';
    ctx.lineWidth   = 1;
    ctx.beginPath();
    ctx.moveTo(pad.l, pad.t);
    ctx.lineTo(pad.l, h - pad.b);
    ctx.lineTo(w - pad.r, h - pad.b);
    ctx.stroke();

    // Etiquetas eje X
    ctx.fillStyle   = '#888';
    ctx.font        = '10px sans-serif';
    ctx.textAlign   = 'center';
    [0, Math.floor(n/2), n-1].forEach(i => {
      const x = pad.l + i * barW + barW / 2;
      ctx.fillText(edges[i].toFixed(1) + '°', x, h - pad.b + 12);
    });

    // Linea de media
    const meanX = pad.l + ((histData.mean - edges[0]) / (edges[edges.length-1] - edges[0])) * (w - pad.l - pad.r);
    ctx.strokeStyle = '#fff';
    ctx.setLineDash([4, 3]);
    ctx.lineWidth   = 1;
    ctx.beginPath();
    ctx.moveTo(meanX, pad.t);
    ctx.lineTo(meanX, h - pad.b);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle   = '#fff';
    ctx.font        = '10px sans-serif';
    ctx.textAlign   = 'left';
    ctx.fillText(`μ=${histData.mean}°`, meanX + 3, pad.t + 12);
  }

  function drawSerie() {
    if (!canvasSerie || !serieData) return;
    const ctx = canvasSerie.getContext('2d');
    const w = canvasSerie.width, h = canvasSerie.height;
    const pad = { t:10, r:10, b:30, l:40 };
    ctx.clearRect(0, 0, w, h);

    const vals = serieData.t2m_mean;
    const n    = vals.length;
    const minV = Math.min(...vals);
    const maxV = Math.max(...vals);
    const rangeV = maxV - minV || 1;

    const toX = i => pad.l + (i / (n - 1)) * (w - pad.l - pad.r);
    const toY = v => h - pad.b - ((v - minV) / rangeV) * (h - pad.t - pad.b);

    // Area bajo la curva
    ctx.beginPath();
    ctx.moveTo(toX(0), toY(vals[0]));
    vals.forEach((v, i) => ctx.lineTo(toX(i), toY(v)));
    ctx.lineTo(toX(n-1), h - pad.b);
    ctx.lineTo(toX(0),   h - pad.b);
    ctx.closePath();
    ctx.fillStyle = 'rgba(224, 92, 58, 0.18)';
    ctx.fill();

    // Linea
    ctx.beginPath();
    ctx.moveTo(toX(0), toY(vals[0]));
    vals.forEach((v, i) => ctx.lineTo(toX(i), toY(v)));
    ctx.strokeStyle = '#e05c3a';
    ctx.lineWidth   = 1.5;
    ctx.stroke();

    // Ejes
    ctx.strokeStyle = '#333';
    ctx.lineWidth   = 1;
    ctx.beginPath();
    ctx.moveTo(pad.l, pad.t);
    ctx.lineTo(pad.l, h - pad.b);
    ctx.lineTo(w - pad.r, h - pad.b);
    ctx.stroke();

    // Etiquetas Y
    ctx.fillStyle   = '#888';
    ctx.font        = '10px sans-serif';
    ctx.textAlign   = 'right';
    [minV, (minV+maxV)/2, maxV].forEach(v => {
      const y = toY(v);
      ctx.fillText(v.toFixed(1) + '°', pad.l - 4, y + 3);
      ctx.strokeStyle = '#222';
      ctx.lineWidth   = 0.5;
      ctx.beginPath();
      ctx.moveTo(pad.l, y);
      ctx.lineTo(w - pad.r, y);
      ctx.stroke();
    });

    // Etiquetas X (meses)
    ctx.fillStyle = '#888';
    ctx.textAlign = 'center';
    const ts = serieData.timestamps;
    const labelIdxs = [0, Math.floor(n*0.25), Math.floor(n*0.5), Math.floor(n*0.75), n-1];
    labelIdxs.forEach(i => {
      const lbl = ts[i] ? ts[i].slice(5, 7) + '/' + ts[i].slice(0, 4) : '';
      ctx.fillText(lbl, toX(i), h - pad.b + 12);
    });
  }

  function tempColor(norm) {
    // RdYlBu_r simplificado: azul->blanco->amarillo->rojo
    const t = Math.max(0, Math.min(1, norm));
    if (t < 0.5) {
      const s = t * 2;
      return `rgb(${Math.round(49+206*s)},${Math.round(54+201*s)},${Math.round(149+106*s)})`;
    } else {
      const s = (t - 0.5) * 2;
      return `rgb(${Math.round(255)},${Math.round(255-146*s)},${Math.round(191-191*s)})`;
    }
  }
</script>

<div class="stats">
  <p class="section-title">Estadística descriptiva · Temperatura 1997</p>

  {#if resumen}
    <div class="kpi-grid">
      <div class="kpi"><span class="kpi-lbl">Media</span><span class="kpi-val">{resumen.mean}°C</span></div>
      <div class="kpi"><span class="kpi-lbl">Desv. Est.</span><span class="kpi-val">±{resumen.std}°</span></div>
      <div class="kpi"><span class="kpi-lbl">Mín</span><span class="kpi-val">{resumen.min}°C</span></div>
      <div class="kpi"><span class="kpi-lbl">Máx</span><span class="kpi-val">{resumen.max}°C</span></div>
      <div class="kpi"><span class="kpi-lbl">P25</span><span class="kpi-val">{resumen.p25}°</span></div>
      <div class="kpi"><span class="kpi-lbl">Mediana</span><span class="kpi-val">{resumen.median}°</span></div>
    </div>
  {/if}

  <p class="chart-lbl">Distribución de temperatura (EDA)</p>
  <canvas bind:this={canvasHist} width="240" height="110" style="width:100%;height:110px"></canvas>

  <p class="chart-lbl" style="margin-top:.75rem">Evolución temporal de temperatura media</p>
  <canvas bind:this={canvasSerie} width="240" height="110" style="width:100%;height:110px"></canvas>
</div>

<style>
  .stats         { padding:1rem; font-family:sans-serif; }
  .section-title { font-size:11px; color:#555; text-transform:uppercase; letter-spacing:.06em; margin:0 0 .75rem; }
  .chart-lbl     { font-size:11px; color:#666; margin:.5rem 0 .25rem; }
  .kpi-grid      { display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-bottom:.75rem; }
  .kpi           { background:#1a1d27; border-radius:6px; padding:.45rem .6rem;
                   display:flex; flex-direction:column; gap:1px; }
  .kpi-lbl       { font-size:10px; color:#555; text-transform:uppercase; letter-spacing:.04em; }
  .kpi-val       { font-size:16px; font-weight:500; color:#e0e0e0; }
  canvas         { display:block; background:#0f1117; border-radius:6px; }
</style>
