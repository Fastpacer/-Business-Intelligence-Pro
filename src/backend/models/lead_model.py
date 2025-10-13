# src/backend/models/lead_model.py

from pydantic import BaseModel, HttpUrl, Field

class Lead(BaseModel):
    company_name: str = Field(..., example="OpenAI")
    company_url: HttpUrl | None = Field(None, example="https://openai.com")
