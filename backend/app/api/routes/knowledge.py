"""Knowledge base management routes"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
import logging
import PyPDF2
import io
import re
from app.services.rag_service import rag_service
from app.services.ai_service import ai_service
from app.database.connection import get_db
from app.models.knowledge_document import KnowledgeDocument
from app.models.team_member import TeamMember
from app.models.task import Task
from app.models.assignment import AssignmentHistory

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a document to the knowledge base"""
    logger.info(f"📄 Uploading document: {file.filename}")
    
    try:
        # Read file content
        content = await file.read()
        
        # Extract text based on file type
        if file.filename.endswith('.pdf'):
            text = extract_text_from_pdf(content)
            file_type = 'pdf'
        elif file.filename.endswith('.txt'):
            text = content.decode('utf-8')
            file_type = 'txt'
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Please upload PDF or TXT files."
            )
        
        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Document appears to be empty or unreadable."
            )
        
        # Validate that document contains role/responsibility information
        if not validate_role_content(text):
            raise HTTPException(
                status_code=400,
                detail="Document does not contain role or responsibility information. Please upload documents with team roles, responsibilities, skills, or expertise descriptions."
            )
        
        # Add to RAG knowledge base (ChromaDB)
        doc_id = rag_service.add_document(
            content=text,
            metadata={
                "filename": file.filename,
                "file_type": file.content_type,
                "source": "user_upload"
            }
        )
        
        # Calculate chunks
        chunks_count = len(text) // 1000 + 1
        
        # Save metadata to PostgreSQL for tracking
        knowledge_doc = KnowledgeDocument(
            filename=file.filename,
            file_type=file_type,
            content_preview=text[:500] if len(text) > 500 else text,
            chunks_count=chunks_count,
            source="user_upload"
        )
        db.add(knowledge_doc)
        db.commit()
        db.refresh(knowledge_doc)
        
        # Parse and create team members from document
        created_members = await parse_and_create_team_members(text, file.filename, db)
        
        # Create serializable team member data before session closes
        team_members_data = [{"name": m.name, "role": m.role, "email": m.email} for m in created_members]
        
        logger.info(f"✅ Document uploaded successfully: {file.filename} (DB ID: {knowledge_doc.id}, Vector ID: {doc_id}, Team Members: {len(created_members)})")
        
        return {
            "message": "Document uploaded successfully",
            "filename": file.filename,
            "doc_id": doc_id,
            "db_id": knowledge_doc.id,
            "chunks_created": chunks_count,
            "team_members_created": len(created_members),
            "team_members": team_members_data
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.get("/stats")
async def get_knowledge_stats(db: Session = Depends(get_db)):
    """Get knowledge base statistics"""
    try:
        # Get vector store stats from ChromaDB
        vector_stats = rag_service.get_stats()
        
        # Get document count from PostgreSQL
        db_doc_count = db.query(KnowledgeDocument).count()
        
        return {
            **vector_stats,
            "documents_in_db": db_doc_count
        }
    except Exception as e:
        logger.error(f"Error getting knowledge stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get knowledge stats: {str(e)}"
        )


@router.get("/documents")
async def list_documents(db: Session = Depends(get_db)):
    """Get list of uploaded documents"""
    try:
        documents = db.query(KnowledgeDocument).order_by(KnowledgeDocument.uploaded_at.desc()).all()
        return [{
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "chunks_count": doc.chunks_count,
            "source": doc.source,
            "uploaded_at": doc.uploaded_at.isoformat(),
            "preview": doc.content_preview[:100] + "..." if len(doc.content_preview) > 100 else doc.content_preview
        } for doc in documents]
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.delete("/clear")
async def clear_knowledge_base(db: Session = Depends(get_db)):
    """Clear all documents from knowledge base and reset entire system"""
    try:
        logger.info("🗑️ Starting complete system clear...")
        
        # Clear vector store (ChromaDB)
        rag_service.clear_knowledge_base()
        logger.info("✓ ChromaDB cleared")
        
        # Clear all database tables in order (due to foreign key constraints)
        # 1. Clear assignment history first (has foreign keys to tasks and team_members)
        deleted_assignments = db.query(AssignmentHistory).delete()
        logger.info(f"✓ Cleared {deleted_assignments} assignment records")
        
        # 2. Clear tasks
        deleted_tasks = db.query(Task).delete()
        logger.info(f"✓ Cleared {deleted_tasks} tasks")
        
        # 3. Clear team members
        deleted_members = db.query(TeamMember).delete()
        logger.info(f"✓ Cleared {deleted_members} team members")
        
        # 4. Clear knowledge documents
        deleted_docs = db.query(KnowledgeDocument).delete()
        logger.info(f"✓ Cleared {deleted_docs} knowledge documents")
        
        db.commit()
        
        logger.info("🗑️ Complete system clear successful")
        return {
            "message": "All data cleared successfully",
            "cleared": {
                "assignments": deleted_assignments,
                "tasks": deleted_tasks,
                "team_members": deleted_members,
                "knowledge_documents": deleted_docs,
                "vector_store": "cleared"
            }
        }
    except Exception as e:
        logger.error(f"Error clearing system: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear system: {str(e)}"
        )


def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text from PDF bytes"""
    try:
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text_parts = []
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        return "\n".join(text_parts)
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting PDF text: {str(e)}"
        )


async def parse_and_create_team_members(text: str, filename: str, db: Session) -> List[TeamMember]:
    """
    Parse team member information from uploaded document and create them in the database.
    Uses AI to intelligently extract structured data from the text.
    """
    try:
        logger.info(f"🤖 Parsing team members from document: {filename}")
        logger.info(f"📄 Document preview (first 500 chars): {text[:500]}")
        
        # Use AI to extract team member information
        prompt = f"""
You are a data extraction assistant. Parse the following document and extract ALL team member information.

CRITICAL INSTRUCTIONS:
1. Extract EVERY person mentioned in the document
2. If email is provided in document, use the EXACT email - do NOT modify it
3. If email is NOT provided, generate one based on name: firstname.lastname@company.com
4. Return a JSON array with ALL people found

For each team member, extract:
- Name (exact name from document)
- Role/Title (exact title from document)  
- Email (if provided use exact email, if not provided generate: firstname.lastname@company.com)
- Skills (array of skills mentioned, or empty array if not specified)
- Responsibilities (brief description from the document)
- Max workload (default to 10 if not specified)

EXAMPLE INPUT:
"1. Sarah Chen - Digital Marketing Manager
   Responsibilities: Managing digital marketing campaigns.

2. David Kim - Content Strategy Lead
   Responsibilities: Developing content calendars."

EXAMPLE OUTPUT (return EXACTLY this format, no markdown, no extra text):
[
  {{
    "name": "Sarah Chen",
    "role": "Digital Marketing Manager",
    "email": "sarah.chen@company.com",
    "skills": [],
    "responsibilities": "Managing digital marketing campaigns.",
    "max_workload": 10
  }},
  {{
    "name": "David Kim",
    "role": "Content Strategy Lead",
    "email": "david.kim@company.com",
    "skills": [],
    "responsibilities": "Developing content calendars.",
    "max_workload": 10
  }}
]

Now extract from this document:
{text[:5000]}

Return ONLY the JSON array, no markdown code blocks, no extra text.
"""
        
        # Call AI service asynchronously
        response = await ai_service.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a precise data extraction assistant. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        import json
        content = response.choices[0].message.content.strip()
        logger.info(f"📝 AI Response: {content[:200]}...")
        
        # Clean up response - remove markdown code blocks if present
        content_clean = content.strip()
        if content_clean.startswith("```json"):
            content_clean = content_clean[7:]  # Remove ```json
        if content_clean.startswith("```"):
            content_clean = content_clean[3:]  # Remove ```
        if content_clean.endswith("```"):
            content_clean = content_clean[:-3]  # Remove trailing ```
        content_clean = content_clean.strip()
        
        # Parse JSON response
        members_data = json.loads(content_clean)
        
        logger.info(f"✅ Parsed {len(members_data)} team members from AI response")
        
        if not isinstance(members_data, list):
            logger.warning(f"AI returned non-list response, wrapping in array")
            members_data = [members_data]
        
        if len(members_data) == 0:
            logger.warning(f"⚠️ AI extracted 0 team members from document. Document might not contain proper team member format.")
            logger.warning(f"Expected format: Name (email@domain.com) - Role")
            return []
        
        created_members = []
        skipped_members = []
        
        for member_data in members_data:
            try:
                # Check if member already exists (by name AND email to avoid false positives with generated emails)
                existing = db.query(TeamMember).filter(
                    TeamMember.email == member_data["email"],
                    TeamMember.name == member_data["name"]
                ).first()
                
                if existing:
                    logger.info(f"⏭️ Team member already exists: {member_data['name']} ({member_data['email']})")
                    skipped_members.append(member_data['name'])
                    continue
                
                # Create new team member
                team_member = TeamMember(
                    name=member_data["name"],
                    role=member_data["role"],
                    email=member_data["email"],
                    skills=member_data.get("skills", []),
                    responsibilities=member_data.get("responsibilities", f"{member_data['role']} responsibilities"),
                    max_workload=member_data.get("max_workload", 10),
                    current_workload=0,
                    is_active=True
                )
                
                db.add(team_member)
                
                # Commit each member individually to avoid batch failures
                try:
                    db.commit()
                    db.refresh(team_member)
                    created_members.append(team_member)
                    logger.info(f"✅ Created team member: {team_member.name} - {team_member.role} ({team_member.email})")
                except Exception as commit_error:
                    db.rollback()
                    logger.warning(f"⚠️ Failed to create {member_data['name']}: {str(commit_error)}")
                    skipped_members.append(member_data['name'])
                    
            except Exception as member_error:
                logger.error(f"Error processing member {member_data.get('name', 'unknown')}: {member_error}")
                db.rollback()
                skipped_members.append(member_data.get('name', 'unknown'))
                continue
        
        if created_members:
            logger.info(f"🎉 Created {len(created_members)} new team members from {filename}")
        if skipped_members:
            logger.info(f"⏭️ Skipped {len(skipped_members)} existing/duplicate members: {', '.join(skipped_members[:5])}")
        if not created_members and not skipped_members:
            logger.info(f"ℹ️ No team members created or skipped")
        
        return created_members
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        logger.error(f"AI Response was: {content if 'content' in locals() else 'N/A'}")
        logger.error(f"Cleaned content was: {content_clean if 'content_clean' in locals() else 'N/A'}")
        return []
    except Exception as e:
        logger.error(f"Error parsing team members: {e}", exc_info=True)
        # Don't fail the upload if team member parsing fails
        return []


def validate_role_content(text: str) -> bool:
    """
    Validate that the document contains role/responsibility related content.
    Returns True if document contains relevant keywords, False otherwise.
    """
    # Convert to lowercase for case-insensitive matching
    text_lower = text.lower()
    
    # Keywords that indicate role/responsibility content
    role_keywords = [
        'role', 'roles', 'responsibility', 'responsibilities',
        'skill', 'skills', 'expertise', 'experience',
        'developer', 'engineer', 'designer', 'manager',
        'team member', 'position', 'job', 'title',
        'backend', 'frontend', 'full stack', 'data scientist',
        'qualified', 'proficient', 'expert', 'specialized',
        'task', 'tasks', 'duties', 'handle', 'manage',
        'technical', 'programming', 'development'
    ]
    
    # Check if at least 3 different keywords are present
    matched_keywords = sum(1 for keyword in role_keywords if keyword in text_lower)
    
    # Also check for common patterns like "Primary Responsibilities:", "Technical Skills:", etc.
    pattern_indicators = [
        'primary responsibilities',
        'technical skills',
        'best suited for',
        'expertise level',
        'years experience',
        'programming language',
        'can handle'
    ]
    
    has_patterns = any(pattern in text_lower for pattern in pattern_indicators)
    
    # Document is valid if it has at least 3 keywords OR at least one pattern
    return matched_keywords >= 3 or has_patterns
