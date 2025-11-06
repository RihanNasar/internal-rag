from sqlalchemy import Column, Integer, String, JSON, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class TeamMember(Base):
    """Team member model"""
    __tablename__ = "team_members"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    role = Column(String, nullable=False)
    skills = Column(JSON, nullable=False)  # ["Python", "FastAPI", "React"]
    responsibilities = Column(String, nullable=False)
    current_workload = Column(Integer, default=0)
    max_workload = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks = relationship("Task", back_populates="assignee")
    
    def __repr__(self):
        return f"<TeamMember(id={self.id}, name='{self.name}', role='{self.role}')>"
