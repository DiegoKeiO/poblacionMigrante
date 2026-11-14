from fastapi import APIRouter, Depends

from app.core.deps import require_role
from app.models.usuario import Usuario

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ping")
def ping_admin(usuario: Usuario = Depends(require_role("administrador"))):
    return {"mensaje": f"Hola {usuario.nombre_completo}, tienes acceso de administrador."}