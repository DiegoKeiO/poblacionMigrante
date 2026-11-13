import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Prediccion(Base):
    __tablename__ = "predicciones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    perfil_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("perfiles_migrantes.id"), nullable=False, index=True)
    usuario_ejecutor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    version_modelo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("versiones_modelo.id"), nullable=False)
    inputs_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    clase_predicha: Mapped[str] = mapped_column(String(30), nullable=False) 
    prob_formal: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    prob_informal: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    prob_desempleado: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    valores_shap: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    tiempo_respuesta_ms: Mapped[int | None] = mapped_column(Integer)
    fecha_prediccion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    perfil = relationship("PerfilMigrante", back_populates="predicciones")
    usuario_ejecutor = relationship("Usuario")
    version_modelo = relationship("VersionModelo")
    recomendaciones = relationship("PrediccionRecomendacion", back_populates="prediccion")