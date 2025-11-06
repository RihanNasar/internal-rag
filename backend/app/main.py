"""Main FastAPI application"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import api_router
from app.config import get_settings
from app.database.connection import init_db
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
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
        "message": "Task Assignment AI API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check called")
    return {
        "status": "healthy",
        "service": "Task Assignment AI"
    }

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("🚀 Starting Task Assignment AI...")
    logger.info(f"Environment: {'Development' if settings.debug else 'Production'}")
    logger.info(f"Frontend URL: {settings.frontend_url}")
    
    try:
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    # Initialize RAG service with documents
    try:
        from app.services.rag_service import rag_service
        logger.info("📚 Initializing RAG knowledge base...")
        
        # Load documents from the documents folder
        doc_count = rag_service.load_documents("documents")
        logger.info(f"✅ RAG initialized with {doc_count} document chunks")
    except Exception as e:
        logger.warning(f"⚠️ RAG initialization failed (will initialize on first upload): {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Shutting down Task Assignment AI...")
