import os
import json
from datetime import datetime
from src.config import LOG_DIR


def log_query(query: str, answer: str, sources: list[dict], best_distance: float) -> None:
    """Append a query/response record to a daily JSON log file."""
    os.makedirs(LOG_DIR, exist_ok=True)

    log_file = os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y-%m-%d')}.json")

    record = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "answer": answer,
        "best_distance": best_distance,
        "sources": sources,
    }

    records = []
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            try:
                records = json.load(f)
            except json.JSONDecodeError:
                records = []

    records.append(record)

    with open(log_file, "w") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)