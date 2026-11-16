from fastapi import APIRouter

from app.api.v1 import auth, conversations, users
from app.api.v1.endpoints import health
from app.api.v1.workspace import router as workspace_router
from app.api.v1.ai import router as ai_router
from app.api.v1.review import router as review_router

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(conversations.router)
api_router.include_router(workspace_router)
api_router.include_router(ai_router)
api_router.include_router(review_router)
