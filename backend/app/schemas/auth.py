import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegistroRequest(BaseModel):
    nombre_completo: str = Field(min_length=3, max_length=150)
    correo: EmailStr
    password: str = Field(min_length=8, max_length=72)
    institucion_id: uuid.UUID


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre_completo: str
    correo: str
    rol: str
    institucion_id: uuid.UUID


class InstitucionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str
    siglas: str | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut