"""
05 - Descarga ERA5 datos recientes (2023-2024)
===============================================
Complementa el dataset de 1997 con datos recientes para poder
comparar el estado climatico actual (2024) con el evento historico,
y evaluar zonas de vulnerabilidad para 2026.

Requiere:
    - .cdsapirc configurado (mismo que para 02_descarga_era5.py)
    - pip install cdsapi

Produce:
    era5_ecuador_2023.nc  → para contexto de variabilidad reciente
    era5_ecuador_2024.nc  → para evaluacion de vulnerabilidad actual

Correr:
    python 05_descarga_era5_reciente.py
"""

import cdsapi
import os

CARPETA = os.path.dirname(os.path.abspath(__file__))
AREA    = [2.0, -81.5, -5.5, -75.0]  # mismo bounding box que 1997

VARIABLES = [
    "2m_temperature",
    "total_precipitation",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
]

PERIODOS = [
    {
        "anio":   "2023",
        "meses":  ["01","02","03","04","05","06","07","08","09","10","11","12"],
        "target": os.path.join(CARPETA, "era5_ecuador_2023.nc"),
        "descripcion": "2023 completo — ano ENSO activo (La Nina transicion a El Nino)",
    },
    {
        "anio":   "2024",
        "meses":  ["01","02","03","04","05","06","07","08","09","10","11","12"],
        "target": os.path.join(CARPETA, "era5_ecuador_2024.nc"),
        "descripcion": "2024 completo — evento El Nino en desarrollo",
    },
]

DIAS  = [f"{d:02d}" for d in range(1, 32)]
HORAS = ["00:00", "06:00", "12:00", "18:00"]


def descargar_periodo(periodo: dict) -> None:
    if os.path.exists(periodo["target"]):
        print(f"Ya existe: {periodo['target']} — omitiendo.")
        return

    print(f"\nDescargando: {periodo['descripcion']}")
    print(f"Target: {periodo['target']}")

    client = cdsapi.Client()
    client.retrieve(
        "reanalysis-era5-single-levels",
        {
            "product_type": ["reanalysis"],
            "variable":     VARIABLES,
            "year":         [periodo["anio"]],
            "month":        periodo["meses"],
            "day":          DIAS,
            "time":         HORAS,
            "area":         AREA,
            "data_format":  "netcdf",
        },
        periodo["target"],
    )
    print(f"Completado: {periodo['target']}")


if __name__ == "__main__":
    for p in PERIODOS:
        descargar_periodo(p)

    print("\n=== Descarga completa ===")
    print("Siguiente paso: correr 03_inspeccionar_netcdf.py sobre cada archivo")
    print("para confirmar el formato, luego actualizar el backend para servir")
    print("los tres periodos (1997, 2023, 2024) con un parametro ?periodo=")
