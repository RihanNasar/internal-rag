from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database.connection import get_db
from app.services.ai_service import ai_service
from app.models.task import Task, TaskStatus
from app.models.team_member import TeamMember
from openai import AsyncOpenAI
from app.config import get_settings
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])
settings = get_settings()


class ChatRequest(BaseModel):
    """Chat request schema"""
    message: str


class ChatResponse(BaseModel):
    """Chat response schema"""
    response: str
    is_task_request: bool = False
    should_create_task: bool = False
    task_description: str | None = None


async def detect_task_intent(message: str) -> dict:
    """Use AI to determine if message is a task request or conversation"""
    
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    prompt = f"""You are an intent classifier for a task assignment system.

User message: "{message}"

Determine if this is:
1. A TASK REQUEST - User wants to assign/create a task (e.g., "Build a website", "Create API endpoints", "Fix bug in login")
2. A QUESTION - User asking for information (e.g., "What can you do?", "Show me tasks", "Who's on the team?")
3. A GREETING - Simple greeting/chitchat (e.g., "Hi", "Hello", "How are you?")

Respond with JSON:
{{
    "intent": "task_request" | "question" | "greeting",
    "confidence": 0.0-1.0,
    "task_description": "cleaned up task description if task_request, else null",
    "reasoning": "brief explanation"
}}

Only classify as "task_request" if the user is clearly asking to CREATE or ASSIGN work.
Questions about the system, greetings, or general queries are NOT task requests."""

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an intent classifier. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        result = response.choices[0].message.content.strip()
        
        # Clean up markdown code blocks if present
        if result.startswith("```json"):
            result = result.replace("```json", "").replace("```", "").strip()
        elif result.startswith("```"):
            result = result.replace("```", "").strip()
        
        return json.loads(result)
        
    except Exception as e:
        logger.error(f"Error in intent detection: {e}")
        # Fallback: assume it's a question
        return {
            "intent": "question",
            "confidence": 0.5,
            "task_description": None,
            "reasoning": "Error in AI classification"
        }


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Intelligent chat endpoint that:
    1. Detects if message is a task request or conversation
    2. Only creates tasks when user clearly wants to assign work
    3. Responds conversationally otherwise
    """
    
    message = request.message.strip()
    message_lower = message.lower()
    
    # Quick pattern matching for common queries (faster than AI)
    if any(word in message_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon"]):
        return ChatResponse(
            response="Hello! 👋 I'm your AI task assignment assistant.\n\n"
                    "I can help you:\n"
                    "• Assign tasks to team members\n"
                    "• Check task status\n"
                    "• View team availability\n\n"
                    "What would you like to do?",
            is_task_request=False
        )
    
    elif any(word in message_lower for word in ["help", "what can you do", "how does this work"]):
        return ChatResponse(
            response="🤖 I'm an AI-powered task assignment system!\n\n"
                    "**How it works:**\n"
                    "1. Tell me about a task (e.g., 'Build a REST API for user management')\n"
                    "2. I'll analyze which team member has the right skills\n"
                    "3. If I'm confident (>75%), I auto-assign it\n"
                    "4. Otherwise, it goes to manual review\n\n"
                    "**Try asking:**\n"
                    "• 'Show me task status' - View all tasks\n"
                    "• 'Who's on the team?' - See team members\n"
                    "• Just describe a task to assign it!",
            is_task_request=False
        )
    
    elif any(phrase in message_lower for phrase in ["show", "list", "status", "what tasks", "view tasks"]):
        pending = db.query(Task).filter(Task.status == TaskStatus.PENDING).count()
        assigned = db.query(Task).filter(Task.status == TaskStatus.AUTO_ASSIGNED).count()
        review = db.query(Task).filter(Task.status == TaskStatus.MANUAL_REVIEW).count()
        completed = db.query(Task).filter(Task.status == TaskStatus.COMPLETED).count()
        
        return ChatResponse(
            response=f"📊 **Task Status Summary**\n\n"
                    f"✅ Completed: {completed}\n"
                    f"🤖 Auto-assigned: {assigned}\n"
                    f"⏳ Pending: {pending}\n"
                    f"👤 Manual review: {review}\n\n"
                    f"Total: {pending + assigned + review + completed} tasks",
            is_task_request=False
        )
    
    elif any(phrase in message_lower for phrase in ["team", "members", "who", "show team", "list team"]):
        members = db.query(TeamMember).filter(TeamMember.is_active == True).all()
        
        if not members:
            return ChatResponse(
                response="⚠️ No team members found. Please add team members first!",
                is_task_request=False
            )
        
        member_list = "\n".join([
            f"• **{m.name}** - {m.role}\n  Skills: {', '.join(m.skills[:3])}{'...' if len(m.skills) > 3 else ''}\n  Workload: {m.current_workload}/{m.max_workload} tasks"
            for m in members
        ])
        
        return ChatResponse(
            response=f"👥 **Team Members** ({len(members)} total)\n\n{member_list}",
            is_task_request=False
        )
    
    # Use AI to detect if this is a task request
    logger.info(f"Using AI to detect intent for: {message[:50]}...")
    intent_result = await detect_task_intent(message)
    
    logger.info(f"Intent detection: {intent_result['intent']} (confidence: {intent_result['confidence']})")
    
    if intent_result["intent"] == "task_request" and intent_result["confidence"] > 0.7:
        # This is a task request!
        task_desc = intent_result["task_description"] or message
        
        return ChatResponse(
            response=f"Got it! I'll analyze this task:\n\n"
                    f"**Task:** {task_desc}\n\n"
                    f"Creating task and finding the best team member...",
            is_task_request=True,
            should_create_task=True,
            task_description=task_desc
        )
    
    elif intent_result["intent"] == "greeting":
        return ChatResponse(
            response="Hi there! 👋\n\n"
                    "I'm here to help assign tasks to your team.\n\n"
                    "**Quick actions:**\n"
                    "• Describe a task to assign it\n"
                    "• Ask 'show tasks' to see all tasks\n"
                    "• Ask 'show team' to see team members\n\n"
                    "What would you like to do?",
            is_task_request=False
        )
    
    else:
        # It's a question or unclear - be conversational
        return ChatResponse(
            response=f"I'm not sure if you want to create a task or just asking a question.\n\n"
                    f"**If you want to assign a task**, please describe it clearly:\n"
                    f"• ✅ Good: 'Create a FastAPI backend for user authentication'\n"
                    f"• ✅ Good: 'Fix the login bug in the mobile app'\n"
                    f"• ❌ Unclear: '{message[:50]}...'\n\n"
                    f"**Or ask me:**\n"
                    f"• 'Show tasks' - View all tasks\n"
                    f"• 'Show team' - See team members\n"
                    f"• 'Help' - Learn what I can do",
            is_task_request=False
        )
