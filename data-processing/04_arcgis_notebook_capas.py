"""
04 - Cargar ERA5 como capas multidimensionales en ArcGIS Pro
==============================================================
Este NO es un script para correr por terminal -- es para pegar celda por
celda dentro de un Notebook de ArcGIS Pro (Insert > New Notebook), donde
arcpy ya esta disponible.

Basado en la estructura REAL confirmada de tus archivos (paso anterior):

  data_stream-oper_stepType-instant.nc
    dimensiones: valid_time (980), latitude (31), longitude (27)
    variables:   t2m, u10, v10

  data_stream-oper_stepType-accum.nc
    dimensiones: valid_time (980), latitude (31), longitude (27)
    variables:   tp
"""

# ============================================================
# CELDA 1 - Configuracion inicial y verificacion de rutas
# ============================================================
import arcpy
import os

# AJUSTA esta ruta a donde tengas la carpeta extraida en tu maquina
CARPETA_DATOS = r"C:\Users\Oldrin\OneDrive\Desktop\Github\proyecto-visualizacion-datos\data-processing\era5_ecuador_1997"

NC_INSTANT = os.path.join(CARPETA_DATOS, "data_stream-oper_stepType-instant.nc")
NC_ACCUM = os.path.join(CARPETA_DATOS, "data_stream-oper_stepType-accum.nc")

print("instant.nc existe:", os.path.exists(NC_INSTANT))
print("accum.nc existe:  ", os.path.exists(NC_ACCUM))


# ============================================================
# CELDA 2 - Verificacion multidimensional (usando arcpy.Raster directo)
# ============================================================
# El segundo argumento "True" le dice a arcpy que lo trate como raster
# multidimensional (no como una imagen plana de una sola banda).
raster_instant = arcpy.Raster(NC_INSTANT, True)
raster_accum = arcpy.Raster(NC_ACCUM, True)

print("instant.nc es multidimensional:", raster_instant.isMultidimensional)
print("Variables en instant.nc:", raster_instant.variables)
print()
print("accum.nc es multidimensional:", raster_accum.isMultidimensional)
print("Variables en accum.nc:", raster_accum.variables)

# Si esto imprime True y las variables esperadas (t2m, u10, v10 / tp),
# ArcGIS ya reconocio correctamente el eje de tiempo y podemos continuar.


# ============================================================
# CELDA 3 - Capa multidimensional de temperatura (t2m)
# ============================================================
resultado_t2m = arcpy.md.MakeMultidimensionalRasterLayer(
    in_multidimensional_raster=NC_INSTANT,
    out_multidimensional_raster_layer="t2m_layer",
    variables="t2m",
)
capa_t2m = resultado_t2m.getOutput(0)
print("Capa t2m creada:", capa_t2m)


# ============================================================
# CELDA 4 - Capas de viento (u10, v10)
# ============================================================
resultado_u10 = arcpy.md.MakeMultidimensionalRasterLayer(
    in_multidimensional_raster=NC_INSTANT,
    out_multidimensional_raster_layer="u10_layer",
    variables="u10",
)
capa_u10 = resultado_u10.getOutput(0)

resultado_v10 = arcpy.md.MakeMultidimensionalRasterLayer(
    in_multidimensional_raster=NC_INSTANT,
    out_multidimensional_raster_layer="v10_layer",
    variables="v10",
)
capa_v10 = resultado_v10.getOutput(0)

print("Capas de viento creadas:", capa_u10, capa_v10)


# ============================================================
# CELDA 5 - Capa de precipitacion (tp), del archivo accum
# ============================================================
resultado_tp = arcpy.md.MakeMultidimensionalRasterLayer(
    in_multidimensional_raster=NC_ACCUM,
    out_multidimensional_raster_layer="tp_layer",
    variables="tp",
)
capa_tp = resultado_tp.getOutput(0)
print("Capa tp creada:", capa_tp)


# ============================================================
# CELDA 6 - Agregar las capas al mapa activo para verlas
# ============================================================
aprx = arcpy.mp.ArcGISProject("CURRENT")
mapa = aprx.activeMap

for capa in [capa_t2m, capa_u10, capa_v10, capa_tp]:
    mapa.addLayer(capa)

print("Listo. Deberias ver 4 capas nuevas en el panel de Contenido.")
print("Para confirmar el Time Slider: clic derecho en 't2m_layer' >")
print("Properties > Time -- deberia detectar 'valid_time' automaticamente")
print("(porque el archivo ya trae unidades CF estandar: 'seconds since 1970-01-01').")


# ============================================================
# CELDA 7 - Convertir temperatura de Kelvin a Celsius
# ============================================================
# ArcGIS Pro aplica el algebra de raster respetando la estructura
# multidimensional (afecta TODAS las capas de tiempo a la vez, no solo
# la primera).
capa_t2m_c = arcpy.Raster(capa_t2m) - 273.15
capa_t2m_c.save("t2m_celsius")

mapa.addLayer(arcpy.management.MakeMultidimensionalRasterLayer(
    "t2m_celsius", "t2m_celsius_layer"
).getOutput(0))

print("Capa t2m_celsius creada y agregada al mapa.")


# ============================================================
# CELDA 8 - Verificacion rapida de rango de valores
# ============================================================
# Ecuador continental deberia rondar 15-30 C segun zona/altitud.
# Si sale algo fuera de ese rango (ej. -200 o 3000), algo esta mal
# en la conversion o en el area/variable seleccionada.
stats = arcpy.management.GetRasterProperties(capa_t2m_c, "MINIMUM")
print("Valor minimo en la capa (deberia estar entre ~10 y ~35 C):", stats.getOutput(0))

stats_max = arcpy.management.GetRasterProperties(capa_t2m_c, "MAXIMUM")
print("Valor maximo en la capa:", stats_max.getOutput(0))

# Si estos valores tienen sentido, ya podemos pasar a simbologia
# (paleta de colores, seccion 5 de la propuesta) y despues a
# publicar como Image Service (seccion 6).
