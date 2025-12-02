from fastapi import APIRouter
from app.api.v1.endpoints import auth, leads, admin

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(leads.router, prefix="/leads", tags=["leads"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
