from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.catalogo_regla import CatalogoRegla


def por_codigos(db: Session, codigos: list[str]) -> dict[str, CatalogoRegla]:
    if not codigos:
        return {}
    filas = db.scalars(select(CatalogoRegla).where(CatalogoRegla.codigo_regla.in_(codigos)))
    return {r.codigo_regla: r for r in filas}