<script>
  import { currentStep, rasterInfo } from '../stores/mapState.js';

  let info = null, step = 0, playing = false;
  let playInterval;

  rasterInfo.subscribe(v => info = v);
  currentStep.subscribe(v => step = v);

  function setStep(n) {
    if (!info) return;
    currentStep.set(Math.max(0, Math.min(n, info.n_steps - 1)));
  }
  function togglePlay() {
    if (playing) { stopPlay(); return; }
    playing = true;
    playInterval = setInterval(() => {
      currentStep.update(s => {
        const next = s + 1;
        if (next >= (info?.n_steps ?? 1)) { stopPlay(); return 0; }
        return next;
      });
    }, 300);
  }
  function stopPlay() { playing = false; clearInterval(playInterval); }

  function fmt(ts, withTime = true) {
    if (!ts) return '';
    const d = new Date(ts);
    return withTime
      ? d.toLocaleString('es-EC', { day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit' })
      : d.toLocaleString('es-EC', { month:'short', year:'numeric' });
  }
</script>

{#if info}
<div class="timebar">
  <button class="play-btn" class:playing on:click={togglePlay}
    title={playing ? 'Pausar' : 'Reproducir animación'}>
    {playing ? '⏸' : '▶'}
  </button>

  <span class="ts-current">{fmt(info.timestamps[step])}</span>

  <div class="slider-wrap">
    <input type="range" min="0" max={info.n_steps - 1} value={step}
      on:input={e => setStep(Number(e.target.value))} />
    <div class="range-labels">
      <span>{fmt(info.timestamps[0], false)}</span>
      <span>{fmt(info.timestamps[info.n_steps - 1], false)}</span>
    </div>
  </div>

  <span class="count">{step + 1} / {info.n_steps}</span>
</div>
{/if}

<style>
  .timebar { display:flex; align-items:center; gap:.9rem; height:46px; padding:0 1.1rem; }

  .play-btn {
    width:30px; height:30px; border-radius:50%;
    background:#fff; border:1px solid #cbd5e1; color:#0079c1;
    cursor:pointer; font-size:12px; flex-shrink:0;
    display:flex; align-items:center; justify-content:center;
    transition:all .15s;
  }
  .play-btn:hover   { border-color:#0079c1; background:#f0f9ff; }
  .play-btn.playing { background:#0079c1; color:#fff; border-color:#0079c1; }

  .ts-current { font-size:12px; color:#334155; font-weight:600;
                min-width:130px; flex-shrink:0; font-variant-numeric:tabular-nums; }

  .slider-wrap { flex:1; min-width:0; display:flex; flex-direction:column; gap:1px; }
  input[type=range] { width:100%; height:4px; accent-color:#0079c1; cursor:pointer; margin:0; }
  .range-labels { display:flex; justify-content:space-between; font-size:9px; color:#94a3b8; }

  .count { font-size:10px; color:#94a3b8; flex-shrink:0; font-variant-numeric:tabular-nums; }
</style>
