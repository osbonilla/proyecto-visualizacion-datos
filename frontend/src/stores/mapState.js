import { writable } from 'svelte/store';

export const currentStep    = writable(0);
export const currentVar     = writable('t2m');
export const currentPeriodo = writable('1997');
export const rasterInfo     = writable(null);
export const ensoFase       = writable({ fase: '—', valor_oni: null });
export const selectedPoint  = writable(null);

export const VAR_CONFIG = {
  t2m:  { nombre: 'Temperatura',   unidades: '°C',
          min: '7.5 °C', max: '28 °C',
          gradiente: 'linear-gradient(to right,#313695,#74add1,#ffffbf,#f46d43,#a50026)',
          hintMin: 'Andes fríos', hintMax: 'Costa / océano cálido',
          accent: '#c62828', accentSoft: '#ef9a9a',
          tituloMensual: 'Mes crítico de temperatura' },
  tp:   { nombre: 'Precipitación', unidades: 'mm',
          min: '0 mm', max: '7 mm / 6h',
          gradiente: 'linear-gradient(to right,#f7fbff,#9ecae1,#4292c6,#08519c,#08306b)',
          hintMin: 'Sin lluvia', hintMax: 'Lluvia intensa',
          accent: '#1565c0', accentSoft: '#90caf9',
          tituloMensual: 'Mes más lluvioso' },
  wind: { nombre: 'Viento',        unidades: 'm/s',
          min: '0 m/s', max: '10 m/s',
          gradiente: 'linear-gradient(to right,#440154,#3b528b,#21918c,#5ec962,#fde725)',
          hintMin: 'Calma', hintMax: 'Viento fuerte',
          accent: '#00796b', accentSoft: '#80cbc4',
          tituloMensual: 'Mes más ventoso' },
};

export const PERIODO_CONFIG = {
  '1997': { anio: 1997, etiqueta: 'El Niño 1997-98', sub: 'evento extremo · referencia', rango: 'may–dic 1997' },
  '2023': { anio: 2023, etiqueta: '2023',            sub: 'transición a El Niño',        rango: 'ene–dic 2023' },
  '2024': { anio: 2024, etiqueta: '2024',            sub: 'El Niño moderado',            rango: 'ene–dic 2024' },
};
