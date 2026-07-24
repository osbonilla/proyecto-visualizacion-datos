"""
06 - Convertir t2m de Kelvin a Celsius (2023 y 2024)
=====================================================
Replica para los nuevos periodos la conversion que para 1997 se hizo
en ArcGIS Pro: genera t2m_celsius.nc dentro de cada carpeta de periodo,
con la misma estructura que el de 1997.

Correr desde data-processing/:
    python 06_convertir_celsius.py
"""

from pathlib import Path
import xarray as xr

BASE = Path(__file__).parent
CARPETAS = ["era5_ecuador_2023", "era5_ecuador_2024"]

for nombre in CARPETAS:
    carpeta = BASE / nombre
    origen  = carpeta / "data_stream-oper_stepType-instant.nc"
    destino = carpeta / "t2m_celsius.nc"

    if not origen.exists():
        print(f"[{nombre}] NO encontrado {origen} — ¿corriste el inspector para extraer el ZIP?")
        continue
    if destino.exists():
        print(f"[{nombre}] t2m_celsius.nc ya existe — omitiendo.")
        continue

    print(f"[{nombre}] Convirtiendo t2m a Celsius...")
    ds = xr.open_dataset(origen)
    t2m_c = ds["t2m"] - 273.15
    t2m_c.attrs = {"units": "degrees_C", "long_name": "2 metre temperature (Celsius)"}
    out = xr.Dataset({"t2m": t2m_c})
    out.to_netcdf(destino)
    ds.close()
    print(f"[{nombre}] OK -> {destino}")
    print(f"[{nombre}] rango: {float(t2m_c.min()):.2f} a {float(t2m_c.max()):.2f} °C")

print("\nListo. Ahora reemplaza backend/main.py y reinicia el backend.")
