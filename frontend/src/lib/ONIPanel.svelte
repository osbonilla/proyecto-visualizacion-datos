<script>
  import { onMount } from 'svelte';
  import { currentStep, rasterInfo, ensoFase } from '../stores/mapState.js';

  const API = 'http://localhost:8000';

  let oniData  = [];
  let eventos  = [];
  let fase     = { fase: 'Cargando...', valor_oni: null };
  let info     = null;
  let step     = 0;

  const unsubFase = ensoFase.subscribe(v => fase = v);
  const unsubInfo = rasterInfo.subscribe(v => info = v);
  const unsubStep = currentStep.subscribe(v => step = v);

  onMount(async () => {
    const [resOni, resFase, resEv] = await Promise.all([
      fetch(`${API}/api/oni`),
      fetch(`${API}/api/oni/actual`),
      fetch(`${API}/api/eventos`),
    ]);
    const oni = await resOni.json();
    oniData   = oni.serie;
    ensoFase.set(await resFase.json());
    eventos   = await resEv.json();
  });

  function faseColor(f) {
    if (f === 'El Nino') return '#e05c3a';
    if (f === 'La Nina') return '#3a8be0';
    return '#888';
  }

  function currentTimestamp() {
    if (!info || !info.timestamps[step]) return '';
    return info.timestamps[step].slice(0, 10);
  }
</script>

<div class="panel">
  <!-- Indicador de fase ENSO -->
  <div class="fase-card">
    <span class="fase-label">Fase ENSO</span>
    <span class="fase-valor" style="color:{faseColor(fase.fase)}">{fase.fase}</span>
    {#if fase.valor_oni !== null}
      <span class="oni-num">ONI: {fase.valor_oni > 0 ? '+' : ''}{fase.valor_oni} °C</span>
    {/if}
  </div>

  <!-- Fecha actual del Time Slider -->
  <div class="fecha-actual">
    <span class="fecha-label">Visualizando</span>
    <span class="fecha-valor">{currentTimestamp()}</span>
  </div>

  <!-- Eventos históricos -->
  <div class="eventos">
    <p class="section-title">Eventos históricos</p>
    {#each eventos as ev}
      <div class="evento-row">
        <span class="ev-dot" style="background:{faseColor('El Nino')}"></span>
        <span class="ev-nombre">{ev.nombre}</span>
        <span class="ev-intensidad">{ev.intensidad}</span>
      </div>
    {/each}
  </div>

  <!-- Comparacion regional -->
  <div class="regiones">
    <p class="section-title">Anomalía 1997-98 por región</p>
    <div class="barra-row">
      <span class="reg-label">Costa</span>
      <div class="barra-bg">
        <div class="barra-fill" style="width:90%;background:#e05c3a"></div>
      </div>
      <span class="reg-val">+85%</span>
    </div>
    <div class="barra-row">
      <span class="reg-label">Sierra</span>
      <div class="barra-bg">
        <div class="barra-fill" style="width:15%;background:#888"></div>
      </div>
      <span class="reg-val">+12%</span>
    </div>
    <div class="barra-row">
      <span class="reg-label">Oriente</span>
      <div class="barra-bg">
        <div class="barra-fill" style="width:35%;background:#3a8be0"></div>
      </div>
      <span class="reg-val">+30%</span>
    </div>
  </div>
</div>

<style>
  .panel {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
    height: 100%;
    background: #0f1117;
    color: #e0e0e0;
    font-family: sans-serif;
    overflow-y: auto;
  }
  .fase-card {
    background: #1a1d27;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .fase-label  { font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: .06em; }
  .fase-valor  { font-size: 22px; font-weight: 600; }
  .oni-num     { font-size: 12px; color: #888; }
  .fecha-actual {
    background: #1a1d27;
    border-radius: 8px;
    padding: 0.6rem 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .fecha-label { font-size: 11px; color: #666; }
  .fecha-valor { font-size: 13px; color: #ccc; font-variant-numeric: tabular-nums; }
  .section-title { font-size: 11px; color: #555; text-transform: uppercase; letter-spacing: .06em; margin: 0 0 6px; }
  .eventos { display: flex; flex-direction: column; gap: 4px; }
  .evento-row {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    padding: 4px 0;
    border-bottom: 1px solid #1e2130;
  }
  .ev-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
  .ev-nombre { flex: 1; color: #ccc; }
  .ev-intensidad { color: #666; font-size: 11px; }
  .regiones { display: flex; flex-direction: column; gap: 8px; }
  .barra-row { display: flex; align-items: center; gap: 8px; font-size: 12px; }
  .reg-label { width: 52px; color: #aaa; }
  .barra-bg  { flex: 1; height: 8px; background: #1e2130; border-radius: 4px; overflow: hidden; }
  .barra-fill { height: 100%; border-radius: 4px; transition: width .3s; }
  .reg-val   { width: 36px; text-align: right; color: #888; font-size: 11px; }
</style>
