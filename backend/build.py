#!/usr/bin/env python3
"""
Database initialization script for Render deployment
"""
import asyncio
import logging
from app.database.connection import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Initialize database tables"""
    try:
        logger.info("🔄 Initializing database tables...")
        init_db()
        logger.info("✅ Database tables initialized successfully!")
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        raise

if __name__ == "__main__":
    main()
