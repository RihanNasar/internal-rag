from pydantic import BaseModel, EmailStr, Field
from typing import List
from datetime import datetime


class TeamMemberBase(BaseModel):
    """Base team member schema"""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    role: str = Field(..., min_length=1, max_length=100)
    skills: List[str] = Field(..., min_items=1)
    responsibilities: str = Field(..., min_length=1)
    max_workload: int = Field(default=5, ge=1, le=20)


class TeamMemberCreate(TeamMemberBase):
    """Schema for creating a team member"""
    pass


class TeamMemberUpdate(BaseModel):
    """Schema for updating a team member"""
    name: str | None = None
    email: EmailStr | None = None
    role: str | None = None
    skills: List[str] | None = None
    responsibilities: str | None = None
    max_workload: int | None = None
    is_active: bool | None = None


class TeamMemberResponse(TeamMemberBase):
    """Schema for team member response"""
    id: int
    current_workload: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TeamMemberSummary(BaseModel):
    """Simplified team member schema for listings"""
    id: int
    name: str
    email: str
    role: str
    current_workload: int
    max_workload: int
    is_active: bool
    
    class Config:
        from_attributes = True
