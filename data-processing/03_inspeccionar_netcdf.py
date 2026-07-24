"""
03 - Inspeccionar el NetCDF descargado (antes de usar ArcPy)
==============================================================
CDS renombra las variables al convertir a NetCDF (nombres cortos), y desde
finales de 2024 el eje de tiempo puede llamarse distinto segun el dataset.
Este script NO necesita ArcGIS ni arcpy -- es Python puro, para confirmar
los nombres reales de variables/dimensiones antes de escribir el codigo
de arcpy.md.MakeNetCDFRasterLayer() (que si requiere esos nombres exactos).

Como correrlo:
    pip install netCDF4
    python 03_inspeccionar_netcdf.py era5_ecuador_1997.nc
"""

import sys
import zipfile
from pathlib import Path

from netCDF4 import Dataset


def _detectar_formato_real(ruta: str) -> str:
    """Revisa los primeros bytes del archivo para saber que es de verdad,
    sin confiar en la extension .nc (CDS a veces entrega un ZIP)."""
    with open(ruta, "rb") as f:
        cabecera = f.read(8)

    if cabecera[:2] == b"PK":
        return "zip"
    if cabecera[:4] == b"CDF\x01" or cabecera[:4] == b"CDF\x02":
        return "netcdf_clasico"
    if cabecera[:4] == b"\x89HDF":
        return "netcdf4_hdf5"
    if cabecera[:4] == b"GRIB":
        return "grib"
    if cabecera[:1] in (b"<", b"{"):
        return "posible_error_html_o_json"
    return f"desconocido (primeros bytes: {cabecera!r})"


def inspeccionar(ruta_nc: str) -> None:
    tamano_mb = Path(ruta_nc).stat().st_size / (1024 * 1024)
    formato = _detectar_formato_real(ruta_nc)
    print(f"Archivo: {ruta_nc}  ({tamano_mb:.2f} MB)")
    print(f"Formato real detectado: {formato}\n")

    if formato == "zip":
        print("CDS entrego un ZIP en vez de un .nc directo (comun al pedir")
        print("varias variables juntas). Extrayendo automaticamente...\n")
        destino = Path(ruta_nc).with_suffix("")  # carpeta sin la extension .nc
        with zipfile.ZipFile(ruta_nc) as z:
            z.extractall(destino)
            archivos = z.namelist()
        print(f"Extraido en: {destino}/")
        for nombre in archivos:
            print(f"  - {nombre}")
        print("\nVuelve a correr este script apuntando a alguno de esos")
        print("archivos .nc extraidos, por ejemplo:")
        if archivos:
            print(f"  python 03_inspeccionar_netcdf.py {destino}/{archivos[0]}")
        return

    if formato == "grib":
        print("El archivo es GRIB, no NetCDF (a pesar de pedir data_format=netcdf).")
        print("Revisa el request en 02_descarga_era5.py: puede que 'data_format'")
        print("no se haya aplicado correctamente para este dataset especifico.")
        print("Alternativa: leerlo con la libreria 'cfgrib' en vez de netCDF4.")
        return

    if formato == "posible_error_html_o_json":
        print("Esto no parece ser un archivo de datos real -- probablemente")
        print("CDS devolvio un mensaje de error. Contenido crudo (primeros 500 caracteres):\n")
        with open(ruta_nc, "r", errors="replace") as f:
            print(f.read(500))
        return

    if formato not in ("netcdf_clasico", "netcdf4_hdf5"):
        print("No se pudo identificar el formato con certeza. Revisa manualmente")
        print("los bytes iniciales impresos arriba antes de continuar.")
        return

    with Dataset(ruta_nc, "r") as ds:
        print("Dimensiones:")
        for nombre, dim in ds.dimensions.items():
            print(f"  - {nombre}: {len(dim)} valores")

        print("\nVariables (nombre_corto -> descripcion larga si existe):")
        for nombre, var in ds.variables.items():
            descripcion = getattr(var, "long_name", "")
            unidades = getattr(var, "units", "")
            print(f"  - {nombre}  [{unidades}]  {descripcion}")

        posibles_tiempo = [n for n in ds.dimensions if "time" in n.lower()]
        if posibles_tiempo:
            nombre_tiempo = posibles_tiempo[0]
            print(f"\nEje de tiempo detectado: '{nombre_tiempo}'")
            print("  -> Usa este nombre exacto en arcpy.md.MakeNetCDFRasterLayer()")
        else:
            print("\nNo se detecto una dimension con 'time' en el nombre; revisa manualmente.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python 03_inspeccionar_netcdf.py <archivo.nc>")
        sys.exit(1)
    inspeccionar(sys.argv[1])
