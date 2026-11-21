import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.models.usuario import Usuario
from app.schemas.prediccion import PrediccionIn, PrediccionOut, PrediccionResumenOut
from app.services import prediccion_service

router = APIRouter(prefix="/predicciones", tags=["predicciones"])

trabajador = require_role("trabajador")


@router.post("", response_model=PrediccionOut, status_code=status.HTTP_201_CREATED)
def ejecutar(payload: PrediccionIn, db: Session = Depends(get_db), usuario: Usuario = Depends(trabajador)):
    """Ejecuta el modelo sobre un perfil completo y devuelve el dashboard de resultado."""
    prediccion_id = prediccion_service.ejecutar(db, usuario, payload.perfil_id)
    return prediccion_service.obtener(db, usuario, prediccion_id)


@router.get("", response_model=list[PrediccionResumenOut])
def listar_por_perfil(perfil_id: uuid.UUID, db: Session = Depends(get_db), usuario: Usuario = Depends(trabajador)):
    """Historial de predicciones de un perfil (más reciente primero)."""
    return prediccion_service.listar_por_perfil(db, usuario, perfil_id)


@router.get("/{prediccion_id}", response_model=PrediccionOut)
def obtener(prediccion_id: uuid.UUID, db: Session = Depends(get_db), usuario: Usuario = Depends(trabajador)):
    return prediccion_service.obtener(db, usuario, prediccion_id)