from typing import Optional
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

import llm_recomendador
import prediccion
from features import extraer_features
from rl_agent import agente_rl
from validacion_archivo import MAX_BYTES, ErrorValidacion, validar_y_leer_zip

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


class FeedbackRequest(BaseModel):
    estado: str
    accion: str
    calificacion: float
    ciclo: int = 1
    dictamen: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    prediccion.inicializar_si_posible()
    llm_recomendador.inicializar_pipeline_en_segundo_plano()
    yield


app = FastAPI(title="Monitor hidráulico — prototipo académico", lifespan=lifespan)


class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static") or request.url.path == "/":
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response


app.add_middleware(NoCacheMiddleware)


@app.get("/api/estado")
def api_estado():
    estado = prediccion.estado()
    return {
        "modelo_disponible": estado["cargado"],
        "detalle": estado.get("error"),
        "llm_disponible": True,
        "rl_disponible": True
    }


@app.get("/api/rl/estado")
def api_rl_estado():
    return agente_rl.obtener_estado_agente()


@app.post("/api/feedback")
def api_feedback(datos: FeedbackRequest):
    resultado = agente_rl.actualizar_con_feedback(
        datos.estado, datos.accion, datos.calificacion, datos.dictamen
    )
    if "error" in resultado:
        raise HTTPException(status_code=400, detail=resultado["error"])
    return {
        "status": "ok",
        "registro": resultado,
        "estado_agente": agente_rl.obtener_estado_agente()
    }


@app.post("/api/predecir")
def api_predecir(archivo: UploadFile = File(...)):
    contenido = archivo.file.read(MAX_BYTES + 1)
    if len(contenido) > MAX_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"El archivo supera el límite de {MAX_BYTES // (1024 * 1024)} MB",
        )
    try:
        matrices = validar_y_leer_zip(contenido)
        X = extraer_features(matrices)
    except ErrorValidacion as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    try:
        predicciones = prediccion.predecir(X)
        for p in predicciones:
            c_clase = p["cooler"]["clase"]
            v_clase = p["valvula"]["clase"]
            b_clase = p["bomba"]["clase"]

            estado_rl = agente_rl.determinar_estado(c_clase, v_clase, b_clase)
            accion_clave, info_accion = agente_rl.seleccionar_accion(estado_rl)

            recomendacion = llm_recomendador.generar_recomendacion(p, info_accion)
            p["estado_rl"] = estado_rl
            p["accion_rl"] = accion_clave
            p["info_accion_rl"] = info_accion
            p["recomendacion_llm"] = recomendacion

    except prediccion.ModeloNoDisponible as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(exc)}")
    return {
        "archivo": archivo.filename or "archivo",
        "n_ciclos": int(X.shape[0]),
        "n_features": int(X.shape[1]),
        "predicciones": predicciones,
    }


@app.get("/")
def indice():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
