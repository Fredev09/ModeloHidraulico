import json
import os

import joblib
import numpy as np

MODELOS_DIR = os.environ.get(
    "MODELOS_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "modelo")
)

NOMBRES_CLASES = {
    "cooler": {
        0: "3 % — fallo total",
        1: "20 % — rendimiento reducido",
        2: "100 % — rendimiento completo",
    },
    "valvula": {
        0: "73 % — fallo total",
        1: "80 % — retardo severo",
        2: "90 % — retardo leve",
        3: "100 % — conmutación óptima",
    },
    "bomba": {0: "Sin fugas", 1: "Fuga débil", 2: "Fuga severa"},
}


class ModeloNoDisponible(Exception):
    pass


_estado = {
    "cargado": False,
    "wrapper": False,
    "error": None,
    "modelo": None,
    "scaler_X": None,
    "scaler_y": None,
}


def estado():
    if not _estado["cargado"]:
        inicializar_si_posible()
    return {
        "cargado": _estado["cargado"],
        "wrapper": _estado["wrapper"],
        "error": _estado["error"],
        "n_features": 288,
    }


def inicializar():
    ruta_modelo = os.path.join(MODELOS_DIR, "modelo_multitarea.keras")
    ruta_metadata = os.path.join(MODELOS_DIR, "metadata.json")
    if not os.path.isfile(ruta_modelo):
        raise ModeloNoDisponible(
            "modelo_multitarea.keras no está disponible. Ejecute la última celda del notebook en Colab y coloque los artefactos descargados en web/modelo/."
        )
    if not os.path.isfile(ruta_metadata):
        raise ModeloNoDisponible(
            "metadata.json no está disponible. Regenere los artefactos desde el notebook en Colab."
        )
    import tensorflow as tf

    with open(ruta_metadata, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    artefacto = metadata.get("artefacto_desplegable", "")
    modelo = tf.keras.models.load_model(ruta_modelo, compile=False)
    scaler_X = None
    scaler_y = None
    es_wrapper = artefacto == "wrapper_sin_escalar"
    if not es_wrapper:
        ruta_scaler_x = os.path.join(MODELOS_DIR, "scaler_X.joblib")
        ruta_scaler_y = os.path.join(MODELOS_DIR, "scaler_y.joblib")
        if not os.path.isfile(ruta_scaler_x) or not os.path.isfile(ruta_scaler_y):
            raise ModeloNoDisponible(
                "El artefacto requiere scaler_X.joblib y scaler_y.joblib, que no están en web/modelo/."
            )
        scaler_X = joblib.load(ruta_scaler_x)
        scaler_y = joblib.load(ruta_scaler_y)
    _estado.update(
        {
            "cargado": True,
            "wrapper": es_wrapper,
            "error": None,
            "modelo": modelo,
            "scaler_X": scaler_X,
            "scaler_y": scaler_y,
        }
    )
    return estado()


def inicializar_si_posible():
    try:
        inicializar()
    except Exception as exc:
        _estado.update(
            {"cargado": False, "wrapper": False, "error": str(exc), "modelo": None}
        )
        return estado()


def reiniciar_estado():
    _estado.update(
        {
            "cargado": False,
            "wrapper": False,
            "error": None,
            "modelo": None,
            "scaler_X": None,
            "scaler_y": None,
        }
    )


def predecir(X_crudo):
    if not _estado["cargado"]:
        inicializar_si_posible()
    if not _estado["cargado"]:
        raise ModeloNoDisponible(
            _estado["error"] or "El modelo no está disponible en el servidor."
        )
    modelo = _estado["modelo"]
    if _estado["wrapper"]:
        entradas = np.asarray(X_crudo, dtype=np.float32)
    else:
        entradas = _estado["scaler_X"].transform(X_crudo).astype(np.float32)

    probs_c, probs_v, probs_b, ef_salida, probs_falla = modelo.predict(entradas, verbose=0)

    if _estado["wrapper"]:
        eficiencia = ef_salida
    else:
        eficiencia = _estado["scaler_y"].inverse_transform(ef_salida)

    resultados = []
    for i in range(entradas.shape[0]):
        pc = [float(x) for x in probs_c[i]]
        pv = [float(x) for x in probs_v[i]]
        pb = [float(x) for x in probs_b[i]]
        ef_val = float(eficiencia[i][0])

        c_clase = int(np.argmax(pc))
        v_clase = int(np.argmax(pv))
        b_clase = int(np.argmax(pb))

        prob_f = float(probs_falla[i][0])
        va_a_fallar = bool(prob_f >= 0.5)

        resultados.append(
            {
                "ciclo": i + 1,
                "falla": {
                    "va_a_fallar": va_a_fallar,
                    "probabilidad": prob_f,
                    "probabilidad_pct": round(prob_f * 100, 1),
                    "estado": "LA MÁQUINA VA A FALLAR" if va_a_fallar else "OPERACIÓN NORMAL (NO VA A FALLAR)",
                    "alerta": "peligro" if va_a_fallar else "ok",
                    "diagnostico": f"Predicción directa de la red neuronal (capa 'falla'): {round(prob_f * 100, 2)}% de probabilidad.",
                },
                "cooler": {
                    "clase": c_clase,
                    "etiqueta": NOMBRES_CLASES["cooler"][c_clase],
                    "probabilidades": pc,
                },
                "valvula": {
                    "clase": v_clase,
                    "etiqueta": NOMBRES_CLASES["valvula"][v_clase],
                    "probabilidades": pv,
                },
                "bomba": {
                    "clase": b_clase,
                    "etiqueta": NOMBRES_CLASES["bomba"][b_clase],
                    "probabilidades": pb,
                },
                "eficiencia_pct": ef_val,
            }
        )
    return resultados
