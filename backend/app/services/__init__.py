"""Services package"""
from app.services.ai_service import ai_service, AssignmentRecommendation
from app.services.email_service import email_service

__all__ = ["ai_service", "email_service", "AssignmentRecommendation"]
