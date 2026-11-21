import logging
import time
import uuid

from sqlalchemy.orm import Session

from app.core.catalogos import NOMBRES_VARIABLES
from app.core.config import settings
from app.core.exceptions import AppError
from app.models.prediccion import Prediccion
from app.models.prediccion_recomendacion import PrediccionRecomendacion
from app.models.usuario import Usuario
from app.repositories import catalogo_repo, prediccion_repo
from app.schemas.prediccion import (
    AreaOut,
    FactorOut,
    NivelesOut,
    NivelOut,
    PrediccionOut,
    PrediccionResumenOut,
    RecomendacionOut,
)
from app.services import modelo_sync_service, perfil_service

logger = logging.getLogger(__name__)

ADVERTENCIA = (
    "Este resultado es un apoyo a la decisión profesional, no una decisión automática. "
    "No reemplaza la valoración multidimensional del profesional (sustento, salud, "
    "protección, documentación) y debe usarse con criterio profesional."
)

CLASES_LEGIBLES = {
    "Desempleado": "Desempleo",
    "Empleado_Formal": "Empleo formal",
    "Empleado_Informal": "Empleo informal",
}


def ejecutar(db: Session, usuario: Usuario, perfil_id: uuid.UUID) -> uuid.UUID:
    """Ejecuta el modelo sobre un perfil completo, guarda el resultado y devuelve su id."""
    perfil = perfil_service.obtener(db, usuario, perfil_id)
    if perfil.estado_formulario != "completo":
        raise AppError(422, "El perfil está en borrador. Complétalo antes de ejecutar la predicción.")

    try:
        from app.inference import get_modelo, predecir

        modelo = get_modelo()
    except Exception:  # noqa: BLE001
        logger.exception("El modelo de inferencia no está disponible")
        raise AppError(503, "El modelo de predicción no está disponible en este momento. Inténtalo más tarde.")

    inicio = time.perf_counter()
    try:
        r = predecir(perfil.datos_formulario, modelo=modelo)
    except Exception:  # noqa: BLE001
        logger.exception("Falló la inferencia del perfil %s", perfil.id)
        raise AppError(500, "No se pudo ejecutar la predicción. Revisa los datos del perfil e inténtalo nuevamente.")
    ms = int((time.perf_counter() - inicio) * 1000)

    version = modelo_sync_service.sincronizar(db, modelo)
    reglas = catalogo_repo.por_codigos(db, [x["id"] for x in r["recomendaciones"]])

    probs = r["probabilidades"]
    prediccion = Prediccion(
        perfil_id=perfil.id,
        usuario_ejecutor_id=usuario.id,
        version_modelo_id=version.id,
        inputs_snapshot=dict(perfil.datos_formulario),
        clase_predicha=r["prediccion"],
        clase_etapa2=r["prediccion_etapa2"],
        prob_formal=probs["Empleado_Formal"],
        prob_informal=probs["Empleado_Informal"],
        prob_desempleado=probs["Desempleado"],
        nivel_riesgo_desempleo=r["niveles_riesgo"]["etapa1"]["nivel"],
        nivel_prob_formalidad=r["niveles_riesgo"]["etapa2"]["nivel"],
        valores_shap={"etapa": r["etapa_explicada"], "sentido": r["sentido_shap"], "factores": r["explicacion"]},
        tiempo_respuesta_ms=ms,
    )
    recomendaciones = [
        PrediccionRecomendacion(
            regla_id=reglas[x["id"]].id,
            orden_prioridad=i,
            variable_shap_asociada=modelo.catalogo[x["id"]].get("variable_prioridad") or None,
        )
        for i, x in enumerate(r["recomendaciones"], start=1)
    ]
    return prediccion_repo.guardar(db, prediccion, recomendaciones)


def _niveles(p: Prediccion) -> NivelesOut:
    return NivelesOut(
        desempleo=NivelOut(
            evento="Desempleo",
            nivel=p.nivel_riesgo_desempleo,
            lectura="Riesgo de desempleo: Alto significa mayor riesgo.",
        ),
        formalidad=NivelOut(
            evento="Empleo formal (si la persona estuviera empleada)",
            nivel=p.nivel_prob_formalidad,
            lectura="Probabilidad de empleo formal: Alto significa más probable que sea formal.",
        ),
    )


def a_respuesta(p: Prediccion) -> PrediccionOut:
    shap_info = p.valores_shap or {}
    factores = [
        FactorOut(
            variable=f["variable"],
            nombre=NOMBRES_VARIABLES.get(f["variable"], f["variable"]),
            valor=f["valor"],
            etiqueta=f["etiqueta"],
            shap=f["shap"],
            empuja_hacia=f["empuja_hacia"],
        )
        for f in shap_info.get("factores", [])
    ]
    recs = [
        RecomendacionOut(
            orden=r.orden_prioridad,
            id=r.regla.codigo_regla,
            area_id=r.regla.tipo,
            area=r.regla.area_tematica,
            texto=r.regla.descripcion_accionable,
        )
        for r in sorted(p.recomendaciones, key=lambda x: x.orden_prioridad)
    ]
    areas: dict[str, int] = {}
    for r in recs:
        areas[r.area] = areas.get(r.area, 0) + 1

    probabilidades = None
    if settings.MOSTRAR_PROBABILIDADES:
        probabilidades = {
            "Desempleado": float(p.prob_desempleado),
            "Empleado_Formal": float(p.prob_formal),
            "Empleado_Informal": float(p.prob_informal),
        }

    return PrediccionOut(
        id=p.id,
        perfil_id=p.perfil_id,
        codigo_identificador=p.perfil.codigo_identificador,
        fecha_prediccion=p.fecha_prediccion,
        version_modelo=p.version_modelo.codigo_version,
        clase=p.clase_predicha,
        clase_legible=CLASES_LEGIBLES.get(p.clase_predicha, p.clase_predicha),
        niveles_riesgo=_niveles(p),
        etapa_explicada=shap_info.get("etapa", ""),
        sentido_shap=shap_info.get("sentido", ""),
        factores=factores,
        recomendaciones=recs,
        areas_recomendadas=[AreaOut(area=a, cantidad=n) for a, n in areas.items()],
        advertencia=ADVERTENCIA,
        probabilidades=probabilidades,
    )


def obtener(db: Session, usuario: Usuario, prediccion_id: uuid.UUID) -> PrediccionOut:
    p = prediccion_repo.get(db, prediccion_id, usuario.institucion_id, usuario.id)
    if p is None:
        raise AppError(404, "Predicción no encontrada.")
    return a_respuesta(p)


def listar_por_perfil(db: Session, usuario: Usuario, perfil_id: uuid.UUID) -> list[PrediccionResumenOut]:
    perfil = perfil_service.obtener(db, usuario, perfil_id)  # valida pertenencia (404 si no)
    return [
        PrediccionResumenOut(
            id=p.id,
            fecha_prediccion=p.fecha_prediccion,
            version_modelo=p.version_modelo.codigo_version,
            clase=p.clase_predicha,
            clase_legible=CLASES_LEGIBLES.get(p.clase_predicha, p.clase_predicha),
            niveles_riesgo=_niveles(p),
        )
        for p in prediccion_repo.listar_por_perfil(db, perfil.id)
    ]