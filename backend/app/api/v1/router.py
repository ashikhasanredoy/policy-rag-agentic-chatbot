from fastapi import APIRouter
from backend.app.api.v1.chat import router as chat_router
from backend.app.api.v1.policies import router as policies_router
from backend.app.api.v1.admin import router as admin_router
from backend.app.api.v1.health import router as health_router

api_v1_router = APIRouter()

api_v1_router.include_router(chat_router)
api_v1_router.include_router(policies_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(health_router)
