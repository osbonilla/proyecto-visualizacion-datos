"""
02 - Descarga de ERA5 via Copernicus CDS
==========================================
IMPORTANTE: este script NO se puede correr dentro de un sandbox sin acceso
a internet externo. Debe ejecutarse en tu ArcGIS Pro Notebook o en tu
maquina local, con una cuenta CDS ya creada.

Preparacion (una sola vez, ~10 minutos):
    1. Crea una cuenta gratuita en https://cds.climate.copernicus.eu
    2. Entra a https://cds.climate.copernicus.eu/profile y copia tu
       "Personal Access Token".
    3. Crea el archivo ~/.cdsapirc (en tu carpeta de usuario) con:

           url: https://cds.climate.copernicus.eu/api
           key: TU_PERSONAL_ACCESS_TOKEN

       (Desde la migracion de octubre 2024, ya NO se necesita un UID
       separado — solo el token.)
    4. Ve a la pagina del dataset "ERA5 hourly data on single levels"
       en el catalogo CDS, acepta los terminos de uso (Terms of Use) al
       fondo del formulario de descarga. Esto solo se puede hacer una vez,
       manualmente, desde el navegador — no via API.
    5. pip install cdsapi

Sugerencia: antes de confiar en los nombres exactos de parametros de este
script, abre la pagina del dataset en el portal CDS y usa el boton
"Show API request code" — genera el snippet exacto y actualizado para
ese dataset especifico, por si algun nombre de parametro cambio.
"""

import cdsapi

# Bounding box aproximado de Ecuador continental: [Norte, Oeste, Sur, Este]
# Ajustar si se requiere mayor precision o se incluye la region oceanica
# Nino 1+2 en la misma descarga.
AREA_ECUADOR = [2.0, -81.5, -5.5, -75.0]

# Evento piloto de la prueba de concepto (alcance minimo viable, ver
# seccion 5.1 de la propuesta): un solo evento historico, El Nino 1997-98.
ANIO = "1997"
MESES = ["05", "06", "07", "08", "09", "10", "11", "12"]
DIAS = [f"{d:02d}" for d in range(1, 32)]
HORAS = ["00:00", "06:00", "12:00", "18:00"]  # 4 pasos/dia alcanza para el piloto

VARIABLES = [
    "2m_temperature",
    "total_precipitation",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
]


def descargar_era5(target: str = "era5_ecuador_1997.nc") -> None:
    client = cdsapi.Client()

    dataset = "reanalysis-era5-single-levels"
    request = {
        "product_type": ["reanalysis"],
        "variable": VARIABLES,
        "year": [ANIO],
        "month": MESES,
        "day": DIAS,
        "time": HORAS,
        "area": AREA_ECUADOR,
        "data_format": "netcdf",
    }

    print(f"Solicitando a CDS: {dataset}")
    print(f"Variables: {VARIABLES}")
    print(f"Periodo: {ANIO}-{MESES[0]} a {ANIO}-{MESES[-1]}, area {AREA_ECUADOR}")
    client.retrieve(dataset, request, target)
    print(f"Descarga completa: {target}")


if __name__ == "__main__":
    descargar_era5()
