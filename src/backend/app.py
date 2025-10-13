"""
LeadGen AI Tool Backend - FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="LeadGen AI Tool",
    description="AI-powered lead generation and enrichment backend.",
    version="1.0.0"
)

# CORS setup (allow frontend)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from src.backend.routers import scrape, enrich, ai_insights # 👈 works once __init__.py files exist


# Register routers
app.include_router(scrape.router, prefix="/api/scrape", tags=["Scraper"])
app.include_router(enrich.router, prefix="/api/enrich", tags=["Enrichment"])
app.include_router(ai_insights.router, prefix="/api/insights", tags=["AI Insights"])

# Health check route
@app.get("/", tags=["Health Check"])
def root():
    return {"message": "✅ LeadGen AI Tool API is up and running!"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
