"""Test the AI service"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ai_service import ai_service
from app.database.connection import SessionLocal
from app.models.team_member import TeamMember


async def test_ai_recommendation():
    print("=" * 70)
    print("Testing AI Service")
    print("=" * 70)
    
    # Get team members from database
    db = SessionLocal()
    try:
        team_members = db.query(TeamMember).all()
        
        if not team_members:
            print("❌ No team members found. Run add_sample_data.py first.")
            return
        
        print(f"\n✅ Found {len(team_members)} team members:")
        for m in team_members:
            print(f"  - {m.name} ({m.role}) - Skills: {', '.join(m.skills[:3])}")
        
        # Test task
        task_description = "Build a REST API for user authentication using FastAPI and PostgreSQL"
        
        print(f"\n📋 Task: {task_description}")
        print("\n🤖 Getting AI recommendation...")
        
        recommendation = await ai_service.get_assignment_recommendation(
            task_description=task_description,
            team_members=team_members
        )
        
        print("\n" + "=" * 70)
        print("AI RECOMMENDATION")
        print("=" * 70)
        print(f"👤 Assigned to: {recommendation.team_member_name}")
        print(f"📧 Email: {recommendation.team_member_email}")
        print(f"📊 Confidence: {recommendation.confidence_score * 100:.1f}%")
        print(f"🎯 Matched Skills: {', '.join(recommendation.matched_skills)}")
        print(f"\n💡 Reasoning:")
        print(f"   {recommendation.reasoning}")
        print("=" * 70)
        
        if recommendation.confidence_score >= 0.75:
            print("\n✅ HIGH CONFIDENCE - Would auto-assign")
        else:
            print("\n⚠️  LOW CONFIDENCE - Needs manual review")
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_ai_recommendation())