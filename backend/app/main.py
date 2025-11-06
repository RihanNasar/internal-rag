"""Main FastAPI application"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import api_router
from app.config import get_settings
from app.database.connection import engine, Base
from app.models import TeamMember, Task, AssignmentHistory, KnowledgeDocument
import logging
import time
from contextlib import asynccontextmanager

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    logger.info("🚀 Starting application...")
    logger.info("🗄️  Creating database tables...")
    
    try:
        # Import all models to ensure they're registered with Base.metadata
        from app.models.team_member import TeamMember
        from app.models.task import Task
        from app.models.assignment import AssignmentHistory
        from app.models.knowledge_document import KnowledgeDocument
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully!")
        
        # Log which tables were created
        logger.info(f"📋 Tables: {list(Base.metadata.tables.keys())}")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    yield
    
    logger.info("👋 Shutting down...")

app = FastAPI(
    title="Internal RAG API",
    description="AI-powered task assignment and knowledge base",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - Allow frontend to connect
origins = [
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    settings.frontend_url,
]

# Add any additional origins from environment
if settings.frontend_url and settings.frontend_url not in origins:
    origins.append(settings.frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Skip detailed logging for OPTIONS (CORS preflight)
    if request.method == "OPTIONS":
        return await call_next(request)
    
    start_time = time.time()
    
    logger.info(f"📨 Incoming: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"✅ Completed: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.2f}s")
        return response
    except Exception as e:
        logger.error(f"❌ Error: {request.method} {request.url.path} - {str(e)}")
        raise

# Include API routes
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Internal RAG API",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from sqlalchemy import text
    from app.database.connection import SessionLocal
    
    db = SessionLocal()
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        
        # Check if tables exist
        result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """))
        tables = [row[0] for row in result]
        
        return {
            "status": "healthy",
            "database": "connected",
            "tables": tables
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
    finally:
        db.close()
