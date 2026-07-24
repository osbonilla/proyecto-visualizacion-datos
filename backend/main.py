"""
Backend API — Visualizador El Nino en Ecuador (v4, multi-periodo)
==================================================================
Sirve 1997, 2023 y 2024 con ?periodo=. Raster suave (t2m/tp/viento),
ONI real NOAA, provincias, estadisticas por variable y periodo.
Correr:  uvicorn main:app --reload     Docs: /docs
"""

import io
import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.path as mpath
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

# ── Rutas ────────────────────────────────────────────────────────────────────
# DATA_ROOT = carpeta data-processing (contiene era5_ecuador_1997/, _2023/, _2024/)
DATA_ROOT = Path(os.environ.get(
    "ERA5_DATA_ROOT",
    r"C:\Users\Oldrin\OneDrive\Desktop\Github\proyecto-visualizacion-datos\data-processing",
))

PERIODOS_DEF = {
    "1997": {"carpeta": "era5_ecuador_1997", "etiqueta": "El Niño 1997-98 · extremo"},
    "2023": {"carpeta": "era5_ecuador_2023", "etiqueta": "2023 · transición a El Niño"},
    "2024": {"carpeta": "era5_ecuador_2024", "etiqueta": "2024 · El Niño moderado"},
}

ONI_CSV      = DATA_ROOT / "oni_procesado.csv"
PROV_GEOJSON = Path(__file__).parent / "provincias.geojson"

EXTENT = {"xmin": -81.5, "ymin": -5.5, "xmax": -75.0, "ymax": 2.0}

VARIABLES = {
    "t2m":  {"cmap": "RdYlBu_r", "vmin": 7.5, "vmax": 28.0,  "unidades": "°C"},
    "tp":   {"cmap": "Blues",    "vmin": 0.0, "vmax": 0.007, "unidades": "m"},
    "wind": {"cmap": "viridis",  "vmin": 0.0, "vmax": 10.0,  "unidades": "m/s"},
}

app = FastAPI(title="API El Nino en Ecuador", version="4.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["GET"], allow_headers=["*"])

# ── Cache por (periodo, dataset) ─────────────────────────────────────────────
_cache = {}
_oni_df = None
_prov_masks = None


def _periodos_disponibles():
    out = {}
    for pid, cfg in PERIODOS_DEF.items():
        carpeta = DATA_ROOT / cfg["carpeta"]
        if (carpeta / "t2m_celsius.nc").exists():
            out[pid] = {"etiqueta": cfg["etiqueta"]}
    return out


def _carpeta(periodo: str) -> Path:
    if periodo not in PERIODOS_DEF:
        raise HTTPException(404, f"Periodo '{periodo}' no reconocido. Usa: {list(PERIODOS_DEF)}")
    carpeta = DATA_ROOT / PERIODOS_DEF[periodo]["carpeta"]
    if not (carpeta / "t2m_celsius.nc").exists():
        raise HTTPException(503,
            f"Periodo '{periodo}' sin datos. Corre 05_descarga_era5_reciente.py "
            f"y 06_convertir_celsius.py")
    return carpeta


def _ds(periodo: str, cual: str) -> xr.Dataset:
    """cual: 'celsius' | 'instant' | 'accum'"""
    key = (periodo, cual)
    if key not in _cache:
        c = _carpeta(periodo)
        nombres = {
            "celsius": "t2m_celsius.nc",
            "instant": "data_stream-oper_stepType-instant.nc",
            "accum":   "data_stream-oper_stepType-accum.nc",
        }
        _cache[key] = xr.open_dataset(c / nombres[cual])
    return _cache[key]


def _get_oni_df():
    global _oni_df
    if _oni_df is None:
        _oni_df = pd.read_csv(ONI_CSV)
    return _oni_df


def _get_var_step(periodo, var, step):
    if var == "t2m":
        return _ds(periodo, "celsius")["t2m"].isel(valid_time=step).values
    if var == "tp":
        return _ds(periodo, "accum")["tp"].isel(valid_time=step).values
    if var == "wind":
        d = _ds(periodo, "instant")
        u = d["u10"].isel(valid_time=step).values
        v = d["v10"].isel(valid_time=step).values
        return np.sqrt(u**2 + v**2)
    raise HTTPException(404, f"Variable '{var}' no reconocida.")


def _serie_espacial(periodo, var):
    if var == "t2m":
        return _ds(periodo, "celsius")["t2m"].mean(dim=["latitude", "longitude"]).values
    if var == "tp":
        return _ds(periodo, "accum")["tp"].mean(dim=["latitude", "longitude"]).values * 1000
    d = _ds(periodo, "instant")
    return np.sqrt(d["u10"]**2 + d["v10"]**2).mean(dim=["latitude", "longitude"]).values


def _raster_to_png(data_2d, cmap, vmin, vmax) -> bytes:
    fig, ax = plt.subplots(figsize=(3, 3), dpi=100)
    ax.imshow(data_2d, cmap=cmap,
              norm=mcolors.Normalize(vmin=vmin, vmax=vmax),
              origin="upper", aspect="auto",
              interpolation="bilinear", alpha=0.9)
    ax.axis("off")
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight",
                pad_inches=0, transparent=True, dpi=100)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ── Endpoints ────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "version": "4.0.0",
            "periodos": list(_periodos_disponibles()), "docs": "/docs"}


