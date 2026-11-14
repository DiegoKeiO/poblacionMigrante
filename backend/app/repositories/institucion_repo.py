import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.institucion import Institucion


def get_by_id(db: Session, institucion_id: uuid.UUID) -> Institucion | None:
    return db.get(Institucion, institucion_id)


def list_activas(db: Session) -> list[Institucion]:
    return list(db.scalars(select(Institucion).where(Institucion.activo.is_(True)).order_by(Institucion.nombre)))