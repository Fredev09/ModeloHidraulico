import json
import os
import random
from typing import Dict, Any, Tuple, Optional

RL_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modelo", "rl_q_table.json")

ESTADOS = [
    "COOLER_CRITICO",
    "VALVULA_CRITICA",
    "BOMBA_CRITICA",
    "FALLA_MULTIPLE",
    "DESGASTE_MODERADO",
    "OPERACION_NOMINAL",
]

ACCIONES = {
    "PARADA_CORRECTIVA": {
        "nombre": "Parada Correctiva Inmediata",
        "descripcion": "Detener el equipo bajo protocolo LOTO, despresurizar el circuito y reemplazar el componente colapsado.",
        "enfoque": "correctivo_urgente"
    },
    "PLAN_PROGRAMADO": {
        "nombre": "Mantenimiento Preventivo Programado",
        "descripcion": "Agendar el cambio de componente en la próxima parada de turno para no detener la producción de inmediato.",
        "enfoque": "preventivo_planificado"
    },
    "INSPECCION_PURGA": {
        "nombre": "Inspección y Diagnóstico Termodinámico",
        "descripcion": "Realizar termografía en el intercambiador, verificar viscosidad del aceite y purgar aire del circuito.",
        "enfoque": "diagnostico_profundo"
    },
    "ALIVIO_CARGA": {
        "nombre": "Mitigación y Alivio Operativo",
        "descripcion": "Reducir la presión del acumulador y aumentar el tiempo de ciclo al 75% de carga para proteger el sistema.",
        "enfoque": "mitigacion_operativa"
    }
}

VALORES_INICIALES_Q = {
    "COOLER_CRITICO": {
        "PARADA_CORRECTIVA": 0.85,
        "PLAN_PROGRAMADO": 0.20,
        "INSPECCION_PURGA": 0.60,
        "ALIVIO_CARGA": 0.40
    },
    "VALVULA_CRITICA": {
        "PARADA_CORRECTIVA": 0.75,
        "PLAN_PROGRAMADO": 0.30,
        "INSPECCION_PURGA": 0.50,
        "ALIVIO_CARGA": 0.35
    },
    "BOMBA_CRITICA": {
        "PARADA_CORRECTIVA": 0.80,
        "PLAN_PROGRAMADO": 0.25,
        "INSPECCION_PURGA": 0.45,
        "ALIVIO_CARGA": 0.30
    },
    "FALLA_MULTIPLE": {
        "PARADA_CORRECTIVA": 0.95,
        "PLAN_PROGRAMADO": 0.10,
        "INSPECCION_PURGA": 0.40,
        "ALIVIO_CARGA": 0.20
    },
    "DESGASTE_MODERADO": {
        "PARADA_CORRECTIVA": 0.15,
        "PLAN_PROGRAMADO": 0.85,
        "INSPECCION_PURGA": 0.70,
        "ALIVIO_CARGA": 0.50
    },
    "OPERACION_NOMINAL": {
        "PARADA_CORRECTIVA": 0.05,
        "PLAN_PROGRAMADO": 0.40,
        "INSPECCION_PURGA": 0.60,
        "ALIVIO_CARGA": 0.20
    }
}


class AgenteRefuerzoMantenimiento:
    def __init__(self, alpha=0.25, epsilon=0.10):
        self.alpha = alpha
        self.epsilon = epsilon
        self.q_table = self._cargar_tabla()
        self.historial_feedback = []

    def _cargar_tabla(self) -> Dict[str, Dict[str, float]]:
        if os.path.isfile(RL_MODEL_PATH):
            try:
                with open(RL_MODEL_PATH, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                    return datos.get("q_table", VALORES_INICIALES_Q)
            except Exception:
                pass
        return {s: dict(a) for s, a in VALORES_INICIALES_Q.items()}

    def guardar_tabla(self):
        os.makedirs(os.path.dirname(RL_MODEL_PATH), exist_ok=True)
        try:
            with open(RL_MODEL_PATH, "w", encoding="utf-8") as f:
                json.dump({
                    "algoritmo": "Q-Learning / Contextual Bandit RLHF",
                    "alpha": self.alpha,
                    "epsilon": self.epsilon,
                    "q_table": self.q_table,
                    "total_interacciones": len(self.historial_feedback)
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error al guardar tabla Q: {e}")

    def determinar_estado(self, c_clase: int, v_clase: int, b_clase: int) -> str:
        criticos = 0
        if c_clase == 0: criticos += 1
        if v_clase in (0, 1): criticos += 1
        if b_clase == 2: criticos += 1

        if criticos >= 2:
            return "FALLA_MULTIPLE"
        elif c_clase == 0:
            return "COOLER_CRITICO"
        elif v_clase in (0, 1):
            return "VALVULA_CRITICA"
        elif b_clase == 2:
            return "BOMBA_CRITICA"
        elif c_clase == 1 or v_clase == 2 or b_clase == 1:
            return "DESGASTE_MODERADO"
        else:
            return "OPERACION_NOMINAL"

    def seleccionar_accion(self, estado: str, permitir_exploracion: bool = True) -> Tuple[str, Dict[str, Any]]:
        if estado not in self.q_table:
            estado = "OPERACION_NOMINAL"

        acciones_disponibles = list(ACCIONES.keys())

        if permitir_exploracion and random.random() < self.epsilon:
            accion_elegida = random.choice(acciones_disponibles)
            modo = "exploracion"
        else:
            accion_elegida = max(acciones_disponibles, key=lambda a: self.q_table[estado][a])
            modo = "explotacion"

        q_val = self.q_table[estado][accion_elegida]
        info_accion = ACCIONES[accion_elegida]

        return accion_elegida, {
            "clave": accion_elegida,
            "nombre": info_accion["nombre"],
            "descripcion": info_accion["descripcion"],
            "q_value": round(q_val, 4),
            "modo_seleccion": modo,
            "valores_q_estado": {k: round(v, 4) for k, v in self.q_table[estado].items()}
        }

    def actualizar_con_feedback(self, estado: str, accion: str, calificacion: float, dictamen: Optional[str] = None) -> Dict[str, Any]:
        if estado not in self.q_table or accion not in self.q_table[estado]:
            return {"error": "Estado o acción no válida"}

        recompensa = float(calificacion)
        q_anterior = self.q_table[estado][accion]

        td_error = recompensa - q_anterior
        q_nuevo = q_anterior + self.alpha * td_error
        self.q_table[estado][accion] = round(q_nuevo, 4)

        registro = {
            "estado": estado,
            "accion": accion,
            "dictamen": dictamen or ("Aprobada (+1)" if recompensa > 0 else "Rechazada (-1)"),
            "recompensa": round(recompensa, 2),
            "q_anterior": round(q_anterior, 4),
            "q_nuevo": round(q_nuevo, 4),
            "td_error": round(td_error, 4),
            "alpha": self.alpha
        }
        self.historial_feedback.append(registro)
        self.guardar_tabla()

        return registro

    def obtener_estado_agente(self) -> Dict[str, Any]:
        return {
            "algoritmo": "Q-Learning / Contextual Bandit con Human Feedback",
            "alpha": self.alpha,
            "epsilon": self.epsilon,
            "total_feedbacks": len(self.historial_feedback),
            "q_table": self.q_table,
            "acciones": ACCIONES,
            "estados": ESTADOS
        }


agente_rl = AgenteRefuerzoMantenimiento()
