import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.perfil_migrante import PerfilMigrante
from app.models.prediccion import Prediccion
from app.models.prediccion_recomendacion import PrediccionRecomendacion


def _con_relaciones():
    return (
        selectinload(Prediccion.recomendaciones).selectinload(PrediccionRecomendacion.regla),
        selectinload(Prediccion.version_modelo),
        selectinload(Prediccion.perfil),
    )


def guardar(db: Session, prediccion: Prediccion, recomendaciones: list[PrediccionRecomendacion]) -> uuid.UUID:
    """Guarda la predicción y sus recomendaciones en una sola transacción."""
    db.add(prediccion)
    db.flush()  # genera prediccion.id
    for rec in recomendaciones:
        rec.prediccion_id = prediccion.id
    db.add_all(recomendaciones)
    db.commit()
    return prediccion.id


def get(db: Session, prediccion_id: uuid.UUID, institucion_id: uuid.UUID, usuario_id: uuid.UUID) -> Prediccion | None:
    """Solo si el perfil pertenece a la institución y al usuario."""
    return db.scalar(
        select(Prediccion)
        .join(PerfilMigrante, Prediccion.perfil_id == PerfilMigrante.id)
        .where(
            Prediccion.id == prediccion_id,
            PerfilMigrante.institucion_id == institucion_id,
            PerfilMigrante.usuario_registro_id == usuario_id,
        )
        .options(*_con_relaciones())
    )


def listar_por_perfil(db: Session, perfil_id: uuid.UUID) -> list[Prediccion]:
    return list(
        db.scalars(
            select(Prediccion)
            .where(Prediccion.perfil_id == perfil_id)
            .order_by(Prediccion.fecha_prediccion.desc())
            .options(*_con_relaciones())
        )
    )