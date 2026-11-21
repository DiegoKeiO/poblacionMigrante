from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.deps import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request, db: Session = Depends(get_db)):
    """Verifica la API, la base de datos y el modelo de inferencia."""
    db.execute(text("SELECT 1"))
    error = getattr(request.app.state, "modelo_error", None)
    return {
        "status": "ok",
        "database": "connected",
        "modelo": "cargado" if error is None else "error",
        "detalle_modelo": error,
    }