from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio


LOG_PATH = Path("data/logs.jsonl")


def load_records() -> list[dict]:
    if not LOG_PATH.exists():
        raise SystemExit("Không tìm thấy data/logs.jsonl. Hãy chạy load test trước.")
    return [
        json.loads(line)
        for line in LOG_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def show_correlation(records: list[dict]) -> None:
    record = next(
        (item for item in records if item.get("event") == "request_received"),
        None,
    )
    if record is None:
        raise SystemExit("Không tìm thấy event request_received.")

    print("=== CHECKPOINT 1: CORRELATION ID & LOG ENRICHMENT ===")
    for field in (
        "ts",
        "level",
        "service",
        "event",
        "correlation_id",
        "user_id_hash",
        "session_id",
        "feature",
        "model",
        "env",
    ):
        print(f"{field:16}: {record.get(field)}")


def show_pii(records: list[dict]) -> None:
    samples = []
    for record in records:
        payload = record.get("payload")
        preview = payload.get("message_preview", "") if isinstance(payload, dict) else ""
        if "REDACTED" in preview:
            samples.append((record.get("correlation_id"), preview))

    print("=== CHECKPOINT 1: PII REDACTION ===")
    if not samples:
        raise SystemExit("Không tìm thấy log đã redact. Hãy chạy load test trước.")
    for correlation_id, preview in samples:
        print(f"{correlation_id}: {preview}")


def main() -> None:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", choices=("correlation", "pii"))
    args = parser.parse_args()
    records = load_records()
    if args.evidence == "correlation":
        show_correlation(records)
    else:
        show_pii(records)


if __name__ == "__main__":
    main()
