"""Test email endpoint"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.services.email_service import email_service
import logging

router = APIRouter(prefix="/test", tags=["testing"])
logger = logging.getLogger(__name__)


class TestEmailRequest(BaseModel):
    to_email: EmailStr
    test_name: str = "Test User"


@router.post("/send-email")
async def test_send_email(request: TestEmailRequest):
    """Test email sending functionality"""
    try:
        logger.info(f"Testing email to {request.to_email}")
        
        success = await email_service.send_task_assignment(
            to_email=request.to_email,
            team_member_name=request.test_name,
            task_description="This is a test task to verify email functionality",
            confidence_score=0.95,
            reasoning="This is a test email sent from the Task Assignment AI system."
        )
        
        if success:
            return {
                "success": True,
                "message": f"Test email sent successfully to {request.to_email}",
                "details": "Check your inbox (and spam folder)"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to send email. Check backend logs for details."
            )
            
    except Exception as e:
        logger.error(f"Error in test email: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error sending test email: {str(e)}"
        )