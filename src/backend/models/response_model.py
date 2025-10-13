# src/backend/models/response_model.py

from pydantic import BaseModel
from typing import List, Optional

class NewsItem(BaseModel):
    title: str
    link: str

class EnrichedLeadResponse(BaseModel):
    company_name: str
    logo: Optional[str]
    summary: Optional[str]
    colors: Optional[list]
    news: List[NewsItem] = []
