<script>
  import { onMount, onDestroy } from 'svelte';
  import { rasterInfo, selectedPoint, currentStep, currentVar, currentPeriodo, VAR_CONFIG } from '../stores/mapState.js';

  const API = 'http://localhost:8000';
  const GEO = { xmin: -81.5, ymin: -5.5, xmax: -75.0, ymax: 2.0 };
  const V = 4;

  let mapDiv, imgOverlay, view, Point;
  let loadingPoint = false;
  let step = 0, varActiva = 't2m', periodo = '1997';
  let preloader = null;
  let montado = false;

  function refreshOverlay() {
    if (!imgOverlay) return;
    const url = `${API}/api/raster/${varActiva}/${step}?periodo=${periodo}&v=${V}`;
    if (!preloader) preloader = new window.Image();
    preloader.onload = () => { imgOverlay.src = url; };
    preloader.src = url;
  }

  async function cargarInfo() {
    const res  = await fetch(`${API}/api/raster/info?periodo=${periodo}`);
    if (!res.ok) return;
    rasterInfo.set(await res.json());
  }

  currentStep.subscribe(v => { step = v; refreshOverlay(); });
  currentVar.subscribe(v  => { varActiva = v; refreshOverlay(); });
  currentPeriodo.subscribe(async p => {
    const cambio = p !== periodo;
    periodo = p;
    if (montado && cambio) {
      currentStep.set(0);          // reinicia la linea de tiempo
      selectedPoint.set(null);     // el punto era de otro periodo
      await cargarInfo();
      refreshOverlay();
    }
  });

  function positionOverlay() {
    if (!view?.ready || !imgOverlay || !Point) return;
    try {
      const tl = view.toScreen(new Point({ longitude: GEO.xmin, latitude: GEO.ymax }));
      const br = view.toScreen(new Point({ longitude: GEO.xmax, latitude: GEO.ymin }));
      if (!tl || !br) return;
      imgOverlay.style.left   = tl.x + 'px';
      imgOverlay.style.top    = tl.y + 'px';
      imgOverlay.style.width  = (br.x - tl.x) + 'px';
      imgOverlay.style.height = (br.y - tl.y) + 'px';
    } catch (_) {}
  }

  onMount(async () => {
    await new Promise(r => setTimeout(r, 120));

    const [
      { default: Map },
      { default: MapView },
      { default: Pt },
      { default: Extent },
      { default: GeoJSONLayer },
    ] = await Promise.all([
      import('@arcgis/core/Map.js'),
      import('@arcgis/core/views/MapView.js'),
      import('@arcgis/core/geometry/Point.js'),
      import('@arcgis/core/geometry/Extent.js'),
      import('@arcgis/core/layers/GeoJSONLayer.js'),
    ]);
    Point = Pt;

    await cargarInfo();

    const provincias = new GeoJSONLayer({
      url: `${API}/api/provincias/geojson`,
      renderer: {
        type: 'simple',
        symbol: {
          type: 'simple-fill',
          color: [0, 0, 0, 0],
          outline: { color: [70, 70, 70, 0.55], width: 0.7 },
        },
      },
      popupEnabled: false,
    });

    const map = new Map({ basemap: 'gray-vector', layers: [provincias] });
    view = new MapView({
      container: mapDiv, map, center: [-78.25, -1.75], zoom: 6,
      ui: { components: ['zoom'] },
    });
    await view.when();

    const extentObj = new Extent({
      xmin: GEO.xmin, ymin: GEO.ymin,
      xmax: GEO.xmax, ymax: GEO.ymax,
      spatialReference: { wkid: 4326 },
    });

    view.constraints = { snapToZoom: false, rotationEnabled: false };
    await view.goTo({ target: extentObj }, { animate: false });

    const va = view.width / view.height;
    const ea = (GEO.xmax - GEO.xmin) / ((GEO.ymax - GEO.ymin) * 1.0015);
    const factor = va > ea ? va / ea : ea / va;
    view.scale = view.scale / 1.05;

    view.constraints = {
      geometry: extentObj,
      minScale: view.scale * 1.3,
      snapToZoom: false,
      rotationEnabled: false,
    };

    view.watch('extent', positionOverlay);
    view.on('resize', positionOverlay);

    view.on('click', async (event) => {
      const { latitude, longitude } = event.mapPoint;
      if (longitude < GEO.xmin || longitude > GEO.xmax ||
          latitude  < GEO.ymin || latitude  > GEO.ymax) return;
      loadingPoint = true;
      try {
        const r = await fetch(`${API}/api/stats/punto?lat=${latitude.toFixed(3)}&lon=${longitude.toFixed(3)}&var=${varActiva}&periodo=${periodo}`);
        selectedPoint.set(await r.json());
      } finally { loadingPoint = false; }
    });

    montado = true;
    positionOverlay();
    refreshOverlay();
  });

  onDestroy(() => { view?.destroy(); });

  function setVar(v) { currentVar.set(v); }
</script>

<div class="map-container">
  <div bind:this={mapDiv} class="map-view"></div>

  <img bind:this={imgOverlay} src="{API}/api/raster/t2m/0?periodo=1997&v={V}"
    alt="Capa climática ERA5" class="raster-overlay" on:load={positionOverlay} />

  <div class="var-selector">
    {#each Object.entries(VAR_CONFIG) as [key, cfg]}
      <button class:active={varActiva === key}
        style={varActiva === key ? `background:${cfg.accent}` : ''}
        on:click={() => setVar(key)}>
        {cfg.nombre}
      </button>
    {/each}
  </div>

  <div class="pan-hint">Desliza verticalmente para recorrer el territorio</div>

  {#if loadingPoint}
    <div class="loading-pill">Analizando zona…</div>
  {/if}
</div>

<style>
  .map-container { position:relative; width:100%; height:100%; overflow:hidden; }
  .map-view      { width:100%; height:100%; }
  .raster-overlay {
    position:absolute; pointer-events:none; opacity:.72;
    top:0; left:0; width:0; height:0;
    mix-blend-mode:multiply;
  }

  .var-selector {
    position:absolute; top:.7rem; right:.7rem; z-index:10;
    display:flex; background:#fff; border:1px solid #d9dee4;
    border-radius:6px; overflow:hidden;
    box-shadow:0 1px 4px rgba(0,0,0,.08);
  }
  .var-selector button {
    border:none; background:none; cursor:pointer;
    font-size:11.5px; padding:6px 13px; color:#64748b;
    font-family:inherit; transition:all .12s;
    border-right:1px solid #eef1f4;
  }
  .var-selector button:last-child { border-right:none; }
  .var-selector button:hover  { background:#f8fafc; color:#1e293b; }
  .var-selector button.active { color:#fff; font-weight:600; }

  .pan-hint {
    position:absolute; bottom:.6rem; left:50%; transform:translateX(-50%);
    background:rgba(255,255,255,.85); color:#94a3b8;
    border:1px solid #e2e8f0;
    font-size:9.5px; padding:2px 10px; border-radius:12px;
    pointer-events:none; z-index:5;
    animation: fadeout 6s forwards;
  }
  @keyframes fadeout { 0%,70% { opacity:1 } 100% { opacity:0 } }

  .loading-pill {
    position:absolute; top:.7rem; left:50%; transform:translateX(-50%);
    background:#0079c1; color:#fff;
    font-size:11px; padding:4px 14px; border-radius:20px; z-index:10;
    box-shadow:0 2px 8px rgba(0,0,0,.15);
  }
</style>
