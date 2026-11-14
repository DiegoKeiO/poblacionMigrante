from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.usuario import Usuario
from app.repositories import institucion_repo
from app.schemas.auth import InstitucionOut, RegistroRequest, TokenOut, UsuarioOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/instituciones", response_model=list[InstitucionOut])
def listar_instituciones(db: Session = Depends(get_db)):
    """Lista pública de instituciones activas (para el formulario de registro)."""
    return institucion_repo.list_activas(db)


@router.post("/registro", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def registro(datos: RegistroRequest, db: Session = Depends(get_db)):
    return auth_service.registrar(db, datos)


@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """El campo `username` del formulario recibe el correo."""
    token, usuario = auth_service.autenticar(db, form.username, form.password)
    return TokenOut(access_token=token, usuario=usuario)


@router.get("/me", response_model=UsuarioOut)
def me(usuario: Usuario = Depends(get_current_user)):
    return usuario