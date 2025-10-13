from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Any
from src.backend.utils.api_helpers import generate_ai_insight

router = APIRouter()

class EnrichedLead(BaseModel):
    company_name: str
    canonical_name: Optional[str] = None
    summary: Optional[str] = None
    news: Optional[List[Any]] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    sources_used: Optional[List[str]] = None
    include_strategic_research: Optional[bool] = False

@router.post("/", summary="Generate strategic business insights")
def generate_insight(lead: EnrichedLead):
    """
    Generate AI-based strategic insights for business assessment.
    """
    try:
        insight_text = generate_ai_insight(
            lead.dict(), 
            include_strategic_context=lead.include_strategic_research or False
        )
        lead_record = {
            "company_name": lead.canonical_name or lead.company_name,
            "summary": lead.summary or "",
            "industry": lead.industry or "Unknown",
            "website": lead.website or "",
            "news": [n.get("title", "") for n in lead.news] if lead.news else [],
            "strategic_insight": insight_text,
            "sources_used": lead.sources_used or [],
            "research_depth": "Strategic Context Included" if lead.include_strategic_research else "Standard Analysis"
        }
        return JSONResponse(content={
            "status": "success", 
            "analysis_type": "Business Assessment",
            "insights": [lead_record]
        })
    except Exception as e:
        print(f"[ERROR] Strategic insights generation failed: {e}")
        return JSONResponse(
            content={"status": "error", "message": str(e)}, 
            status_code=500
        )