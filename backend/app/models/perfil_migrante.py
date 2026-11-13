import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PerfilMigrante(Base):
    __tablename__ = "perfiles_migrantes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institucion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instituciones.id"), nullable=False, index=True)
    usuario_registro_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    codigo_identificador: Mapped[str] = mapped_column(String(30), nullable=False)
    consentimiento_datos: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    estado_formulario: Mapped[str] = mapped_column(String(20), nullable=False, default="borrador")  # borrador | completo
    sexo: Mapped[str | None] = mapped_column(String(20))
    edad: Mapped[int | None] = mapped_column(Integer)
    nacionalidad: Mapped[str | None] = mapped_column(String(60))
    nivel_educativo: Mapped[str | None] = mapped_column(String(60))
    condicion_laboral_actual: Mapped[str | None] = mapped_column(String(40))
    datos_formulario: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    institucion = relationship("Institucion", back_populates="perfiles")
    usuario_registro = relationship("Usuario")
    predicciones = relationship("Prediccion", back_populates="perfil")