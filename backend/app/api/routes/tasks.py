"""Task management routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, field_serializer
from datetime import datetime
from app.database.connection import get_db
from app.models.task import Task, TaskStatus
from app.services.ai_service import ai_service
from app.services.email_service import email_service
from app.models.team_member import TeamMember
import logging

router = APIRouter(prefix="/tasks", tags=["tasks"])
logger = logging.getLogger(__name__)


class TaskCreate(BaseModel):
    description: str


class TaskResponse(BaseModel):
    id: int
    description: str
    status: str
    confidence_score: Optional[float]
    assigned_to: Optional[int]
    assigned_by: str
    created_at: datetime
    assigned_at: Optional[datetime]

    class Config:
        from_attributes = True
    
    @field_serializer('created_at', 'assigned_at')
    def serialize_datetime(self, dt: Optional[datetime], _info) -> Optional[str]:
        """Serialize datetime to ISO format string"""
        if dt is None:
            return None
        return dt.isoformat()


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db)
):
    """Create a new task and auto-assign using AI"""
    logger.info(f"📝 Creating new task: {task_data.description[:50]}...")
    
    try:
        # Get all available team members
        team_members = db.query(TeamMember).all()
        
        if not team_members:
            logger.warning("No team members available")
            raise HTTPException(
                status_code=400,
                detail="No team members available. Please add team members first."
            )
        
        logger.info(f"Found {len(team_members)} team members")
        
        # Get AI recommendation
        logger.info("Getting AI recommendation...")
        recommendation = await ai_service.get_assignment_recommendation(
            task_description=task_data.description,
            team_members=team_members
        )
        
        logger.info(f"AI recommended: {recommendation.team_member_name} (confidence: {recommendation.confidence_score:.2%})")
        
        # Determine status based on confidence
        if recommendation.confidence_score >= 0.75:
            status = TaskStatus.AUTO_ASSIGNED
            assigned_to = recommendation.team_member_id
            assigned_by = "ai_auto"
        else:
            status = TaskStatus.MANUAL_REVIEW
            assigned_to = None
            assigned_by = "pending"
        
        # Create task
        task = Task(
            description=task_data.description,
            status=status.value,
            confidence_score=recommendation.confidence_score,
            assigned_to=assigned_to,
            assigned_by=assigned_by
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        logger.info(f"✅ Task created with ID: {task.id}, Status: {status.value}")
        
        # If auto-assigned, send email and update workload
        if status == TaskStatus.AUTO_ASSIGNED:
            member = db.query(TeamMember).filter(TeamMember.id == assigned_to).first()
            if member:
                # Update workload
                member.current_workload += 1
                db.commit()
                logger.info(f"Updated workload for {member.name}: {member.current_workload}/{member.max_workload}")
                
                # Send email (don't wait for it)
                try:
                    await email_service.send_task_assignment(
                        to_email=member.email,
                        team_member_name=member.name,
                        task_description=task.description,
                        confidence_score=recommendation.confidence_score,
                        reasoning=recommendation.reasoning
                    )
                    logger.info(f"📧 Email sent to {member.email}")
                except Exception as e:
                    logger.error(f"Email failed but task created: {e}")
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create task: {str(e)}"
        )


@router.get("/", response_model=List[TaskResponse])
def get_tasks(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all tasks, optionally filtered by status"""
    logger.info(f"📋 Fetching tasks (status filter: {status or 'all'})")
    
    try:
        query = db.query(Task)
        
        # Only filter if status is provided and not empty
        if status and status.strip():
            query = query.filter(Task.status == status)
        
        tasks = query.order_by(Task.created_at.desc()).all()
        logger.info(f"Found {len(tasks)} tasks")
        
        return tasks
        
    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch tasks: {str(e)}"
        )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific task by ID"""
    logger.info(f"Fetching task {task_id}")
    
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@router.post("/{task_id}/assign/{member_id}")
async def manual_assign(
    task_id: int,
    member_id: int,
    db: Session = Depends(get_db)
):
    """Manually assign a task to a team member"""
    logger.info(f"Manual assignment: Task {task_id} -> Member {member_id}")
    
    try:
        # Get task
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get team member
        member = db.query(TeamMember).filter(TeamMember.id == member_id).first()
        if not member:
            raise HTTPException(status_code=404, detail="Team member not found")
        
        # Check workload
        if member.current_workload >= member.max_workload:
            raise HTTPException(
                status_code=400,
                detail=f"{member.name} is at maximum workload capacity"
            )
        
        # Update old assignee workload if task was previously assigned
        if task.assigned_to:
            old_member = db.query(TeamMember).filter(TeamMember.id == task.assigned_to).first()
            if old_member and old_member.current_workload > 0:
                old_member.current_workload -= 1
        
        # Update task
        task.assigned_to = member_id
        task.status = TaskStatus.AUTO_ASSIGNED.value
        task.assigned_by = "manual"
        task.confidence_score = 1.0  # Manual assignment has 100% confidence
        task.assigned_at = datetime.utcnow()
        
        # Update workload
        member.current_workload += 1
        
        db.commit()
        
        logger.info(f"✅ Task {task_id} assigned to {member.name}")
        
        # Send email notification
        try:
            await email_service.send_task_assignment(
                to_email=member.email,
                team_member_name=member.name,
                task_description=task.description,
                confidence_score=1.0,
                reasoning=f"Task manually assigned by administrator."
            )
            logger.info(f"📧 Email sent to {member.email}")
        except Exception as e:
            logger.warning(f"Email notification failed: {e}")
        
        return {
            "success": True,
            "message": f"Task assigned to {member.name}",
            "task_id": task_id,
            "member_id": member_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in manual assignment: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to assign task: {str(e)}"
        )
