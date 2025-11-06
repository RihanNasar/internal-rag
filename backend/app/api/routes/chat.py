from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.services import langgraph_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request schema"""
    message: str


class ChatResponse(BaseModel):
    """Chat response schema"""
    response: str
    task_id: int | None = None
    confidence: float | None = None


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Chat endpoint - provides conversational interface
    
    In the full implementation, this could be enhanced with:
    - Conversation history tracking
    - Multi-turn dialogues
    - Task clarification before creation
    - Status queries
    
    For now, it provides information about the system
    """
    message = request.message.lower().strip()
    
    # Simple intent detection
    if any(word in message for word in ["hello", "hi", "hey"]):
        return ChatResponse(
            response="Hello! I'm your AI task assignment assistant. You can describe a task, and I'll find the best team member to handle it. Just tell me what needs to be done!"
        )
    
    elif any(word in message for word in ["help", "how", "what"]):
        return ChatResponse(
            response="I can help you assign tasks to team members! Here's how it works:\n\n"
                    "1. Describe the task you need done\n"
                    "2. I'll analyze the requirements and match them with team members' skills\n"
                    "3. If I'm confident, I'll auto-assign it. Otherwise, it'll go for manual review\n\n"
                    "Try describing a task like: 'Create a FastAPI backend for user authentication'"
        )
    
    elif any(word in message for word in ["status", "tasks", "list"]):
        from app.models.task import Task, TaskStatus
        
        pending = db.query(Task).filter(Task.status == TaskStatus.PENDING).count()
        assigned = db.query(Task).filter(Task.status == TaskStatus.AUTO_ASSIGNED).count()
        review = db.query(Task).filter(Task.status == TaskStatus.MANUAL_REVIEW).count()
        completed = db.query(Task).filter(Task.status == TaskStatus.COMPLETED).count()
        
        return ChatResponse(
            response=f"📊 Task Status Summary:\n\n"
                    f"✅ Completed: {completed}\n"
                    f"🤖 Auto-assigned: {assigned}\n"
                    f"⏳ Pending: {pending}\n"
                    f"👤 Manual review: {review}"
        )
    
    elif any(word in message for word in ["team", "members", "who"]):
        from app.models.team_member import TeamMember
        
        members = db.query(TeamMember).filter(TeamMember.is_active == True).all()
        
        if not members:
            return ChatResponse(response="No team members available. Please add team members first.")
        
        member_list = "\n".join([
            f"• {m.name} - {m.role} ({m.current_workload}/{m.max_workload} tasks)"
            for m in members
        ])
        
        return ChatResponse(
            response=f"👥 Team Members ({len(members)}):\n\n{member_list}"
        )
    
    else:
        # Default response - guide user to create a task
        return ChatResponse(
            response="To assign a task, please use the task creation interface or describe your task in detail. "
                    "For example: 'Build a React dashboard with charts and analytics'.\n\n"
                    "You can also ask me about:\n"
                    "• 'help' - Learn how to use the system\n"
                    "• 'status' - See task statistics\n"
                    "• 'team' - View team members"
        )
