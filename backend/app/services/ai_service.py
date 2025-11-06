"""AI service for task assignment recommendations"""
from typing import List
from pydantic import BaseModel
from openai import AsyncOpenAI
from app.config import get_settings
from app.models.team_member import TeamMember
from app.services.rag_service import rag_service
import logging
import json

logger = logging.getLogger(__name__)
settings = get_settings()


class AssignmentRecommendation(BaseModel):
    """AI assignment recommendation"""
    team_member_id: int
    team_member_name: str
    team_member_email: str
    confidence_score: float
    reasoning: str
    matched_skills: List[str]


class AIService:
    """Service for AI-powered task assignment"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        logger.info("AI Service initialized with OpenAI")
    
    async def get_assignment_recommendation(
        self,
        task_description: str,
        team_members: List[TeamMember]
    ) -> AssignmentRecommendation:
        """Get AI recommendation for task assignment"""
        
        logger.info(f"Getting AI recommendation for task: {task_description[:50]}...")
        logger.info(f"Analyzing {len(team_members)} team members")
        
        try:
            # Get relevant context from RAG knowledge base
            rag_context = ""
            try:
                rag_context = rag_service.get_relevant_context(task_description)
                if rag_context:
                    logger.info(f"📚 Retrieved {len(rag_context)} chars of context from knowledge base")
                else:
                    logger.info("📚 No additional context from knowledge base")
            except Exception as e:
                logger.warning(f"Could not retrieve RAG context: {e}")
            
            # Prepare team member data for AI
            members_data = []
            for member in team_members:
                members_data.append({
                    "id": member.id,
                    "name": member.name,
                    "email": member.email,
                    "role": member.role,
                    "skills": member.skills,
                    "responsibilities": member.responsibilities,
                    "current_workload": member.current_workload,
                    "max_workload": member.max_workload,
                    "availability": f"{member.max_workload - member.current_workload}/{member.max_workload}"
                })
            
            # Create the prompt
            prompt = f"""You are an AI task assignment system. Analyze the following task and team members, then recommend the best person to assign this task to.

Task Description:
{task_description}

Available Team Members:
{json.dumps(members_data, indent=2)}

Additional Knowledge Base Context:
{rag_context if rag_context else "No additional context available"}

Please analyze:
1. Which team member's skills best match this task
2. Their current workload and availability
3. Their role and responsibilities
4. Any additional expertise mentioned in the knowledge base context
5. Overall fit for the task

IMPORTANT: Be strict with confidence scoring. Only assign high confidence (>0.75) if there is a CLEAR and SPECIFIC skill match.
- If the task requires specialized skills (like blockchain, machine learning, etc.) that a team member doesn't explicitly have, score should be LOW (<0.70)
- Don't assume a team member can do something just because they're a developer

Respond with a JSON object in this exact format:
{{
    "team_member_id": <id>,
    "team_member_name": "<name>",
    "team_member_email": "<email>",
    "confidence_score": <0.0 to 1.0>,
    "reasoning": "<detailed explanation>",
    "matched_skills": ["skill1", "skill2"]
}}

The confidence_score should be:
- 0.9-1.0: Perfect match with all required skills explicitly listed
- 0.75-0.89: Very good match with most required skills (auto-assign threshold)
- 0.60-0.74: Partial match, missing some key skills - needs manual review
- Below 0.60: Poor match, missing critical skills

Only respond with the JSON object, no other text."""

            logger.info("Calling OpenAI API...")
            
            # Call OpenAI
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert task assignment AI that analyzes team member skills and task requirements to make optimal assignments."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            # Parse response
            ai_response = response.choices[0].message.content.strip()
            logger.info(f"AI Response received: {ai_response[:100]}...")
            
            # Clean up the response (remove markdown code blocks if present)
            if ai_response.startswith("```json"):
                ai_response = ai_response.replace("```json", "").replace("```", "").strip()
            elif ai_response.startswith("```"):
                ai_response = ai_response.replace("```", "").strip()
            
            # Parse JSON
            recommendation_data = json.loads(ai_response)
            
            # Validate the recommendation
            if not all(key in recommendation_data for key in ["team_member_id", "team_member_name", "confidence_score"]):
                raise ValueError("AI response missing required fields")
            
            # Create recommendation object
            recommendation = AssignmentRecommendation(**recommendation_data)
            
            logger.info(f"✅ Recommendation: {recommendation.team_member_name} (confidence: {recommendation.confidence_score:.2%})")
            
            return recommendation
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"Response was: {ai_response}")
            
            # Fallback: assign to member with lowest workload
            return self._fallback_assignment(team_members, task_description)
            
        except Exception as e:
            logger.error(f"Error in AI recommendation: {e}", exc_info=True)
            
            # Fallback: assign to member with lowest workload
            return self._fallback_assignment(team_members, task_description)
    
    def _fallback_assignment(
        self,
        team_members: List[TeamMember],
        task_description: str
    ) -> AssignmentRecommendation:
        """Fallback assignment strategy when AI fails"""
        
        logger.warning("Using fallback assignment strategy")
        
        # Find member with lowest workload percentage
        best_member = min(
            team_members,
            key=lambda m: m.current_workload / m.max_workload if m.max_workload > 0 else 1.0
        )
        
        return AssignmentRecommendation(
            team_member_id=best_member.id,
            team_member_name=best_member.name,
            team_member_email=best_member.email,
            confidence_score=0.50,  # Low confidence for fallback
            reasoning=f"Assigned to {best_member.name} based on lowest current workload. AI analysis failed, manual review recommended.",
            matched_skills=[]
        )


# Singleton instance
ai_service = AIService()