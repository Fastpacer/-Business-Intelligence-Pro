# src/backend/utils/data_cleaner.py

def clean_enriched_data(leads: list[dict]) -> list[dict]:
    """
    Remove duplicates, empty entries, and normalize structure in enriched leads.
    """
    seen = set()
    cleaned = []

    for lead in leads:
        name = lead.get("company_name", "").strip().lower()
        if not name or name in seen:
            continue

        # Normalize keys and drop Nones
        lead = {k: v for k, v in lead.items() if v not in [None, "", [], {}]}
        lead["company_name"] = name.title()

        cleaned.append(lead)
        seen.add(name)

    return cleaned
