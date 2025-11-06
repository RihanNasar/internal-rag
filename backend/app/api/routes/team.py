"""Team member management routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr, field_serializer
from datetime import datetime
from app.database.connection import get_db
from app.models.team_member import TeamMember
import logging

router = APIRouter(prefix="/team", tags=["team"])
logger = logging.getLogger(__name__)


class TeamMemberCreate(BaseModel):
    name: str
    email: EmailStr
    role: str
    skills: List[str]
    responsibilities: str
    max_workload: int = 40


class TeamMemberUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    skills: Optional[List[str]] = None
    responsibilities: Optional[str] = None
    max_workload: Optional[int] = None


class TeamMemberResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    skills: List[str]
    responsibilities: str
    current_workload: int
    max_workload: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
    
    @field_serializer('created_at')
    def serialize_datetime(self, dt: datetime, _info) -> str:
        """Serialize datetime to ISO format string"""
        return dt.isoformat()


@router.post("/", response_model=TeamMemberResponse, status_code=201)
def create_team_member(
    member_data: TeamMemberCreate,
    db: Session = Depends(get_db)
):
    """Create a new team member"""
    logger.info(f"Creating team member: {member_data.name}")
    
    try:
        # Check if email already exists
        existing = db.query(TeamMember).filter(TeamMember.email == member_data.email).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Team member with email {member_data.email} already exists"
            )
        
        # Create new member
        member = TeamMember(
            name=member_data.name,
            email=member_data.email,
            role=member_data.role,
            skills=member_data.skills,
            responsibilities=member_data.responsibilities,
            max_workload=member_data.max_workload,
            current_workload=0
        )
        
        db.add(member)
        db.commit()
        db.refresh(member)
        
        logger.info(f"✅ Created team member: {member.name} (ID: {member.id})")
        
        return member
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating team member: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create team member: {str(e)}"
        )


@router.get("/", response_model=List[TeamMemberResponse])
def get_team_members(db: Session = Depends(get_db)):
    """Get all team members"""
    logger.info("Fetching all team members")
    
    try:
        members = db.query(TeamMember).order_by(TeamMember.name).all()
        logger.info(f"Found {len(members)} team members")
        return members
        
    except Exception as e:
        logger.error(f"Error fetching team members: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch team members: {str(e)}"
        )


@router.get("/{member_id}", response_model=TeamMemberResponse)
def get_team_member(
    member_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific team member by ID"""
    logger.info(f"Fetching team member {member_id}")
    
    member = db.query(TeamMember).filter(TeamMember.id == member_id).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    
    return member


@router.put("/{member_id}", response_model=TeamMemberResponse)
def update_team_member(
    member_id: int,
    member_data: TeamMemberUpdate,
    db: Session = Depends(get_db)
):
    """Update a team member"""
    logger.info(f"Updating team member {member_id}")
    
    try:
        member = db.query(TeamMember).filter(TeamMember.id == member_id).first()
        
        if not member:
            raise HTTPException(status_code=404, detail="Team member not found")
        
        # Update fields if provided
        update_data = member_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(member, field, value)
        
        db.commit()
        db.refresh(member)
        
        logger.info(f"✅ Updated team member: {member.name}")
        
        return member
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating team member: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update team member: {str(e)}"
        )


@router.delete("/{member_id}")
def delete_team_member(
    member_id: int,
    db: Session = Depends(get_db)
):
    """Delete a team member"""
    logger.info(f"Deleting team member {member_id}")
    
    try:
        member = db.query(TeamMember).filter(TeamMember.id == member_id).first()
        
        if not member:
            raise HTTPException(status_code=404, detail="Team member not found")
        
        db.delete(member)
        db.commit()
        
        logger.info(f"✅ Deleted team member: {member.name}")
        
        return {
            "success": True,
            "message": f"Team member {member.name} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting team member: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete team member: {str(e)}"
        )
