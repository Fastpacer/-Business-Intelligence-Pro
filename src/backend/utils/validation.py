# src/backend/utils/validation.py

import re
from urllib.parse import urlparse

def is_valid_url(url: str) -> bool:
    """Basic URL validation."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def is_valid_company_name(name: str) -> bool:
    """Ensure company name isn't gibberish or too short."""
    if not name or len(name.strip()) < 2:
        return False
    return re.match(r"^[A-Za-z0-9 &.\-]+$", name.strip()) is not None
