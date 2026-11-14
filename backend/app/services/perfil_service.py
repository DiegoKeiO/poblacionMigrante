import secrets
import uuid

from sqlalchemy.orm import Session

from app.core.catalogos import (
    CAMPOS_DERIVADOS,
    CAMPOS_REQUERIDOS,
    aplica_homologacion,
    aplica_titulo,
    derivar_educacion,
)
from app.core.exceptions import AppError
from app.models.perfil_migrante import PerfilMigrante
from app.models.usuario import Usuario
from app.repositories import perfil_repo
from app.schemas.perfil import PerfilIn

NO_ESPECIFICADO = "No Especificado"


def _normalizar_aplicabilidad(datos: dict) -> None:
    """Aplica las reglas de aplicabilidad vistas en el entrenamiento.

    - obtuvo_titulo solo se responde con cierto nivel educativo en Venezuela;
      en otro caso el modelo vio 'No Especificado'.
    - homologo_titulo_peru solo se responde si obtuvo_titulo == '1'.
    """
    nivel_ven = datos.get("nivel_educ_venezuela")
    if nivel_ven is not None and not aplica_titulo(nivel_ven):
        datos["obtuvo_titulo"] = NO_ESPECIFICADO

    titulo = datos.get("obtuvo_titulo")
    if titulo is not None and not aplica_homologacion(titulo):
        datos["homologo_titulo_peru"] = NO_ESPECIFICADO


def _derivar_educacion(datos: dict) -> None:
    """Calcula años de escolaridad y brecha, igual que en el preprocesamiento.

    Si no hay equivalencia (códigos 99), las claves no se guardan: el módulo de
    inferencia las imputará con las medianas de entrenamiento.
    """
    for campo in CAMPOS_DERIVADOS:
        datos.pop(campo, None)

    nv, np_ = datos.get("nivel_educ_venezuela"), datos.get("nivel_educ_peru")
    if nv is None or np_ is None:
        return
    for campo, valor in derivar_educacion(nv, np_).items():
        if valor is not None:
            datos[campo] = valor


def _preparar_datos(payload: PerfilIn) -> dict:
    datos = payload.datos.model_dump(exclude_none=True)
    _normalizar_aplicabilidad(datos)
    _derivar_educacion(datos)
    return datos


def _validar_completo(datos: dict, consentimiento: bool) -> None:
    faltantes = [c for c in CAMPOS_REQUERIDOS if c not in datos]
    if faltantes:
        raise AppError(422, f"Faltan campos obligatorios: {', '.join(faltantes)}.")

    nv = datos["nivel_educ_venezuela"]
    if aplica_titulo(nv) and datos["obtuvo_titulo"] == NO_ESPECIFICADO:
        raise AppError(422, "Debe indicar si obtuvo el título (nivel educativo en Venezuela con título).")
    if datos["obtuvo_titulo"] == "1" and datos["homologo_titulo_peru"] == NO_ESPECIFICADO:
        raise AppError(422, "Debe indicar si homologó el título en el Perú.")

    if not consentimiento:
        raise AppError(422, "Se requiere el consentimiento de tratamiento de datos del migrante.")


def _aplicar(perfil: PerfilMigrante, payload: PerfilIn, datos: dict, estado: str) -> None:
    perfil.datos_formulario = datos
    perfil.estado_formulario = estado
    perfil.consentimiento_datos = payload.consentimiento_datos
    perfil.condicion_laboral_actual = payload.condicion_laboral_actual
    # Columnas espejo para filtros del historial (guardan el código del modelo)
    perfil.sexo = datos.get("sexo")
    perfil.edad = datos.get("edad")
    perfil.nacionalidad = datos.get("nacionalidad")
    # Se usa el nivel en Venezuela porque el 95 % de los casos tiene nivel Perú = 13
    perfil.nivel_educativo = datos.get("nivel_educ_venezuela")


def crear(db: Session, usuario: Usuario, payload: PerfilIn) -> PerfilMigrante:
    datos = _preparar_datos(payload)
    if payload.completar:
        _validar_completo(datos, payload.consentimiento_datos)

    perfil = PerfilMigrante(
        institucion_id=usuario.institucion_id,
        usuario_registro_id=usuario.id,
        codigo_identificador=f"MIG-{secrets.token_hex(4).upper()}",
    )
    _aplicar(perfil, payload, datos, "completo" if payload.completar else "borrador")
    return perfil_repo.guardar(db, perfil)


def obtener(db: Session, usuario: Usuario, perfil_id: uuid.UUID) -> PerfilMigrante:
    perfil = perfil_repo.get(db, perfil_id, usuario.institucion_id, usuario.id)
    if perfil is None:
        raise AppError(404, "Perfil no encontrado.")
    return perfil


def actualizar(db: Session, usuario: Usuario, perfil_id: uuid.UUID, payload: PerfilIn) -> PerfilMigrante:
    perfil = obtener(db, usuario, perfil_id)
    datos = _preparar_datos(payload)

    # Un perfil completo no puede volver a quedar incompleto al editarlo.
    estado = "completo" if (payload.completar or perfil.estado_formulario == "completo") else "borrador"
    if estado == "completo":
        _validar_completo(datos, payload.consentimiento_datos)

    _aplicar(perfil, payload, datos, estado)
    return perfil_repo.guardar(db, perfil)


def eliminar_borrador(db: Session, usuario: Usuario, perfil_id: uuid.UUID) -> None:
    perfil = obtener(db, usuario, perfil_id)
    if perfil.estado_formulario != "borrador":
        raise AppError(409, "Solo se pueden eliminar perfiles en borrador.")
    perfil_repo.eliminar(db, perfil)


def listar(db: Session, usuario: Usuario, estado: str | None, q: str | None, page: int, page_size: int):
    return perfil_repo.listar(db, usuario.institucion_id, usuario.id, estado, q, page, page_size)