"""Módulo de inferencia: independiente de FastAPI y de la base de datos.

Uso:
    from app.inference import predecir
    resultado = predecir(perfil.datos_formulario)
"""
from app.inference.cascade import clasificar
from app.inference.explainer import explicar
from app.inference.model_loader import ModeloProduccion, get_modelo
from app.inference.preprocessing import preparar_fila
from app.inference.recommender import generar_recomendaciones


def predecir(perfil: dict, top_k: int = 5, modelo: ModeloProduccion | None = None) -> dict:
    modelo = modelo or get_modelo()
    fila = preparar_fila(perfil, modelo)

    res = clasificar(modelo, fila)
    sv, cols, top, sentido = explicar(modelo, fila, res["etapa_explicada"], top_k)

    # El motor de reglas recibe los valores EXACTOS del modelo (fila), no el dict crudo.
    perfil_modelo = fila.iloc[0].to_dict()
    recs, areas = generar_recomendaciones(modelo, perfil_modelo, res["prediccion"], sv, cols)

    return {
        **res,
        "sentido_shap": sentido,
        "explicacion": top,
        "recomendaciones": recs,
        "areas_recomendadas": areas,
        "version_modelo": modelo.version,
    }