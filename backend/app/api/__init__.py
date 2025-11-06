from fastapi import APIRouter

# Import route modules
from app.api.routes import tasks, team, chat, knowledge

# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(tasks.router)
api_router.include_router(team.router)
api_router.include_router(chat.router)
api_router.include_router(knowledge.router)

__all__ = ["api_router"]
