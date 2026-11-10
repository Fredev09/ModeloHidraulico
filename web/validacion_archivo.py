import io
import zipfile

import numpy as np
import pandas as pd

from features import MUESTRAS_POR_SENSOR, SENSOR_NAMES

MAX_BYTES = 20 * 1024 * 1024
MAX_CICLOS = 5000
ARCHIVOS_IGNORADOS = {"profile.txt", "se.txt"}


class ErrorValidacion(Exception):
    pass


def _leer_sensor(archivo_bytes, nombre):
    esperadas = MUESTRAS_POR_SENSOR[nombre]
    try:
        df = pd.read_csv(io.BytesIO(archivo_bytes), sep="\t", header=None, dtype=np.float32)
    except pd.errors.EmptyDataError:
        raise ErrorValidacion(f"{nombre}.txt está vacío")
    except Exception:
        raise ErrorValidacion(f"{nombre}.txt no es un archivo tabulado numérico válido")
    if df.shape[0] == 0 or df.shape[1] == 0 or df.size == 0:
        raise ErrorValidacion(f"{nombre}.txt está vacío")
    if df.shape[1] != esperadas:
        raise ErrorValidacion(
            f"{nombre}.txt tiene {df.shape[1]} columnas de muestras; se esperaban {esperadas}"
        )
    matriz = df.to_numpy()
    if not np.isfinite(matriz).all():
        raise ErrorValidacion(f"{nombre}.txt contiene valores no numéricos, NaN o infinitos")
    return matriz


def validar_y_leer_zip(contenido_zip):
    if len(contenido_zip) > MAX_BYTES:
        raise ErrorValidacion(f"El ZIP supera el límite de {MAX_BYTES // (1024 * 1024)} MB")
    if len(contenido_zip) == 0:
        raise ErrorValidacion("El archivo subido está vacío")
    try:
        zf = zipfile.ZipFile(io.BytesIO(contenido_zip))
    except zipfile.BadZipFile:
        raise ErrorValidacion("El archivo subido no es un ZIP válido")
    with zf:
        nombres_archivos = {}
        for info in zf.infolist():
            if info.is_dir():
                continue
            nombres_archivos[info.filename.lower().split("/")[-1]] = info.filename
        faltantes = [s for s in SENSOR_NAMES if f"{s.lower()}.txt" not in nombres_archivos]
        if faltantes:
            raise ErrorValidacion(
                "Faltan sensores obligatorios: " + ", ".join(f"{s}.txt" for s in faltantes)
            )
        matrices = {}
        for sensor in SENSOR_NAMES:
            contenido = zf.read(nombres_archivos[f"{sensor.lower()}.txt"])
            matrices[sensor] = _leer_sensor(contenido, sensor)
    n_ciclos = matrices[SENSOR_NAMES[0]].shape[0]
    if any(matrices[s].shape[0] != n_ciclos for s in SENSOR_NAMES):
        raise ErrorValidacion("Los archivos de sensores tienen números de ciclos distintos")
    if n_ciclos > MAX_CICLOS:
        raise ErrorValidacion(f"Demasiados ciclos ({n_ciclos}); el máximo es {MAX_CICLOS}")
    return matrices
