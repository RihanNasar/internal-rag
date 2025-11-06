from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.task import TaskStatus


class TaskCreate(BaseModel):
    """Schema for creating a task"""
    description: str = Field(..., min_length=10, max_length=1000)


class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    description: str | None = None
    status: TaskStatus | None = None


class TaskResponse(BaseModel):
    """Schema for task response"""
    id: int
    description: str
    status: TaskStatus
    confidence_score: Optional[float]
    assigned_to: Optional[int]
    assigned_by: str
    reasoning: Optional[str]
    matched_skills: Optional[str]
    created_at: datetime
    assigned_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class AssignmentRecommendation(BaseModel):
    """Schema for AI assignment recommendation"""
    team_member_id: int
    team_member_name: str
    team_member_email: str
    team_member_role: str
    confidence_score: float
    reasoning: str
    matched_skills: List[str]
    workload_score: float


class TaskWithAssignee(TaskResponse):
    """Task with assignee details"""
    assignee: Optional[dict] = None
    
    class Config:
        from_attributes = True


class ManualAssignment(BaseModel):
    """Schema for manual task assignment"""
    task_id: int
    team_member_id: int
    reasoning: str = Field(default="Manually assigned by human reviewer")
