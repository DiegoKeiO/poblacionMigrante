import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.catalogos import CATEGORIAS, codigo_modelo


class PerfilDatos(BaseModel):
    """Variables que la persona llena. Los años de escolaridad y la brecha
    NO se piden: se derivan de los niveles educativos en el servicio.
    Los valores categóricos son los CÓDIGOS del modelo ('1', '6.0', 'No Especificado')."""

    sexo: str | None = None
    edad: int | None = Field(None, ge=14, le=99)  # TODO: ajustar al rango real del dataset
    estado_civil: str | None = None
    nacionalidad: str | None = None
    nivel_educ_venezuela: str | None = None
    nivel_educ_peru: str | None = None
    obtuvo_titulo: str | None = None
    homologo_titulo_peru: str | None = None
    tipo_permiso_migratorio: str | None = None
    tiempo_residencia_anios: float | None = Field(None, ge=0, le=50)

    @field_validator(*CATEGORIAS.keys(), mode="before")
    @classmethod
    def validar_categoria(cls, valor, info):
        """Acepta 6, '6' o '6.0' y lo normaliza al formato exacto del entrenamiento."""
        if valor is None:
            return None
        campo = info.field_name
        try:
            normalizado = codigo_modelo(campo, valor)
        except (ValueError, TypeError):
            normalizado = str(valor)
        if normalizado not in CATEGORIAS[campo]:
            raise ValueError(f"Código no válido para {campo}. Permitidos: {', '.join(CATEGORIAS[campo])}")
        return normalizado


class PerfilIn(BaseModel):
    datos: PerfilDatos
    consentimiento_datos: bool = False
    condicion_laboral_actual: str | None = Field(None, max_length=40)
    completar: bool = False  # False = guardar como borrador


class PerfilOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    codigo_identificador: str
    estado_formulario: str
    consentimiento_datos: bool
    condicion_laboral_actual: str | None = None
    datos: dict = Field(validation_alias="datos_formulario")
    fecha_creacion: datetime
    fecha_actualizacion: datetime


class PerfilListOut(BaseModel):
    items: list[PerfilOut]
    total: int
    page: int
    page_size: int