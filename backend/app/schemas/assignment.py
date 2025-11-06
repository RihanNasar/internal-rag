from pydantic import BaseModel
from typing import List
from datetime import datetime


class AssignmentHistoryResponse(BaseModel):
    """Schema for assignment history response"""
    id: int
    task_id: int
    team_member_id: int
    confidence_score: float
    reasoning: str | None
    matched_skills: List[str] | None
    assigned_by: str
    created_at: datetime
    
    class Config:
        from_attributes = True
