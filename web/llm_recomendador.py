import json
import os
import threading
import time
import urllib.request
from typing import Dict, Any

_pipeline_llm = None
_cargando_modelo = False
_modelo_hf = os.environ.get("LLM_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
_ollama_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
_ollama_modelo = os.environ.get("OLLAMA_MODEL", "qwen3.5:4b")
_pipeline_error = None


def _ollama_disponible() -> bool:
    base = _ollama_url.rsplit("/api/", 1)[0]
    try:
        with urllib.request.urlopen(f"{base}/api/tags", timeout=1.5) as resp:
            return resp.status == 200
    except Exception:
        return False


def _precalentar_ollama():
    try:
        payload = {
            "model": _ollama_modelo,
            "stream": False,
            "keep_alive": "15m",
            "messages": []
        }
        req = urllib.request.Request(
            _ollama_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=20):
            print(f"[LLM] Ollama precalentado con modelo {_ollama_modelo}.")
    except Exception as e:
        print(f"[LLM] Aviso al precalentar Ollama: {e}")


def _cargar_pipeline_sincrono():
    global _pipeline_llm, _cargando_modelo, _pipeline_error
    if _pipeline_llm is not None:
        return
    _cargando_modelo = True
    try:
        print(f"[LLM] Inicializando Hugging Face pipeline con modelo {_modelo_hf}...")
        from transformers import pipeline
        import torch

        dispositivo = 0 if torch.cuda.is_available() else -1
        _pipeline_llm = pipeline(
            "text-generation",
            model=_modelo_hf,
            device=dispositivo
        )
        print(f"[LLM] Pipeline de Hugging Face cargado exitosamente en dispositivo: {dispositivo}.")
    except Exception as e:
        _pipeline_error = str(e)
        print(f"[LLM] Error al cargar pipeline local: {e}")
    finally:
        _cargando_modelo = False


def inicializar_pipeline_en_segundo_plano():
    def _init():
        if _ollama_disponible():
            _precalentar_ollama()
        else:
            _cargar_pipeline_sincrono()

    hilo = threading.Thread(target=_init, daemon=True)
    hilo.start()


def construir_prompt(pred_ciclo: Dict[str, Any], estrategia_rl: Dict[str, Any]) -> str:
    c_info = pred_ciclo.get("cooler", {})
    v_info = pred_ciclo.get("valvula", {})
    b_info = pred_ciclo.get("bomba", {})
    falla_info = pred_ciclo.get("falla", {})

    c_clase = c_info.get("clase", 2)
    v_clase = v_info.get("clase", 3)
    b_clase = b_info.get("clase", 0)

    c_estado = f"{c_info.get('etiqueta', 'Desconocido')} ({'FALLA CRÍTICA' if c_clase == 0 else 'DEGRADADO' if c_clase == 1 else 'ÓPTIMO'})"
    v_estado = f"{v_info.get('etiqueta', 'Desconocido')} ({'FALLA SEVERA' if v_clase in (0, 1) else 'RETARDO LEVE' if v_clase == 2 else 'ÓPTIMA'})"
    b_estado = f"{b_info.get('etiqueta', 'Desconocido')} ({'FUGA SEVERA' if b_clase == 2 else 'FUGA LEVE' if b_clase == 1 else 'SIN FUGAS'})"

    ef = pred_ciclo.get("eficiencia_pct", 60.0)
    estado_falla = falla_info.get("estado", "Normal")
    prob_falla = falla_info.get("probabilidad_pct", 0.0)

    nombre_estrategia = estrategia_rl.get("nombre", "Mantenimiento General")
    desc_estrategia = estrategia_rl.get("descripcion", "")

    prompt = (
        f"Datos del diagnóstico por Red Neuronal:\n"
        f"- Enfriador (Cooler): {c_estado}\n"
        f"- Válvula hidráulica: {v_estado}\n"
        f"- Bomba hidráulica: {b_estado}\n"
        f"- Eficiencia global del sistema: {ef:.2f}%\n"
        f"- Riesgo de falla: {prob_falla:.1f}% ({estado_falla})\n"
        f"- Estrategia asignada por Agente RL: {nombre_estrategia} ({desc_estrategia})\n\n"
        f"Instrucción: Redacta una recomendación técnica de mantenimiento en español (entre 90 y 180 palabras, mínimo 250 caracteres) "
        f"dividida exactamente en estos 3 puntos numerados:\n"
        f"1. Diagnóstico técnico del ciclo:\n"
        f"2. Acciones de mantenimiento recomendadas:\n"
        f"3. Protocolo de seguridad LOTO:"
    )
    return prompt


def _recortar_a_ultima_oracion(texto: str) -> str:
    texto = texto.strip()
    if not texto:
        return texto
    if texto.endswith((".", "!", "?")):
        return texto
    ultimo_punto = texto.rfind(".")
    ultimo_salto = texto.rfind("\n")
    if ultimo_punto > len(texto) * 0.6:
        return texto[:ultimo_punto + 1].strip()
    if ultimo_salto > len(texto) * 0.6:
        return texto[:ultimo_salto].strip()
    return texto


def _generar_con_ollama(mensajes) -> str:
    payload = {
        "model": _ollama_modelo,
        "stream": False,
        "think": False,
        "keep_alive": "15m",
        "options": {
            "temperature": 0.3,
            "num_predict": 320
        },
        "messages": mensajes
    }
    req = urllib.request.Request(
        _ollama_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=35) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("message", {}).get("content", "").strip()


def generar_recomendacion(pred_ciclo: Dict[str, Any], estrategia_rl: Dict[str, Any]) -> Dict[str, Any]:
    global _pipeline_llm, _cargando_modelo

    prompt = construir_prompt(pred_ciclo, estrategia_rl)
    mensajes = [
        {
            "role": "system",
            "content": (
                "Eres un Ingeniero Jefe de Confiabilidad Hidráulica Industrial. "
                "Responde únicamente en español técnico claro, preciso y sin inventar datos ajenos al reporte. "
                "Estructura la respuesta exactamente en los 3 puntos numerados solicitados y termina todas las oraciones con punto final."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    texto_generado = ""
    modelo_usado = f"{_ollama_modelo} · Ollama"

    try:
        texto_generado = _generar_con_ollama(mensajes)
        texto_generado = _recortar_a_ultima_oracion(texto_generado)
    except Exception as e:
        print(f"[LLM] Ollama no disponible ({e}), usando pipeline Hugging Face de respaldo.")
        texto_generado = ""

    if not texto_generado:
        modelo_usado = _modelo_hf
        espera = 0
        while _cargando_modelo and espera < 30:
            time.sleep(0.25)
            espera += 0.25

        if _pipeline_llm is None and _pipeline_error is None:
            _cargar_pipeline_sincrono()

        if _pipeline_llm is not None:
            try:
                salida = _pipeline_llm(
                    mensajes,
                    max_new_tokens=230,
                    do_sample=True,
                    temperature=0.25,
                    top_p=0.9,
                    repetition_penalty=1.15
                )
                if isinstance(salida, list) and len(salida) > 0:
                    gen = salida[0].get("generated_text", "")
                    if isinstance(gen, list):
                        texto_generado = gen[-1].get("content", "").strip()
                    elif isinstance(gen, str):
                        texto_generado = gen.strip()
                texto_generado = _recortar_a_ultima_oracion(texto_generado)
            except Exception as e:
                print(f"[LLM] Error en inferencia del pipeline: {e}")
                texto_generado = ""

    if not texto_generado:
        texto_generado = (
            f"No fue posible generar la respuesta del modelo LLM ({_pipeline_error or 'error de inferencia'}). "
            f"Estrategia RL sugerida: {estrategia_rl.get('nombre', 'Mantenimiento')}."
        )

    longitud = len(texto_generado)
    cumple = longitud >= 200

    return {
        "texto": texto_generado,
        "n_caracteres": longitud,
        "cumple_requisito_200_chars": cumple,
        "modelo": modelo_usado,
        "estrategia_rl": estrategia_rl.get("nombre", ""),
        "q_value": estrategia_rl.get("q_value", 0.0),
        "accion_clave": estrategia_rl.get("clave", ""),
        "modo_seleccion": estrategia_rl.get("modo_seleccion", "explotacion")
    }
