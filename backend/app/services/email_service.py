"""Email service for sending notifications"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailService:
    """Service for sending email notifications"""
    
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
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = "New Task Assignment"
            message["From"] = settings.smtp_user
            message["To"] = to_email
            
            # Create HTML and plain text versions
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
            
            # Attach both versions
            part1 = MIMEText(text, "plain")
            part2 = MIMEText(html, "html")
            message.attach(part1)
            message.attach(part2)
            
            # Send email
            logger.info(f"🔄 Connecting to SMTP server: {settings.smtp_host}:{settings.smtp_port}")
            
            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user,
                password=settings.smtp_password,
                start_tls=True,
            )
            
            logger.info(f"✅ Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
            logger.exception("Full error details:")
            return False


# Singleton instance
email_service = EmailService()
