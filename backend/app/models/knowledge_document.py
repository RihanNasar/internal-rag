"""Knowledge document model for tracking uploaded documents"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class KnowledgeDocument(Base):
    """Model for tracking uploaded knowledge base documents"""
    __tablename__ = "knowledge_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # pdf, txt
    content_preview = Column(Text)  # First 500 chars preview
    chunks_count = Column(Integer, default=0)
    source = Column(String, default="user_upload")  # user_upload, system
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<KnowledgeDocument(id={self.id}, filename='{self.filename}')>"
