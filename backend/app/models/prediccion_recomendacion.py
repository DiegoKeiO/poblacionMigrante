import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PrediccionRecomendacion(Base):
    __tablename__ = "prediccion_recomendaciones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediccion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("predicciones.id"), nullable=False, index=True)
    regla_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("catalogo_reglas.id"), nullable=False)
    orden_prioridad: Mapped[int] = mapped_column(Integer, nullable=False)
    variable_shap_asociada: Mapped[str | None] = mapped_column(String(80))

    prediccion = relationship("Prediccion", back_populates="recomendaciones")
    regla = relationship("CatalogoRegla")