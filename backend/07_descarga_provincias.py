"""
07 - Descargar GeoJSON de provincias de Ecuador (geoBoundaries ADM1)
=====================================================================
Fuente abierta: geoBoundaries (CC-BY), nivel ADM1 = provincias.
Guarda provincias.geojson junto a main.py.

Correr desde backend/:
    python 07_descarga_provincias.py
"""

import json
from pathlib import Path

import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (proyecto academico visualizacion)"}
API = "https://www.geoboundaries.org/api/current/gbOpen/ECU/ADM1/"
DESTINO = Path(__file__).parent / "provincias.geojson"


def main():
    print("Consultando metadata de geoBoundaries...")
    meta = requests.get(API, headers=HEADERS, timeout=30).json()
    url = meta["gjDownloadURL"]
    print(f"Descargando GeoJSON: {url}")

    gj = requests.get(url, headers=HEADERS, timeout=60).json()
    n = len(gj.get("features", []))
    print(f"Provincias en el archivo: {n}")

    DESTINO.write_text(json.dumps(gj), encoding="utf-8")
    print(f"Guardado: {DESTINO}")
    print("Listo. Reinicia el backend si estaba corriendo.")


if __name__ == "__main__":
    main()
