"""LangGraph service for AI-powered task assignment"""
import json
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from sqlalchemy.orm import Session
from app.models.team_member import TeamMember
from app.config import get_settings
from app.services.rag_service import rag_service
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class AssignmentState(TypedDict):
    """State for the assignment workflow"""
    task_description: str
    team_members: List[dict]
    rag_context: str
    task_requirements: dict
    member_scores: List[dict]
    final_assignment: dict
    confidence_score: float
    reasoning: str


class LangGraphAssignmentService:
    """Service for AI-powered task assignment using LangGraph"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0,
            openai_api_key=settings.openai_api_key
        )
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow for task assignment"""
        workflow = StateGraph(AssignmentState)
        
        # Add nodes
        workflow.add_node("fetch_context", self._fetch_rag_context)
        workflow.add_node("extract_requirements", self._extract_requirements)
        workflow.add_node("score_members", self._score_members)
        workflow.add_node("select_best_match", self._select_best_match)
        
        # Define edges
        workflow.set_entry_point("fetch_context")
        workflow.add_edge("fetch_context", "extract_requirements")
        workflow.add_edge("extract_requirements", "score_members")
        workflow.add_edge("score_members", "select_best_match")
        workflow.add_edge("select_best_match", END)
        
        return workflow.compile()
    
    def _fetch_rag_context(self, state: AssignmentState) -> AssignmentState:
        """Fetch relevant context from RAG"""
        try:
            context = rag_service.get_relevant_context(state["task_description"])
            state["rag_context"] = context
        except Exception as e:
            logger.error(f"Error fetching RAG context: {e}")
            state["rag_context"] = ""
        return state
    
    def _extract_requirements(self, state: AssignmentState) -> AssignmentState:
        """Extract skills and requirements from task"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Extract technical requirements from this task.

Context from team documentation:
{context}

Return JSON with:
- required_skills: array of required technical skills
- preferred_skills: array of nice-to-have skills  
- complexity: "low", "medium", or "high"
- estimated_hours: number

Example:
{{
    "required_skills": ["Python", "FastAPI"],
    "preferred_skills": ["Docker"],
    "complexity": "medium",
    "estimated_hours": 8
}}"""),
            ("user", "{task_description}")
        ])
        
        try:
            chain = prompt | self.llm
            response = chain.invoke({
                "context": state["rag_context"],
                "task_description": state["task_description"]
            })
            
            # Parse JSON from response
            content = response.content
            # Try to extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            requirements = json.loads(content)
            state["task_requirements"] = requirements
        except Exception as e:
            logger.error(f"Error extracting requirements: {e}")
            # Fallback
            state["task_requirements"] = {
                "required_skills": [],
                "preferred_skills": [],
                "complexity": "medium",
                "estimated_hours": 4
            }
        
        return state
    
    def _score_members(self, state: AssignmentState) -> AssignmentState:
        """Score each team member for the task"""
        requirements = state["task_requirements"]
        required_skills = set(skill.lower() for skill in requirements.get("required_skills", []))
        preferred_skills = set(skill.lower() for skill in requirements.get("preferred_skills", []))
        
        member_scores = []
        
        for member in state["team_members"]:
            member_skills = set(skill.lower() for skill in member["skills"])
            
            # Calculate skill match
            required_match = len(required_skills & member_skills) / max(len(required_skills), 1) if required_skills else 0.5
            preferred_match = len(preferred_skills & member_skills) / max(len(preferred_skills), 1) if preferred_skills else 0.5
            
            # Calculate workload score (lower is better)
            workload_ratio = member["current_workload"] / max(member["max_workload"], 1)
            workload_score = 1 - workload_ratio
            
            # Combined score
            skill_score = (required_match * 0.7) + (preferred_match * 0.3)
            final_score = (skill_score * 0.7) + (workload_score * 0.3)
            
            # Find matched skills
            matched_required = list(required_skills & member_skills)
            matched_preferred = list(preferred_skills & member_skills)
            matched_skills = matched_required + matched_preferred
            
            member_scores.append({
                "team_member_id": member["id"],
                "team_member_name": member["name"],
                "team_member_email": member["email"],
                "score": final_score,
                "required_match": required_match,
                "preferred_match": preferred_match,
                "workload_score": workload_score,
                "matched_skills": matched_skills
            })
        
        # Sort by score (highest first)
        member_scores.sort(key=lambda x: x["score"], reverse=True)
        state["member_scores"] = member_scores
        
        return state
    
    def _select_best_match(self, state: AssignmentState) -> AssignmentState:
        """Select best match and generate reasoning"""
        if not state["member_scores"]:
            state["confidence_score"] = 0.0
            state["final_assignment"] = {}
            state["reasoning"] = "No team members available"
            return state
        
        best_match = state["member_scores"][0]
        
        # Use LLM to generate human-readable reasoning
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Generate a brief explanation for why this team member is the best match for the task.

