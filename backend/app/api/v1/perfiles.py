import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.catalogos import CATEGORIAS, ETIQUETAS, NO_OFRECER_EN_UI, aplica_titulo
from app.core.deps import get_db, require_role
from app.models.usuario import Usuario
from app.schemas.perfil import PerfilIn, PerfilListOut, PerfilOut
from app.services import perfil_service

router = APIRouter(prefix="/perfiles", tags=["perfiles"])

trabajador = require_role("trabajador")


@router.get("/catalogos")
def catalogos(_: Usuario = Depends(trabajador)):
    """Opciones de las listas desplegables: valor = código del modelo, etiqueta = texto a mostrar."""
    opciones = {}
    for campo, codigos in CATEGORIAS.items():
        ocultos = NO_OFRECER_EN_UI.get(campo, set())
        opciones[campo] = [
            {"valor": c, "etiqueta": ETIQUETAS[campo][c]} for c in codigos if c not in ocultos
        ]
    return {
        "opciones": opciones,
        # Para que el frontend muestre u oculte los campos condicionales
        "reglas": {
            "niveles_venezuela_con_titulo": [
                c for c in CATEGORIAS["nivel_educ_venezuela"] if aplica_titulo(c)
            ],
        },
    }


@router.post("", response_model=PerfilOut, status_code=status.HTTP_201_CREATED)
def crear(payload: PerfilIn, db: Session = Depends(get_db), usuario: Usuario = Depends(trabajador)):
    return perfil_service.crear(db, usuario, payload)


@router.get("", response_model=PerfilListOut)
def listar(
    estado: str | None = Query(None, pattern="^(borrador|completo)$"),
    q: str | None = Query(None, max_length=30),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(trabajador),
):
    items, total = perfil_service.listar(db, usuario, estado, q, page, page_size)
    return PerfilListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/{perfil_id}", response_model=PerfilOut)
def obtener(perfil_id: uuid.UUID, db: Session = Depends(get_db), usuario: Usuario = Depends(trabajador)):
    return perfil_service.obtener(db, usuario, perfil_id)


@router.put("/{perfil_id}", response_model=PerfilOut)
def actualizar(
    perfil_id: uuid.UUID,
    payload: PerfilIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(trabajador),
):
    return perfil_service.actualizar(db, usuario, perfil_id, payload)


@router.delete("/{perfil_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(perfil_id: uuid.UUID, db: Session = Depends(get_db), usuario: Usuario = Depends(trabajador)):
    perfil_service.eliminar_borrador(db, usuario, perfil_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)