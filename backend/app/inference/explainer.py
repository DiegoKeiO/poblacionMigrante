"""Explicación local con SHAP (TreeExplainer) de la etapa que decide la clase."""
import numpy as np
import pandas as pd

from app.inference.model_loader import ModeloProduccion
from app.inference.utils import etiqueta


def explicar(modelo: ModeloProduccion, fila: pd.DataFrame, etapa: str, top_k: int = 5):
    """Devuelve (valores_shap, columnas, top_factores, sentido).

    E1: SHAP > 0 empuja hacia Empleado. E2: SHAP > 0 empuja hacia Empleado_Informal.
    El sentido lo da modelo.classes_[1], igual que en el notebook.
    """
    cbm, explainer = (modelo.e1, modelo.expl1) if etapa == "E1" else (modelo.e2, modelo.expl2)
    cols = list(cbm.feature_names_)
    sv = explainer.shap_values(fila[cols])[0]
    c_neg, c_pos = list(cbm.classes_)

    top = []
    for j in np.argsort(-np.abs(sv))[:top_k]:
        col = cols[j]
        valor = fila[col].iloc[0]
        es_cat = col in modelo.cat_cols
        top.append({
            "variable": col,
            "valor": valor if es_cat else float(valor),
            "etiqueta": etiqueta(modelo.etiquetas["etiquetas"], col, valor) if es_cat else float(valor),
            "shap": round(float(sv[j]), 4),
            "empuja_hacia": c_pos if sv[j] > 0 else c_neg,
        })
    return sv, cols, top, f"SHAP > 0 empuja hacia {c_pos}"