Task: {task_description}
Team Member: {member_name}
Role: {member_role}
Matched Skills: {matched_skills}
Score: {score:.1%}

Provide 1-2 sentences explaining the match."""),
            ("user", "Generate reasoning")
        ])
        
        # Get member details
        member_id = best_match["team_member_id"]
        member_full = next((m for m in state["team_members"] if m["id"] == member_id), None)
        
        try:
            chain = prompt | self.llm
            reasoning_response = chain.invoke({
                "task_description": state["task_description"],
                "member_name": best_match["team_member_name"],
                "member_role": member_full["role"] if member_full else "Team Member",
                "matched_skills": ", ".join(best_match["matched_skills"]) if best_match["matched_skills"] else "general skills",
                "score": best_match["score"]
            })
            reasoning = reasoning_response.content
        except Exception as e:
            logger.error(f"Error generating reasoning: {e}")
            reasoning = f"Best skill match with {len(best_match['matched_skills'])} matching skills"
        
        state["final_assignment"] = {
            "id": best_match["team_member_id"],
            "name": best_match["team_member_name"],
            "email": best_match["team_member_email"],
            "matched_skills": best_match["matched_skills"]
        }
        state["confidence_score"] = best_match["score"]
        state["reasoning"] = reasoning
        
        return state
    
    async def assign_task(self, task_description: str, db: Session) -> Dict[str, Any]:
        """Main method to assign task using LangGraph"""
        try:
            # Fetch active team members with capacity
            team_members = db.query(TeamMember).filter(
                TeamMember.current_workload < TeamMember.max_workload
            ).all()
            
            if not team_members:
                return {
                    "confidence_score": 0.0,
                    "final_assignment": {},
                    "reasoning": "No team members available with capacity",
                    "all_recommendations": []
                }
            
            team_members_dict = [
                {
                    "id": tm.id,
                    "name": tm.name,
                    "email": tm.email,
                    "role": tm.role,
                    "skills": tm.skills,
                    "current_workload": tm.current_workload,
                    "max_workload": tm.max_workload
                }
                for tm in team_members
            ]
            
            # Initial state
            initial_state: AssignmentState = {
                "task_description": task_description,
                "team_members": team_members_dict,
                "rag_context": "",
                "task_requirements": {},
                "member_scores": [],
                "final_assignment": {},
                "confidence_score": 0.0,
                "reasoning": ""
            }
            
            # Run workflow
            result = self.workflow.invoke(initial_state)
            
            return {
                "confidence_score": result["confidence_score"],
                "final_assignment": result["final_assignment"],
                "reasoning": result["reasoning"],
                "all_recommendations": result["member_scores"][:3]  # Top 3
            }
        
        except Exception as e:
            logger.error(f"Error in assign_task: {e}")
            return {
                "confidence_score": 0.0,
                "final_assignment": {},
                "reasoning": f"Error during assignment: {str(e)}",
                "all_recommendations": []
            }


# Singleton instance
langgraph_service = LangGraphAssignmentService()
