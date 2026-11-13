import uuid

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CatalogoRegla(Base):
    __tablename__ = "catalogo_reglas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo_regla: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    area_tematica: Mapped[str] = mapped_column(String(80), nullable=False)
    clase_objetivo: Mapped[str] = mapped_column(String(30), nullable=False)
    condicion_disparo: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion_accionable: Mapped[str] = mapped_column(Text, nullable=False)
    entidad_derivacion: Mapped[str | None] = mapped_column(String(150))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)