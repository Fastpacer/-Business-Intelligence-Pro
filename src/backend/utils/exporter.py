import os
import csv
from datetime import datetime
import json

def export_to_csv(leads: list[dict], folder: str = "src/backend/data/processed"):
    """
    Export enriched + AI-analyzed leads to a timestamped CSV file (readable format).
    """
    if not leads:
        print("[INFO] No leads to export.")
        return None

    os.makedirs(folder, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(folder, f"leads_export_{timestamp}.csv")

    # Collect unique keys
    all_keys = set()
    for lead in leads:
        all_keys.update(lead.keys())

    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(all_keys))
        writer.writeheader()
        for lead in leads:
            row = {}
            for key, value in lead.items():
                # Convert lists/dicts to clean strings
                if isinstance(value, (list, dict)):
                    row[key] = json.dumps(value, ensure_ascii=False)
                else:
                    row[key] = value
            writer.writerow(row)

    print(f"[EXPORT SUCCESS] Saved {len(leads)} leads → {file_path}")
    return file_path
