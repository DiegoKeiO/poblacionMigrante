import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VersionModelo(Base):
    __tablename__ = "versiones_modelo"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo_version: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    archivo_etapa1_cbm: Mapped[str] = mapped_column(String(255), nullable=False)
    archivo_etapa2_cbm: Mapped[str] = mapped_column(String(255), nullable=False)
    config_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    metricas_evaluacion: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    activo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fecha_despliegue: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())