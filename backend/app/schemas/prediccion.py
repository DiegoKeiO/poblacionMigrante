import uuid
from datetime import datetime

from pydantic import BaseModel


class PrediccionIn(BaseModel):
    perfil_id: uuid.UUID


class NivelOut(BaseModel):
    evento: str      # qué mide este nivel
    nivel: str       # Bajo | Medio | Alto
    lectura: str     # cómo leerlo en la interfaz


class NivelesOut(BaseModel):
    desempleo: NivelOut
    formalidad: NivelOut


class FactorOut(BaseModel):
    variable: str
    nombre: str
    valor: str | float
    etiqueta: str | float
    shap: float
    empuja_hacia: str


class RecomendacionOut(BaseModel):
    orden: int
    id: str
    area_id: str
    area: str
    texto: str


class AreaOut(BaseModel):
    area: str
    cantidad: int


class PrediccionOut(BaseModel):
    id: uuid.UUID
    perfil_id: uuid.UUID
    codigo_identificador: str
    fecha_prediccion: datetime
    version_modelo: str
    clase: str
    clase_legible: str
    niveles_riesgo: NivelesOut
    etapa_explicada: str
    sentido_shap: str
    factores: list[FactorOut]
    recomendaciones: list[RecomendacionOut]
    areas_recomendadas: list[AreaOut]
    advertencia: str
    probabilidades: dict[str, float] | None = None  # solo si MOSTRAR_PROBABILIDADES=true


class PrediccionResumenOut(BaseModel):
    id: uuid.UUID
    fecha_prediccion: datetime
    version_modelo: str
    clase: str
    clase_legible: str
    niveles_riesgo: NivelesOut