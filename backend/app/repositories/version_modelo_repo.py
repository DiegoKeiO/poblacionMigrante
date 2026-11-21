from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.version_modelo import VersionModelo


def get_by_codigo(db: Session, codigo_version: str) -> VersionModelo | None:
    return db.scalar(select(VersionModelo).where(VersionModelo.codigo_version == codigo_version))