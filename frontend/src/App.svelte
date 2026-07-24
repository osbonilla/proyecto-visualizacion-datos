<script>
  import { onMount } from 'svelte';
  import MapView    from './lib/MapView.svelte';
  import TimeBar    from './lib/TimeBar.svelte';
  import LeftPanel  from './lib/LeftPanel.svelte';
  import RightPanel from './lib/RightPanel.svelte';
  import { ensoFase } from './stores/mapState.js';

  const API = 'http://localhost:8000';

  let fase = { fase: '—', valor_oni: null, periodo: '' };
  ensoFase.subscribe(v => fase = v);

  onMount(async () => {
    try {
      const r = await fetch(`${API}/api/oni/actual`);
      ensoFase.set(await r.json());
    } catch (_) {
      ensoFase.set({ fase: 'Sin conexión', valor_oni: null });
    }
  });

  const faseColor = f =>
    f === 'El Nino' ? '#c62828' : f === 'La Nina' ? '#1565c0' : '#546e7a';
</script>

<div class="app">
  <header class="topbar">
    <div class="brand">
      <div>
        <p class="title">El Niño en Ecuador <span class="title-sep">·</span> <span class="title-thin">Visualizador Climático</span></p>
        <p class="sub">Inteligencia climática para gestión de riesgo · Gobiernos locales</p>
      </div>
    </div>

    <div class="enso-block">
      <div>
        <p class="enso-label">Estado ENSO {fase.periodo ? '· ' + fase.periodo : ''}</p>
        <p class="enso-val" style="color:{faseColor(fase.fase)}">
          <span class="enso-dot" style="background:{faseColor(fase.fase)}"></span>
          {fase.fase}
        </p>
      </div>
      {#if fase.valor_oni !== null}
        <div class="sep"></div>
        <div>
          <p class="enso-label">Índice ONI</p>
          <p class="enso-val" style="color:{faseColor(fase.fase)}">{fase.valor_oni > 0 ? '+' : ''}{fase.valor_oni} °C</p>
        </div>
      {/if}
    </div>
  </header>

  <main class="layout">
    <aside class="left"><LeftPanel /></aside>
    <section class="center">
      <div class="map-wrap">
        <div class="map-area"><MapView /></div>
      </div>
      <div class="timebar-area"><TimeBar /></div>
    </section>
    <aside class="right"><RightPanel /></aside>
  </main>
</div>

<style>
  :global(html), :global(body) { height:100%; overflow:hidden; margin:0; padding:0; }
  :global(body) {
    background:#eef1f4;
    font-family:'Segoe UI', 'Avenir Next', -apple-system, sans-serif;
    color:#1e293b;
  }
  :global(#app) { height:100%; width:100%; }
  :global(*), :global(*::before), :global(*::after) { box-sizing:border-box; }

  .app { display:flex; flex-direction:column; width:100%; height:100%; overflow:hidden; }

  .topbar {
    display:flex; align-items:center; justify-content:space-between;
    padding:0 1.5rem; height:56px; flex-shrink:0; gap:1rem;
    background:#fff; border-bottom:1px solid #d9dee4;
  }
  .brand { min-width:0; }
  .title { font-size:16px; font-weight:700; color:#1e293b; white-space:nowrap; margin:0; }
  .title-sep  { color:#cbd5e1; font-weight:400; }
  .title-thin { font-weight:400; color:#64748b; font-size:14px; }
  .sub   { font-size:11px; color:#94a3b8; margin:1px 0 0; white-space:nowrap; }

  .enso-block {
    display:flex; align-items:center; gap:1rem;
    background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px;
    padding:.4rem 1.1rem; flex-shrink:0;
    align-self:center;           /* se centra en el alto del header, no se desborda */
    white-space:nowrap;
  }
  .sep { width:1px; height:28px; background:#e2e8f0; flex-shrink:0; }
  .enso-label { font-size:9.5px; text-transform:uppercase; letter-spacing:.05em;
                color:#94a3b8; margin:0; white-space:nowrap; }
  .enso-val   { font-size:16px; font-weight:700; margin:0; display:flex; align-items:center;
                gap:5px; white-space:nowrap; }
  .enso-dot   { width:8px; height:8px; border-radius:50%; display:inline-block; }

  .layout { display:flex; flex:1; min-height:0; width:100%; overflow:hidden;
            gap:12px; padding:12px; }

  /* Paneles con ancho comodo y acotado: el mapa es el protagonista */
  .left, .right {
    flex:0 0 24%; min-width:250px; max-width:340px;
    background:#fff; border:1px solid #d9dee4; border-radius:10px;
    display:flex; flex-direction:column; overflow:hidden;
  }

  /* El centro toma TODO el espacio restante y el mapa lo llena por
     completo (modo cover: el raster cubre el encuadre; el excedente
     vertical se explora con pan) */
  .center {
    flex:1 1 auto; min-width:0; display:flex; flex-direction:column; overflow:hidden;
    background:#fff; border:1px solid #d9dee4; border-radius:10px;
  }
  .map-wrap {
    flex:1; min-height:0; display:flex;
    padding:10px 10px 0;
  }
  .map-area {
    flex:1; min-width:0;
    position:relative; overflow:hidden;
    border-radius:8px;
    border:1px solid #e2e8f0;
  }
  .timebar-area { height:50px; flex-shrink:0; background:#fff;
                  border-top:1px solid #e8ecf0; border-radius:0 0 10px 10px; }
</style>