@app.get("/api/periodos")
def periodos():
    return _periodos_disponibles()


@app.get("/api/raster/info")
def raster_info(periodo: str = "1997"):
    d = _ds(periodo, "celsius")
    ts = [str(t.values)[:19] for t in d.valid_time]
    return {"periodo": periodo, "n_steps": len(ts), "timestamps": ts,
            "extent": EXTENT,
            "variables": {k: {"unidades": v["unidades"], "vmin": v["vmin"], "vmax": v["vmax"]}
                          for k, v in VARIABLES.items()}}


@app.get("/api/raster/{var}/{step}")
def raster_var(var: str, step: int, periodo: str = "1997"):
    if var not in VARIABLES:
        raise HTTPException(404, f"Variable '{var}' no reconocida.")
    n = _ds(periodo, "celsius").sizes["valid_time"]
    if not 0 <= step < n:
        raise HTTPException(404, f"step {step} fuera de rango 0-{n-1}")
    cfg = VARIABLES[var]
    png = _raster_to_png(_get_var_step(periodo, var, step),
                         cfg["cmap"], cfg["vmin"], cfg["vmax"])
    return Response(content=png, media_type="image/png",
                    headers={"Cache-Control": "public, max-age=3600"})


@app.get("/api/oni")
def get_oni():
    df = _get_oni_df()
    return {"serie": df["oni"].tolist(),
            "timestamps": (df["YR"].astype(str) + "-" + df["SEAS"]).tolist(),
            "anios": df["YR"].tolist(),
            "fases": df["fase"].tolist()}


@app.get("/api/oni/actual")
def get_oni_actual():
    row = _get_oni_df().iloc[-1]
    return {"valor_oni": round(float(row["oni"]), 2),
            "fase": str(row["fase"]),
            "periodo": f"{row['SEAS']} {row['YR']}"}


@app.get("/api/stats/mensual")
def stats_mensual_var(var: str = "t2m", periodo: str = "1997"):
    if var not in VARIABLES:
        raise HTTPException(404, f"Variable '{var}' no reconocida.")
    ts = pd.DatetimeIndex(_ds(periodo, "celsius").valid_time.values)
    vals = _serie_espacial(periodo, var)
    df = pd.DataFrame({"t": ts, "v": vals})
    df["mes"] = df["t"].dt.to_period("M").astype(str)
    agg = df.groupby("mes")["v"].sum() if var == "tp" else df.groupby("mes")["v"].mean()
    agg = agg.reset_index()
    unidad = "mm acumulados" if var == "tp" else VARIABLES[var]["unidades"]
    return {"variable": var, "periodo": periodo, "unidades": unidad,
            "meses": agg["mes"].tolist(),
            "valores": [round(float(v), 2) for v in agg["v"]]}


