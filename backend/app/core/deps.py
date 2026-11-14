import uuid
from collections.abc import Callable, Generator

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.usuario import Usuario
from app.repositories import usuario_repo

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise AppError(401, "Sesión inválida o expirada. Inicia sesión nuevamente.")

    try:
        user_id = uuid.UUID(payload["sub"])
    except ValueError:
        raise AppError(401, "Sesión inválida.")

    usuario = usuario_repo.get_by_id(db, user_id)
    if usuario is None or not usuario.activo:
        raise AppError(401, "Usuario no encontrado o desactivado.")
    return usuario


def require_role(*roles: str) -> Callable[[Usuario], Usuario]:
    def checker(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if usuario.rol not in roles:
            raise AppError(403, "No tienes permisos para realizar esta acción.")
        return usuario

    return checker