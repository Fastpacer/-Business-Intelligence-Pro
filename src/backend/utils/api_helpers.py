# src/backend/utils/api_helpers.py
import os
import requests
import time
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

# Primary API keys (loaded from .env)
BRANDFETCH_API_KEY = os.getenv("BRANDFETCH_API_KEY")
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Common request config
DEFAULT_TIMEOUT = 10
RETRY_COUNT = 2
RETRY_BACKOFF = 0.5  # seconds

# -------------------------
# Utility helpers
# -------------------------
def is_valid_url(url: str) -> bool:
    if not url:
        return False
    try:
        p = urlparse(url)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False

def extract_domain(url: str) -> str:
    """Return domain from url-like input, else empty string."""
    if not url:
        return ""
    if not is_valid_url(url):
        if "/" not in url and "." in url:
            return url.strip()
        return ""
    parsed = urlparse(url)
    return parsed.netloc

def _safe_get(url, headers=None, params=None, timeout=DEFAULT_TIMEOUT):
    """Simple wrapper with retries and backoff."""
    for attempt in range(RETRY_COUNT):
        try:
            r = requests.get(url, headers=headers, params=params, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            if attempt < RETRY_COUNT - 1:
                time.sleep(RETRY_BACKOFF * (attempt + 1))
                continue
            print(f"[ERROR] GET {url} failed: {e}")
            return None

def _safe_post(url, headers=None, json=None, timeout=DEFAULT_TIMEOUT):
    for attempt in range(RETRY_COUNT):
        try:
            r = requests.post(url, headers=headers, json=json, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            if attempt < RETRY_COUNT - 1:
                time.sleep(RETRY_BACKOFF * (attempt + 1))
                continue
            print(f"[ERROR] POST {url} failed: {e}")
            return None

# -------------------------
# WEBSITE CONTENT EXTRACTION (Robust HTML parsing)
# -------------------------
def scrape_website_content(url: str):
    """
    Robust website content extraction using BeautifulSoup with html5lib
    """
    if not url or not is_valid_url(url):
        return ""
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        resp = _safe_get(url, headers=headers, timeout=10)
        if not resp:
            return ""
        
        # Use html5lib parser (pure Python, no compilation issues)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.content, 'html5lib')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()
        
        # Extract key information
        extracted_data = {}
        
        # Title
        title = soup.find('title')
        extracted_data['title'] = title.get_text().strip() if title else ""
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        extracted_data['description'] = meta_desc.get('content', '').strip() if meta_desc else ""
        
        # H1 headings
        h1s = [h1.get_text().strip() for h1 in soup.find_all('h1')[:2]]
        extracted_data['headings'] = h1s
        
        # First meaningful paragraph
        first_p = soup.find('p')
        extracted_data['first_paragraph'] = first_p.get_text().strip()[:300] if first_p else ""
        
        # Try to find main content
        main_content = ""
        content_selectors = ['main', 'article', '.content', '#content', '.main-content']
        for selector in content_selectors:
            main_elem = soup.select_one(selector)
            if main_elem:
                main_text = main_elem.get_text().strip()
                if len(main_text) > 50:  # Only use if substantial content
                    main_content = main_text[:500]
                    break
        
        # If no main content found, get body text
        if not main_content:
            body = soup.find('body')
            if body:
                main_content = body.get_text().strip()[:500]
        
        # Clean up the main content
        if main_content:
            main_content = ' '.join(main_content.split())  # Normalize whitespace
        
        # Build comprehensive summary
        summary_parts = []
        
        if extracted_data['title']:
            summary_parts.append(f"Title: {extracted_data['title']}")
        
        if extracted_data['description']:
            summary_parts.append(f"Description: {extracted_data['description']}")
        
        if extracted_data['headings']:
            summary_parts.append(f"Headings: {', '.join(extracted_data['headings'])}")
        
        if main_content:
            summary_parts.append(f"Content: {main_content}")
        elif extracted_data['first_paragraph']:
            summary_parts.append(f"Content: {extracted_data['first_paragraph']}")
        
        result = " | ".join([part for part in summary_parts if part])
        return result if result else "Website content extracted but limited text available"
        
    except Exception as e:
        print(f"[ERROR] Website scraping failed for {url}: {e}")
        return ""

# -------------------------
# SERPER: Strategic market research
# -------------------------
def _fetch_serper_organic(query: str, num: int = 3):
    """Internal Serper call for organic results only."""
    if not SERPER_API_KEY:
        return []
    
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "num": num}

    resp = _safe_post(url, headers=headers, json=payload, timeout=15)
    if not resp:
        return []

    try:
        data = resp.json()
        organic = data.get("organic") or data.get("results") or data.get("organic_results") or []
        context_data = []
        for item in organic:
            title = item.get("title") or item.get("label") or ""
            snippet = item.get("snippet") or item.get("description") or item.get("snippetText") or ""
            link = item.get("link") or item.get("url") or item.get("source") or ""
            if link and not link.startswith("http"):
                link = "https://" + link.lstrip("/")
            context_data.append({
                "title": title.strip(),
                "content": snippet.strip(),
                "source": link.strip()
            })
        return context_data
    except Exception as e:
        print(f"[ERROR] parsing Serper response: {e}")
        return []

def fetch_strategic_context(company_name: str, industry: str = ""):
    """
    Intentional market research using Serper for business intelligence.
    """
    # Add disambiguation terms for common word company names
    disambiguation_terms = " company tech startup business inc"
    
    strategic_queries = [
        f"{company_name}{disambiguation_terms} competitors market position",
        f"{company_name}{disambiguation_terms} growth funding {industry}",
        f'"{company_name}" company business model'
    ]
    
    all_context = []
    for query in strategic_queries[:2]:
        results = _fetch_serper_organic(query, num=2)
        all_context.extend(results)
    
    return all_context

# COMPATIBILITY: Keep for existing endpoints
def fetch_serper_results(query: str, num: int = 5):
    """
    Compatibility function for existing scrape endpoint.
    """
    return _fetch_serper_organic(query, num)

# -------------------------
# BRANDFETCH: logo + canonical name
# -------------------------
def fetch_brandfetch_data(domain: str):
    """
    Return dict: {logo, name}
    """
    if not domain:
        return {}

    if not BRANDFETCH_API_KEY:
        print("[WARN] No BRANDFETCH_API_KEY configured.")
        return {}

    url = f"https://api.brandfetch.io/v2/brands/{domain}"
    headers = {"Authorization": f"Bearer {BRANDFETCH_API_KEY}"}

    resp = _safe_get(url, headers=headers, timeout=8)
    if not resp:
        return {}

    try:
        data = resp.json()
        logos = data.get("logos") or []
        logo_url = ""
        if logos and isinstance(logos, list):
            logo_url = logos[0].get("url") or logos[0].get("src") or ""
        name = data.get("name") or domain
        return {"logo": logo_url or "", "name": name}
    except Exception as e:
        print(f"[ERROR] parse Brandfetch response: {e}")
        return {}

def fetch_brandfetch_data_enhanced(domain: str):
    """
    Enhanced Brandfetch that actually uses the domain properly
    """
    if not domain:
        return {}
    
    clean_domain = domain.replace('www.', '').split('/')[0]
    brand_data = fetch_brandfetch_data(clean_domain)
    
    # If Brandfetch fails, try alternative domains
    if not brand_data.get('name') and '.' in clean_domain:
        variations = [
            clean_domain,
            f"www.{clean_domain}",
            clean_domain.replace('.com', '.co'),
            clean_domain.replace('.io', '.com')
        ]
        
        for variation in variations:
            if variation != clean_domain:
                alt_data = fetch_brandfetch_data(variation)
                if alt_data.get('name'):
                    brand_data = alt_data
                    break
    
    return brand_data

# -------------------------
# DUCKDUCKGO - primary summary (WITH DISAMBIGUATION)
# -------------------------
def fetch_duckduckgo_summary(company: str):
    """
    Returns a short summary string, or empty string if none found.
    Uses disambiguation for common word company names.
    """
    try:
        # Add disambiguation for common word companies
        common_words = ['stochastic', 'quantum', 'vector', 'matrix', 'alpha', 'beta', 'gamma', 
                       'delta', 'sigma', 'lambda', 'omega', 'zen', 'nova', 'pulse', 'flux']
        
        query = f"{company}"
        if company.lower() in common_words:
            query = f"{company} company tech startup business"
        
        url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json", "no_redirect": 1, "no_html": 1}
        resp = _safe_get(url, params=params, timeout=8)
        if not resp:
            return ""
        data = resp.json()
        summary = data.get("AbstractText") or data.get("Heading") or ""
        
        # Filter out conceptual definitions - look for company/business indicators
        if summary:
            company_indicators = ['company', 'startup', 'tech', 'business', 'inc', 'corp', 'ltd', 'founder', 'CEO', 'venture']
            is_conceptual = any(indicator in summary.lower() for indicator in company_indicators)
            
            if not is_conceptual and len(summary.split()) > 20:
                # This might be a conceptual definition, not a company
                summary = ""
        
        if not summary:
            related = data.get("RelatedTopics", [])
            if related and isinstance(related, list):
                for r in related:
                    if isinstance(r, dict):
                        t = r.get("Text") or r.get("Result") or ""
                        if t:
                            # Check if this looks like company information
                            if any(indicator in t.lower() for indicator in company_indicators):
                                summary = t
                                break
        return summary or ""
    except Exception as e:
        print(f"[ERROR] DuckDuckGo summary failed: {e}")
        return ""

# -------------------------
# NEWSDATA - primary news source (WITH DISAMBIGUATION)
# -------------------------
def fetch_news_articles(company_name: str, limit: int = 3):
    """
    Returns list of {"title", "link"}.
    Uses disambiguation for common word company names.
    """
    if not NEWSDATA_API_KEY:
        print("[WARN] NEWSDATA_API_KEY not set.")
        return []

    try:
        # Add disambiguation for common words
        common_words = ['stochastic', 'quantum', 'vector', 'matrix', 'alpha', 'beta']
        query = company_name
        if company_name.lower() in common_words:
            query = f'"{company_name}" company OR "{company_name}" startup OR "{company_name}" tech'
        
        url = "https://newsdata.io/api/1/news"
        params = {"apikey": NEWSDATA_API_KEY, "q": query, "language": "en"}
        resp = _safe_get(url, params=params, timeout=8)
        if not resp:
            return []
        data = resp.json()
        results = data.get("results") or data.get("articles") or []
        out = []
        for a in results[:limit]:
            title = a.get("title") or a.get("headline") or ""
            link = a.get("link") or a.get("url") or ""
            if title:
                out.append({"title": title, "link": link})
        return out
    except Exception as e:
        print(f"[ERROR] NewsData fetch failed: {e}")
        return []

def fetch_news_articles_enhanced(company_name: str, domain: str = "", limit: int = 5):
    """
    News search that uses both company name AND domain
    """
    articles = []
    
    if company_name:
        name_articles = fetch_news_articles(company_name, limit)
        articles.extend(name_articles)
    
    if domain and domain not in company_name:
        clean_domain = domain.replace('www.', '').replace('https://', '').replace('http://', '').split('/')[0]
        domain_articles = fetch_news_articles(clean_domain, limit)
        articles.extend(domain_articles)
    
    seen_titles = set()
    unique_articles = []
    
    for article in articles:
        title = article.get('title', '').lower().strip()
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_articles.append(article)
    
    return unique_articles[:limit]

# -------------------------
# OFFICIAL WEBSITE HELPER 
# -------------------------
def find_official_website(company_name: str):
    """
    Try to discover an official website for the company.
    """
    try:
        # Use disambiguation for common words
        common_words = ['stochastic', 'quantum', 'vector', 'matrix', 'alpha', 'beta']
        query = f"{company_name} official website"
        if company_name.lower() in common_words:
            query = f"{company_name} company official website tech startup"
        
        ddg_url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json", "no_html": 1}
        resp = _safe_get(ddg_url, params=params, timeout=6)
        if resp:
            data = resp.json()
            related = data.get("RelatedTopics", [])
            if related and isinstance(related, list):
                first = related[0]
                if isinstance(first, dict) and first.get("FirstURL"):
                    return first.get("FirstURL")

            abs_url = data.get("AbstractURL") or ""
            if abs_url:
                return abs_url
    except Exception as e:
        print(f"[WARN] find_official_website ddg part failed: {e}")

    if "." in company_name and len(company_name.split(".")) >= 2:
        candidate = company_name.strip()
        if is_valid_url(candidate):
            return candidate
        if not candidate.startswith("http"):
            candidate = "https://" + candidate
        if is_valid_url(candidate):
            return candidate

    try:
        strategic_data = fetch_strategic_context(company_name, "")
        if strategic_data:
            for item in strategic_data:
                source = item.get("source", "")
                if company_name.lower() in source.lower() or any(domain in source for domain in ['.com', '.io', '.co', '.ai']):
                    return source
    except Exception as e:
        print(f"[WARN] find_official_website strategic fallback failed: {e}")

    return ""

# -------------------------
# GROQ LLM - industry inference & insight generation
# -------------------------
def _call_groq_chat(payload):
    if not GROQ_API_KEY:
        print("[ERROR] GROQ_API_KEY not set.")
        return None
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    resp = _safe_post(url, headers=headers, json=payload, timeout=20)
    if not resp:
        return None
    try:
        return resp.json()
    except Exception as e:
        print(f"[ERROR] parse Groq response: {e}")
        return None

def infer_industry(company_name: str, summary: str):
    """
    Short, low-cost industry inference using Groq.
    """
    prompt = f"Classify the industry for the company named '{company_name}'. Summary: {summary or 'No summary available.'}\nReturn a short phrase like 'FinTech', 'AI Consulting', 'Healthcare SaaS'."
    payload = {
        "model": "moonshotai/kimi-k2-instruct-0905",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 30,
        "temperature": 0.0
    }
    resp = _call_groq_chat(payload)
    if not resp:
        return "Unknown"
    try:
        return resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[ERROR] infer_industry parse: {e}")
        return "Unknown"

# -------------------------
# COMPREHENSIVE COMPANY RESEARCH (MAIN FUNCTION)
# -------------------------
def research_company_thoroughly(company_name: str, website: str = ""):
    """
    MAIN FUNCTION: Properly research company using ALL available inputs
    """
    results = {
        "company_name": company_name,
        "website": website,
        "canonical_name": company_name,
        "summary": "",
        "news": [],
        "logo": "",
        "industry": "",
        "sources_used": []
    }
    
    # If no website provided, try to find it
    if not website:
        website = find_official_website(company_name)
        results["website"] = website
    
    domain = extract_domain(website) if website else ""
    
    # SOURCE 1: BRANDFETCH (if we have domain)
    if domain:
        brand_data = fetch_brandfetch_data_enhanced(domain)
        if brand_data:
            results["logo"] = brand_data.get("logo", "")
            results["canonical_name"] = brand_data.get("name", company_name)
            results["sources_used"].append("Brandfetch")
    
    # SOURCE 2: DIRECT WEBSITE SCRAPING (for niche companies)
    website_content = ""
    if website:
        website_content = scrape_website_content(website)
        if website_content:
            results["sources_used"].append("Website Content")
    
    # SOURCE 3: DUCKDUCKGO (with proper company name)
    ddg_summary = fetch_duckduckgo_summary(results["canonical_name"])
    if ddg_summary:
        results["summary"] = ddg_summary
        results["sources_used"].append("DuckDuckGo")
    elif website_content:
        results["summary"] = website_content
        results["sources_used"].append("Website Summary")
    
    # SOURCE 4: NEWS (using both name and domain)
    news_articles = fetch_news_articles_enhanced(results["canonical_name"], domain, 5)
    if news_articles:
        results["news"] = news_articles
        results["sources_used"].append("NewsData")
    
    # SOURCE 5: INDUSTRY INFERENCE
    if results["summary"]:
        results["industry"] = infer_industry(results["canonical_name"], results["summary"])
        results["sources_used"].append("AI Industry Classification")
    
    return results

def generate_ai_insight(enriched_lead: dict, include_strategic_context: bool = False):
    """
    Enhanced AI insights that actually use the properly researched data
    """
    company = enriched_lead.get("company_name", "")
    canonical_name = enriched_lead.get("canonical_name", company)
    summary = enriched_lead.get("summary", "") 
    industry = enriched_lead.get("industry", "")
    website = enriched_lead.get("website", "")
    news = enriched_lead.get("news", [])
    sources = enriched_lead.get("sources_used", [])
    
    # Build RICH context from actual research
    context_parts = []
    
    if summary:
        context_parts.append(f"## Company Overview\n{summary}")
    
    if website:
        context_parts.append(f"## Website\n{website}")
    
    if news:
        news_text = "\n".join([f"- **{n.get('title', '')}** - {n.get('link', '')}" for n in news[:3]])
        context_parts.append(f"## Recent News & Mentions\n{news_text}")
    
    if industry and industry != "Unknown":
        context_parts.append(f"## Industry\n{industry}")
    
    if sources:
        context_parts.append(f"## Research Sources\n{', '.join(sources)}")
    
    # Add strategic context if requested
    strategic_data = []
    if include_strategic_context:
        strategic_data = fetch_strategic_context(canonical_name, industry)
        if strategic_data:
            strategic_text = "\n".join([f"- {item.get('title', '')}: {item.get('content', '')}" for item in strategic_data[:2]])
            context_parts.append(f"## Market Context\n{strategic_text}")
    
    context = "\n\n".join(context_parts) if context_parts else "No detailed public information found through automated research."

    prompt = f"""
You are a business intelligence analyst. Create a detailed company assessment for **{canonical_name}**.

**AVAILABLE RESEARCH DATA:**
{context}

**REQUIRED ANALYSIS:**
Provide substantive insights in these THREE sections:

1) **Business Model & Market Position**
   - Analyze their likely business model based on available data
   - Assess their market positioning and potential differentiation
   - Identify their target customer base

2) **Growth Signals & Market Presence**  
   - Evaluate any growth indicators from news or online presence
   - Assess their market traction and visibility
   - Identify potential partnership or expansion opportunities

3) **Strategic Assessment & Recommendations**
   - Provide actionable business intelligence
   - Suggest potential engagement strategies
   - Identify areas for further due diligence

**CRITICAL INSTRUCTIONS:**
- Base ALL analysis strictly on the provided research data
- If data is limited, focus on what CAN be inferred from available information
- Provide concrete, actionable business intelligence
- Never state "not enough data" - instead provide industry-level insights
- **IMPORTANT: You MUST complete all 3 sections. Do not cut off mid-sentence.**

**FORMAT REQUIREMENTS:**
- Use clear section headings with numbers (1, 2, 3)
- Keep each section concise but comprehensive
- Use bullet points for clarity
- Ensure the analysis flows logically between sections
"""

    payload = {
        "model": "moonshotai/kimi-k2-instruct-0905",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1200,  # Increased from 600 to 1200
        "temperature": 0.3
    }

    resp = _call_groq_chat(payload)
    if not resp:
        return "Analysis generation failed. Please check the company website and try again."
    
    try:
        content = resp["choices"][0]["message"]["content"].strip()
        
        # Check if the response was likely truncated
        if content and not content.endswith(('.', '!', '?')) and len(content.split()) > 300:
            # Response was probably truncated, try a shorter version
            return "Analysis was truncated. Please try again with the 'Strategic Research' option disabled, or provide a company website for more focused analysis."
        
        return content
    except Exception as e:
        print(f"[ERROR] AI insight generation failed: {e}")
        return "Analysis generation failed due to technical error."