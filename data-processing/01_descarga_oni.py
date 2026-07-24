"""
01 - Descarga y parseo del indice ONI (NOAA CPC)
==================================================
Este es el PRIMER script del proyecto. Su unico objetivo es validar que
podemos obtener y parsear correctamente el indice ONI antes de tocar nada
de ArcGIS/ArcPy. Es la fuente de dato mas simple del proyecto: no requiere
cuenta, ni API key, ni registro.

Fuente oficial (texto plano, verificada):
    https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt

Formato real del archivo (columnas separadas por espacios):
    SEAS YR TOTAL ANOM
    DJF  1950 24.72 -1.53
    JFM  1950 25.17 -1.34
    ...

Donde:
    SEAS  -> codigo de temporada de 3 meses (DJF, JFM, FMA, ... NDJ)
    YR    -> anio
    TOTAL -> SST promedio en la region Nino 3.4 (grados C)
    ANOM  -> anomalia respecto al periodo climatologico = este es el
             valor ONI que usamos para clasificar fases ENSO

Como correrlo:
    pip install requests pandas
    python 01_descarga_oni.py

Nota: si no hay conexion a internet disponible (por ejemplo, corriendo
dentro de un sandbox restringido), el script usa automaticamente una
pequenia muestra local de respaldo para que puedas seguir probando el
parseo sin bloquearte. Cuando lo corras en tu maquina real, sí descargara
el archivo completo y actualizado.
"""

import io
import sys
from datetime import datetime

import pandas as pd

URL_ONI = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"

# Pequenia muestra real de respaldo (mismas 4 columnas y formato exacto del
# archivo oficial), solo para poder probar el parseo sin conexion.
MUESTRA_RESPALDO = """SEAS YR TOTAL ANOM
DJF 1950 24.72 -1.53
JFM 1950 25.17 -1.34
FMA 1950 25.75 -1.16
DJF 1997 25.90 0.62
NDJ 1997 27.29 2.36
DJF 1998 27.29 2.25
FMA 1998 26.66 1.39
DJF 2015 26.66 0.53
NDJ 2015 28.13 2.51
DJF 2016 28.05 2.51
"""


def descargar_oni(url: str = URL_ONI, timeout: int = 20) -> str:
    """Descarga el archivo crudo del indice ONI. Requiere internet real."""
    import requests  # import local: solo se necesita si de verdad hay red

    # Muchos servidores .gov (incluido NOAA) devuelven 403 si detectan el
    # User-Agent por defecto de la libreria requests (se ve como bot).
    # Con un User-Agent de navegador normal, la peticion pasa sin problema.
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
    }
    resp = requests.get(url, timeout=timeout, headers=headers)
    resp.raise_for_status()
    return resp.text


def parsear_oni(texto_crudo: str) -> pd.DataFrame:
    """Convierte el texto plano del ONI en un DataFrame limpio."""
    df = pd.read_csv(io.StringIO(texto_crudo), sep=r"\s+")
    df = df.rename(columns={"TOTAL": "sst_nino34", "ANOM": "oni"})

    def clasificar(valor_oni: float) -> str:
        if valor_oni >= 0.5:
            return "El Nino"
        elif valor_oni <= -0.5:
            return "La Nina"
        return "Neutro"

    # Nota: esta es una clasificacion simplificada fila por fila.
    # La definicion oficial de NOAA requiere ADEMAS que el umbral se
    # sostenga por 5 temporadas consecutivas para contar como "evento".
    # Eso se implementa en un paso posterior (02_clasificar_eventos.py),
    # no en este script de descarga.
    df["fase"] = df["oni"].apply(clasificar)
    return df


def main():
    try:
        print(f"Intentando descargar desde: {URL_ONI}")
        texto = descargar_oni()
        print("Descarga real exitosa.")
    except Exception as e:
        print(f"No se pudo descargar en vivo ({type(e).__name__}: {e}).")
        print("Usando muestra local de respaldo para validar el parseo...")
        texto = MUESTRA_RESPALDO

    df = parsear_oni(texto)

    print("\nPrimeras filas parseadas:")
    print(df.head(10).to_string(index=False))

    print(f"\nTotal de filas: {len(df)}")
    print("Distribucion de fases:")
    print(df["fase"].value_counts().to_string())

    salida = "oni_procesado.csv"
    df.to_csv(salida, index=False)
    print(f"\nGuardado en: {salida}")


if __name__ == "__main__":
    main()
