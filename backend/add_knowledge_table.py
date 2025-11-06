"""Add knowledge_documents table to database"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.connection import engine
from app.models.knowledge_document import KnowledgeDocument, Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_knowledge_documents_table():
    """Create the knowledge_documents table"""
    try:
        logger.info("Creating knowledge_documents table...")
        
        # Create only the knowledge_documents table
        KnowledgeDocument.__table__.create(bind=engine, checkfirst=True)
        
        logger.info("✅ knowledge_documents table created successfully")
        
    except Exception as e:
        logger.error(f"❌ Error creating table: {e}")
        raise

if __name__ == "__main__":
    add_knowledge_documents_table()
