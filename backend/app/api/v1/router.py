from fastapi import APIRouter

from app.api.v1 import admin, auth, health, perfiles, predicciones

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(perfiles.router)
api_router.include_router(predicciones.router)