import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Institucion(Base):
    __tablename__ = "instituciones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    siglas: Mapped[str | None] = mapped_column(String(30))
    ruc: Mapped[str | None] = mapped_column(String(11), unique=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fecha_registro: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    usuarios = relationship("Usuario", back_populates="institucion")
    perfiles = relationship("PerfilMigrante", back_populates="institucion")