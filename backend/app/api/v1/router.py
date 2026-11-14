from fastapi import APIRouter

from app.api.v1 import admin, auth, health, perfiles

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(perfiles.router)