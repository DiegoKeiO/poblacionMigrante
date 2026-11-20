import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.perfil_migrante import PerfilMigrante


def get(db: Session, perfil_id: uuid.UUID, institucion_id: uuid.UUID, usuario_id: uuid.UUID) -> PerfilMigrante | None:
    """Solo devuelve el perfil si pertenece a la institución y al usuario."""
    return db.scalar(
        select(PerfilMigrante).where(
            PerfilMigrante.id == perfil_id,
            PerfilMigrante.institucion_id == institucion_id,
            PerfilMigrante.usuario_registro_id == usuario_id,
        )
    )


def listar(
    db: Session,
    institucion_id: uuid.UUID,
    usuario_id: uuid.UUID,
    estado: str | None,
    q: str | None,
    page: int,
    page_size: int,
) -> tuple[list[PerfilMigrante], int]:
    filtros = [
        PerfilMigrante.institucion_id == institucion_id,
        PerfilMigrante.usuario_registro_id == usuario_id,
    ]
    if estado:
        filtros.append(PerfilMigrante.estado_formulario == estado)
    if q:
        filtros.append(PerfilMigrante.codigo_identificador.ilike(f"%{q}%"))

    total = db.scalar(select(func.count()).select_from(PerfilMigrante).where(*filtros)) or 0
    items = db.scalars(
        select(PerfilMigrante)
        .where(*filtros)
        .order_by(PerfilMigrante.fecha_actualizacion.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(items), total


def guardar(db: Session, perfil: PerfilMigrante) -> PerfilMigrante:
    db.add(perfil)
    db.commit()
    db.refresh(perfil)
    return perfil


def eliminar(db: Session, perfil: PerfilMigrante) -> None:
    db.delete(perfil)
    db.commit()