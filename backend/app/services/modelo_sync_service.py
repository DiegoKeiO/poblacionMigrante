"""Sincroniza la BD con los artefactos del modelo cargado.

- versiones_modelo: registra la versión del modelo en uso (trazabilidad).
- catalogo_reglas: inserta las reglas de catalogo_reglas.json que aún no estén.
Es idempotente: si ya existen, no hace nada.
"""
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.inference.model_loader import ModeloProduccion
from app.models.catalogo_regla import CatalogoRegla
from app.models.version_modelo import VersionModelo
from app.repositories import catalogo_repo, version_modelo_repo


def _sincronizar(db: Session, modelo: ModeloProduccion) -> VersionModelo:
    version = version_modelo_repo.get_by_codigo(db, modelo.version)
    if version is None:
        db.execute(update(VersionModelo).values(activo=False))
        version = VersionModelo(
            codigo_version=modelo.version,
            archivo_etapa1_cbm=modelo.config["etapa1"]["archivo"],
            archivo_etapa2_cbm=modelo.config["etapa2"]["archivo"],
            config_json=modelo.config,
            metricas_evaluacion=modelo.config.get("metricas_test", {}),
            activo=True,
        )
        db.add(version)

    existentes = catalogo_repo.por_codigos(db, list(modelo.catalogo))
    for codigo, r in modelo.catalogo.items():
        if codigo in existentes:
            continue
        db.add(
            CatalogoRegla(
                codigo_regla=codigo,
                tipo=r["area_id"],
                area_tematica=r["area"],
                clase_objetivo=str(r.get("aplica_a", "Todas"))[:30],
                condicion_disparo={
                    "activa_cuando": r.get("activa_cuando"),
                    "variable_prioridad": r.get("variable_prioridad") or None,
                },
                titulo=f"{codigo}: {r['area']}"[:150],
                descripcion_accionable=r["texto"],
            )
        )
    db.commit()
    return version


def sincronizar(db: Session, modelo: ModeloProduccion) -> VersionModelo:
    try:
        return _sincronizar(db, modelo)
    except IntegrityError:
        # Dos primeras predicciones simultáneas: la otra ya insertó. Se reintenta leyendo.
        db.rollback()
        return _sincronizar(db, modelo)