from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from src.backend.utils.api_helpers import research_company_thoroughly

router = APIRouter()

class LeadModel(BaseModel):
    company_name: str
    company_url: Optional[str] = ""  # Change from HttpUrl to str with default ""

@router.post("/")
async def enrich_company(lead: LeadModel):
    """
    Enhanced enrichment that actually uses the provided website
    """
    try:
        # Use the new thorough research function
        research_data = research_company_thoroughly(
            company_name=lead.company_name,
            website=lead.company_url if lead.company_url else ""  # Handle empty string
        )
        
        return {
            "status": "success", 
            "data": [research_data],
            "sources_used": research_data.get("sources_used", [])
        }
        
    except Exception as e:
        print(f"[ERROR] Enrichment failed: {e}")
        return {"status": "error", "message": str(e)}


