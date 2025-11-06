from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, JSON, Text
from datetime import datetime
from app.database.connection import Base


class AssignmentHistory(Base):
    """Assignment history model for tracking all assignment decisions"""
    __tablename__ = "assignment_history"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    team_member_id = Column(Integer, ForeignKey("team_members.id"), nullable=False)
    confidence_score = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=True)
    matched_skills = Column(JSON, nullable=True)
    assigned_by = Column(String, nullable=False)  # "AI" or "Human"
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<AssignmentHistory(task_id={self.task_id}, team_member_id={self.team_member_id})>"
