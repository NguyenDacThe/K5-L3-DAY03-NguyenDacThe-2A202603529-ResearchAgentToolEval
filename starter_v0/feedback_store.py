"""Persist reproducible manual feedback separately from automated evals."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

FEEDBACK_DIR = Path(__file__).resolve().parent / "feedback"


def save_feedback(version: dict, steps: str, expected: str, actual: str) -> Path:
    if not all(value.strip() for value in [steps, expected, actual]):
        raise ValueError("Cần điền cách tái hiện, kết quả mong đợi và kết quả thực tế.")
    record = {"id": uuid4().hex, "source": "manual_feedback", "status": "open",
              "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              **{key: version[key] for key in ["version", "prompt_hash", "tools_hash"]},
              "steps": steps.strip(), "expected": expected.strip(), "actual": actual.strip()}
    text = json.dumps(record, ensure_ascii=False, indent=2)
    for key, value in os.environ.items():
        if value and len(value) > 8 and any(part in key for part in ["API_KEY", "TOKEN", "SECRET"]):
            text = text.replace(value, "[hidden]")
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    path = FEEDBACK_DIR / f"{record['id']}.json"
    path.write_text(text, encoding="utf-8")
    return path


def read_feedback(version: str) -> list[dict]:
    records = []
    for path in sorted(FEEDBACK_DIR.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            if record.get("version") == version:
                records.append(record)
        except (ValueError, OSError):
            continue
    return records
