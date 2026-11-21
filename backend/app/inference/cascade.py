"""Cascada de dos etapas. Réplica de predecir_perfil del notebook XAI."""
import numpy as np
import pandas as pd

from app.inference.model_loader import ModeloProduccion


def _asignar_nivel(p_cal: float, cortes: list[float], niveles: list[str]) -> str:
    if p_cal < cortes[0]:
        return niveles[0]
    if p_cal < cortes[1]:
        return niveles[1]
    return niveles[2]


def clasificar(modelo: ModeloProduccion, fila: pd.DataFrame, peso_formal: float | None = None) -> dict:
    peso = modelo.peso_formal if peso_formal is None else float(peso_formal)
    cal_cfg = modelo.config["calibracion"]
    niveles = cal_cfg["niveles"]

    # Etapa 1 (positivo = Desempleado). La clase usa predict() de CatBoost.
    c1 = list(modelo.e1.classes_)
    p_des = float(modelo.e1.predict_proba(fila)[0, c1.index("Desempleado")])
    pred_e1 = str(modelo.e1.predict(fila).ravel()[0])

    # Etapa 2: se calcula SIEMPRE ("si la persona estuviera empleada").
    c2 = list(modelo.e2.classes_)
    p2 = modelo.e2.predict_proba(fila)[0]
    pesos = np.ones(len(c2))
    pesos[c2.index("Empleado_Formal")] = peso
    ajustada = p2 * pesos
    pred_e2 = c2[int(np.argmax(ajustada))]
    p_formal_raw = float(p2[c2.index("Empleado_Formal")])
    p_formal_adj = float(ajustada[c2.index("Empleado_Formal")] / ajustada.sum())

    if pred_e1 == "Desempleado":
        pred_final, etapa = "Desempleado", "E1"
    else:
        pred_final, etapa = pred_e2, "E2"

    # Probabilidades crudas de las 3 clases (uso interno / trazabilidad).
    probs = {
        "Desempleado": p_des,
        "Empleado_Formal": (1 - p_des) * p_formal_raw,
        "Empleado_Informal": (1 - p_des) * (1 - p_formal_raw),
    }

    # Nivel de riesgo: probabilidad CALIBRADA -> Bajo/Medio/Alto. No cambia la clase.
    niveles_riesgo = {
        "etapa1": {
            "evento": "Desempleado",
            "nivel": _asignar_nivel(float(modelo.cal1.predict(p_des)), cal_cfg["etapa1"]["cortes_riesgo"], niveles),
        },
        "etapa2": {
            "evento": "Empleado_Formal",
            "condicionado_a": "Empleado",
            "nivel": _asignar_nivel(float(modelo.cal2.predict(p_formal_raw)), cal_cfg["etapa2"]["cortes_riesgo"], niveles),
        },
    }

    return {
        "prediccion": pred_final,
        "etapa_explicada": etapa,
        "prediccion_etapa1": pred_e1,
        "prediccion_etapa2": pred_e2,
        "probabilidades": {k: round(v, 4) for k, v in probs.items()},
        "prob_formal_ajustada_e2": round(p_formal_adj, 4),
        "peso_formal": peso,
        "niveles_riesgo": niveles_riesgo,
    }