@app.get("/api/stats/punto")
def stats_punto(lat: float, lon: float, var: str = "t2m", periodo: str = "1997"):
    if var == "wind":
        d = _ds(periodo, "instant")
        u = d["u10"].sel(latitude=lat, longitude=lon, method="nearest")
        v = d["v10"].sel(latitude=lat, longitude=lon, method="nearest")
        vals = np.sqrt(u.values**2 + v.values**2)
        la, lo = float(u.latitude.values), float(u.longitude.values)
    else:
        d = _ds(periodo, "celsius") if var == "t2m" else _ds(periodo, "accum")
        campo = "t2m" if var == "t2m" else "tp"
        p = d[campo].sel(latitude=lat, longitude=lon, method="nearest")
        vals = p.values
        la, lo = float(p.latitude.values), float(p.longitude.values)
    ts = [str(t.values)[:10] for t in _ds(periodo, "celsius").valid_time[::4]]
    return {"lat": la, "lon": lo, "variable": var, "periodo": periodo,
            "timestamps": ts,
            "serie": [round(float(x), 4) for x in vals[::4]],
            "mean": round(float(np.nanmean(vals)), 4),
            "max":  round(float(np.nanmax(vals)),  4),
            "min":  round(float(np.nanmin(vals)),  4)}


# ── Provincias ───────────────────────────────────────────────────────────────
def _build_masks():
    global _prov_masks
    if _prov_masks is not None:
        return _prov_masks
    if not PROV_GEOJSON.exists():
        raise HTTPException(503, "Falta provincias.geojson — corre 07_descarga_provincias.py")
    gj = json.loads(PROV_GEOJSON.read_text(encoding="utf-8"))
    # La grilla es identica en todos los periodos (mismo bbox y resolucion)
    d = _ds(next(iter(_periodos_disponibles())), "celsius")
    LON, LAT = np.meshgrid(d.longitude.values, d.latitude.values)
    pts = np.column_stack([LON.ravel(), LAT.ravel()])
    masks = {}
    for feat in gj["features"]:
        nombre = feat["properties"].get("shapeName") or feat["properties"].get("name") or "?"
        geom = feat["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        inside = np.zeros(len(pts), dtype=bool)
        for poly in polys:
            inside |= mpath.Path(np.array(poly[0])).contains_points(pts)
        mask = inside.reshape(LAT.shape)
        if mask.any():
            masks[nombre] = mask
    _prov_masks = masks
    return masks


@app.get("/api/provincias/geojson")
def provincias_geojson():
    if not PROV_GEOJSON.exists():
        raise HTTPException(503, "Falta provincias.geojson")
    return FileResponse(PROV_GEOJSON, media_type="application/geo+json")


@app.get("/api/provincias/resumen")
def provincias_resumen(var: str = "t2m", periodo: str = "1997"):
    if var not in VARIABLES:
        raise HTTPException(404, f"Variable '{var}' no reconocida.")
    masks = _build_masks()
    if var == "t2m":
        campo = _ds(periodo, "celsius")["t2m"].mean(dim="valid_time").values
    elif var == "tp":
        campo = _ds(periodo, "accum")["tp"].sum(dim="valid_time").values * 1000
    else:
        d = _ds(periodo, "instant")
        campo = np.sqrt(d["u10"]**2 + d["v10"]**2).mean(dim="valid_time").values
    filas = []
    for nombre, mask in masks.items():
        vals = campo[mask]
        if len(vals):
            filas.append({"provincia": nombre,
                          "valor": round(float(np.nanmean(vals)), 2),
                          "celdas": int(mask.sum())})
    filas.sort(key=lambda x: x["valor"], reverse=True)
    unidad = "mm acumulados" if var == "tp" else VARIABLES[var]["unidades"]
    return {"variable": var, "periodo": periodo, "unidades": unidad, "ranking": filas}
