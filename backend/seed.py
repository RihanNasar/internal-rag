"""
Seed script to populate the database with sample team members
Run this script to add initial test data
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal, init_db
from app.models.team_member import TeamMember
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_team_members():
    """Seed database with sample team members"""
    
    # Initialize database
    init_db()
    
    db = SessionLocal()
    
    try:
        # Clear existing team members
        logger.info("Clearing existing team members...")
        db.query(TeamMember).delete()
        db.commit()
        
        # Create sample team members
        team_members = [
            TeamMember(
                name="Alice Johnson",
                email="alice@example.com",
                role="Senior Backend Developer",
                skills=["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "Redis", "SQLAlchemy"],
                responsibilities="Backend API development, database design and optimization, cloud infrastructure setup, API security implementation, performance tuning",
                max_workload=5,
                is_active=True
            ),
            TeamMember(
                name="Bob Smith",
                email="bob@example.com",
                role="Frontend Developer",
                skills=["React", "TypeScript", "JavaScript", "Tailwind CSS", "Vite", "HTML", "CSS", "Redux"],
                responsibilities="Frontend development, UI/UX implementation, responsive design, component libraries, state management, accessibility compliance",
                max_workload=5,
                is_active=True
            ),
            TeamMember(
                name="Carol Martinez",
                email="carol@example.com",
                role="Full Stack Developer",
                skills=["Python", "React", "Node.js", "MongoDB", "GraphQL", "TypeScript", "Express"],
                responsibilities="Full stack development, API integration, database management, end-to-end feature implementation, code reviews",
                max_workload=4,
                is_active=True
            ),
            TeamMember(
                name="David Lee",
                email="david@example.com",
                role="DevOps Engineer",
                skills=["Docker", "Kubernetes", "CI/CD", "AWS", "Terraform", "Jenkins", "Linux", "Bash"],
                responsibilities="Infrastructure automation, deployment pipelines, container orchestration, monitoring and logging, cloud resource management",
                max_workload=5,
                is_active=True
            ),
            TeamMember(
                name="Emma Wilson",
                email="emma@example.com",
                role="Data Scientist",
                skills=["Python", "Machine Learning", "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "SQL"],
                responsibilities="Data analysis, machine learning model development, data pipeline creation, statistical analysis, model deployment",
                max_workload=4,
                is_active=True
            ),
            TeamMember(
                name="Frank Zhang",
                email="frank@example.com",
                role="Mobile Developer",
                skills=["React Native", "iOS", "Android", "Swift", "Kotlin", "JavaScript", "Firebase"],
                responsibilities="Mobile app development, cross-platform solutions, mobile UI/UX, app store deployment, mobile performance optimization",
                max_workload=5,
                is_active=True
            ),
        ]
        
        # Add to database
        db.add_all(team_members)
        db.commit()
        
        logger.info(f"✅ Successfully seeded {len(team_members)} team members:")
        for member in team_members:
            logger.info(f"  • {member.name} - {member.role}")
        
    except Exception as e:
        logger.error(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("🌱 Starting database seed...")
    seed_team_members()
    logger.info("✨ Seed complete!")
