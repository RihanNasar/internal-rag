from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database.connection import Base


class TaskStatus(str, enum.Enum):
    """Task status enumeration"""
    PENDING = "pending"
    AUTO_ASSIGNED = "auto_assigned"
    MANUAL_REVIEW = "manual_review"
    COMPLETED = "completed"
    REJECTED = "rejected"


class Task(Base):
    """Task model"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, index=True)
    confidence_score = Column(Float, nullable=True)
    assigned_to = Column(Integer, ForeignKey("team_members.id"), nullable=True)
    assigned_by = Column(String, default="AI")  # "AI" or "Human"
    reasoning = Column(Text, nullable=True)
    matched_skills = Column(String, nullable=True)  # JSON string of matched skills
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    assigned_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    assignee = relationship("TeamMember", back_populates="tasks")
    
    def __repr__(self):
        return f"<Task(id={self.id}, status='{self.status}', assigned_to={self.assigned_to})>"
