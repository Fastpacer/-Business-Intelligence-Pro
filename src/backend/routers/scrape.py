from fastapi import APIRouter, Query
from src.backend.utils.api_helpers import fetch_strategic_context

router = APIRouter()

@router.get("/")
async def scrape_leads(query: str = Query(..., description="Search phrase for business research")):
    """
    Strategic business research using Serper.dev API.
    Example: /api/scrape?query=ai+startups+in+india
    """
    try:
        # Use the new strategic context function
        research_data = fetch_strategic_context(query)
        print(f"[DEBUG] {len(research_data)} research items fetched for query '{query}'")

        if not research_data:
            return {"status": "error", "message": "No research data found or API error."}
        
        # Transform to match expected format
        formatted_data = [
            {
                "company_name": item.get("title", ""),
                "summary": item.get("content", ""),
                "company_url": item.get("source", "")
            }
            for item in research_data
        ]
        
        return {"status": "success", "count": len(formatted_data), "data": formatted_data}

    except Exception as e:
        print(f"[ERROR] Research scraping failed: {e}")
        return {"status": "error", "message": str(e)}
