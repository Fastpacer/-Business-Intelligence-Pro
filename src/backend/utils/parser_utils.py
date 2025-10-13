# src/backend/utils/parser_utils.py

import re
from urllib.parse import urlparse

def extract_domain(url: str) -> str:
    """Extract clean domain name from URL."""
    if not url:
        return ""
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    domain = domain.replace("www.", "").strip().lower()
    return domain

def normalize_company_name(name: str) -> str:
    """Standardize company names (trim, capitalize, remove suffix noise)."""
    if not name:
        return ""
    name = name.strip()
    name = re.sub(r"\s+(inc\.?|ltd\.?|corp\.?|co\.?)$", "", name, flags=re.I)
    return name.title()
