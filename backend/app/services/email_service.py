"""Email service for sending notifications"""
import httpx
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailService:
    """Service for sending email notifications via Brevo HTTP API"""
    
    async def send_task_assignment(
        self,
        to_email: str,
        team_member_name: str,
        task_description: str,
        confidence_score: float,
        reasoning: str
    ):
        """Send task assignment notification email"""
        try:
            logger.info(f"📧 Preparing to send email to {to_email}")
            
            if not settings.brevo_api_key:
                logger.error("❌ BREVO_API_KEY not configured")
                return False
            
            logger.info(f"🔑 Using Brevo API key: {settings.brevo_api_key[:15]}...")
            
            # Create HTML email content
            html = f"""
<html>
  <head>
    <style>
      body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
      .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
      .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
      .content {{ background: #f9f9f9; padding: 20px; border-radius: 0 0 8px 8px; }}
      .task-box {{ background: white; padding: 15px; margin: 15px 0; border-left: 4px solid #667eea; border-radius: 4px; }}
      .confidence {{ display: inline-block; padding: 5px 10px; background: #10b981; color: white; border-radius: 4px; font-weight: bold; }}
      .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
    </style>
  </head>
  <body>
    <div class="container">
      <div class="header">
        <h2>🎯 New Task Assignment</h2>
      </div>
      <div class="content">
        <p>Hello <strong>{team_member_name}</strong>,</p>
        <p>You have been assigned a new task by our AI assignment system:</p>
        
        <div class="task-box">
          <h3>📋 Task Description</h3>
          <p>{task_description}</p>
        </div>
        
        <p>
          <strong>AI Confidence:</strong> 
          <span class="confidence">{confidence_score * 100:.1f}%</span>
        </p>
        
        <div class="task-box">
          <h3>💡 Why you were selected</h3>
          <p>{reasoning}</p>
        </div>
        
        <p>Please review and start working on this task at your earliest convenience.</p>
        
        <div class="footer">
          <p>This is an automated message from the Task Assignment AI System</p>
        </div>
      </div>
    </div>
  </body>
</html>
            """
            
            # Plain text version
            text = f"""
Hello {team_member_name},

You have been assigned a new task:

Task: {task_description}

Assignment Confidence: {confidence_score * 100:.1f}%

Reasoning: {reasoning}

Please review and start working on this task.

Best regards,
Task Assignment AI
            """
            
            logger.info(f"🔄 Sending email via Brevo API to {to_email}")
            logger.info(f"📧 From: {settings.email_from_name} <{settings.email_from_address}>")
            
            # Send via Brevo's pure HTTP API
            url = "https://api.brevo.com/v3/smtp/email"
            headers = {
                "accept": "application/json",
                "api-key": settings.brevo_api_key,
                "content-type": "application/json"
            }
            payload = {
                "sender": {
                    "name": settings.email_from_name,
                    "email": settings.email_from_address
                },
                "to": [
                    {
                        "email": to_email,
                        "name": team_member_name
                    }
                ],
                "subject": "New Task Assignment",
                "htmlContent": html,
                "textContent": text
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=30.0)
                response.raise_for_status()
                result = response.json()
            
            logger.info(f"✅ Email sent successfully to {to_email} - Message ID: {result.get('messageId', 'unknown')}")
            return True
            
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Brevo HTTP error sending to {to_email}: {e.response.status_code} - {e.response.text}")
            logger.exception("Full error details:")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
            logger.error(f"📧 Email Config - From: {settings.email_from_name} <{settings.email_from_address}>, API Key Set: {bool(settings.brevo_api_key)}")
            logger.exception("Full error details:")
            return False


# Singleton instance
email_service = EmailService()
