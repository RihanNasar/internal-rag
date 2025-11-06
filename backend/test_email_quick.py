"""Quick email test script"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.email_service import email_service
from app.config import get_settings

async def test_email():
    settings = get_settings()
    
    print("=" * 60)
    print("EMAIL CONFIGURATION TEST")
    print("=" * 60)
    print(f"SMTP Host: {settings.smtp_host}")
    print(f"SMTP Port: {settings.smtp_port}")
    print(f"SMTP User: {settings.smtp_user}")
    print(f"Password Set: {'Yes' if settings.smtp_password else 'No'}")
    print("=" * 60)
    
    test_email_address = input("\nEnter email address to send test to: ").strip()
    
    if not test_email_address:
        print("❌ No email address provided")
        return
    
    print(f"\n📧 Sending test email to: {test_email_address}")
    print("Please wait...\n")
    
    success = await email_service.send_task_assignment(
        to_email=test_email_address,
        team_member_name="Test User",
        task_description="Create a REST API endpoint for user authentication",
        confidence_score=0.92,
        reasoning="You have strong experience with API development and security best practices."
    )
    
    if success:
        print("✅ Email sent successfully!")
        print("\nCheck your inbox (and spam/junk folder if not in inbox)")
        print(f"Email sent to: {test_email_address}")
    else:
        print("❌ Failed to send email")
        print("Check the error messages above for details")

if __name__ == "__main__":
    asyncio.run(test_email())