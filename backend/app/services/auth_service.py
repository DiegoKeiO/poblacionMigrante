from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.usuario import Usuario
from app.repositories import institucion_repo, usuario_repo
from app.schemas.auth import RegistroRequest


def registrar(db: Session, datos: RegistroRequest) -> Usuario:
    institucion = institucion_repo.get_by_id(db, datos.institucion_id)
    if institucion is None or not institucion.activo:
        raise AppError(404, "La institución seleccionada no existe o no está activa.")

    if usuario_repo.get_by_correo(db, datos.correo):
        raise AppError(409, "Ya existe una cuenta registrada con ese correo.")

    usuario = Usuario(
        institucion_id=datos.institucion_id,
        nombre_completo=datos.nombre_completo.strip(),
        correo=datos.correo.lower(),
        password_hash=hash_password(datos.password),
        rol="trabajador",
    )
    return usuario_repo.create(db, usuario)


def autenticar(db: Session, correo: str, password: str) -> tuple[str, Usuario]:
    usuario = usuario_repo.get_by_correo(db, correo)
    if usuario is None or not verify_password(password, usuario.password_hash):
        raise AppError(401, "Correo o contraseña incorrectos.")
    if not usuario.activo:
        raise AppError(403, "La cuenta está desactivada.")

    token = create_access_token(str(usuario.id), usuario.rol)
    return token, usuario