📊 Business Intelligence Pro
AI‑Powered Company Research & Strategic Insights

🚀 Project Overview
Business Intelligence Pro is an AI‑driven company intelligence platform that goes beyond simple lead scraping. It enriches company data with summaries, websites, industries, and fresh news, then generates concise, actionable insights using LLMs.

Instead of raw lists, users get a strategic business brief they can export and share — ideal for sales intelligence, due diligence, or investment research.

✨ Key Features
🔍 Company Enrichment: Auto‑discovers websites, summaries, industries, and recent news.

🤖 AI Insights: Generates structured analysis:

Strategic Positioning

Customer & GTM Signals

Growth Signals & Risks

🖥️ Clean NiceGUI Frontend: Simple input → enrichment → insights → export.

📑 Export Options: Download reports as PDF for easy sharing.

🔗 Multi‑API Orchestration: DuckDuckGo, NewsData, Brandfetch, Groq LLM, with Serper used only for strategic context.

🔑 APIs & Configuration
Create a .env file in the project root with your keys:

bash
GROQ_API_KEY=your_groq_key
NEWSDATA_API_KEY=your_newsdata_key
BRANDFETCH_API_KEY=your_brandfetch_key
SERPER_API_KEY=your_serper_key   # optional, used only for strategic context
Groq LLM → AI insights & industry inference

NewsData.io → Fresh company news

Brandfetch → Logos & branding (optional)

DuckDuckGo → Summaries & site discovery

Serper → Used sparingly for market/competitor context

⚡ How to Run Locally
Clone the repo

bash
git clone https://github.com/yourusername/business-intelligence-pro.git
cd business-intelligence-pro
Install dependencies

bash
pip install -r requirements.txt
Start backend (FastAPI)

bash
uvicorn src.backend.app:app --reload --port 8000
Swagger docs: http://127.0.0.1:8000/docs

Start frontend (NiceGUI)

bash
python src/backend/main_nicegui.py
UI available at: http://127.0.0.1:3000

🖥️ Demo Flow
Enter a company name (and optional website).

Backend enriches with summary, industry, news, branding.

AI generates strategic insights in structured sections.

Export the report as PDF.

🧩 Lessons & Debugging Notes
✅ Pivoted from React → NiceGUI for speed and simplicity.

✅ Fixed Pydantic validation issues (empty URLs).

✅ Reduced hallucinations by grounding LLM prompts only in available data.

✅ Serper repositioned as intentional market context, not a fallback crutch.

📈 Next Steps
Add caching (SQLite/JSON) to reduce API calls.

Add CRM integration (HubSpot/Salesforce).

Improve LLM prompts for sales‑specific or investment‑specific use cases.

Add multi‑company comparison mode.

📜 License
MIT License — free to use and adapt.

