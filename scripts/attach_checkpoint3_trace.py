from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from langfuse import get_client

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio

EVIDENCE_PATH = REPO_ROOT / "submission/evidence/checkpoint-3-investigation.json"
EVIDENCE_TEXT_PATH = REPO_ROOT / "submission/evidence/checkpoint-3-investigation.txt"


def main() -> None:
    configure_utf8_stdio()
    load_dotenv()
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    correlation_id = evidence["representative_correlation_id"]
    session_id = evidence["root_cause_log_sample"]["session_id"]
    client = get_client()

    matched_trace = None
    for _ in range(10):
        traces = client.api.trace.list(session_id=session_id, limit=50, order_by="timestamp.desc")
        matched_trace = next(
            (
                trace
                for trace in traces.data
                if (trace.metadata or {}).get("correlation_id") == correlation_id
            ),
            None,
        )
        if matched_trace is not None:
            break
        time.sleep(3)
    if matched_trace is None:
        raise RuntimeError(f"Chưa tìm thấy trace cho correlation ID {correlation_id}.")

    evidence["representative_trace_id"] = matched_trace.id
    evidence["representative_trace_latency_seconds"] = matched_trace.latency
    EVIDENCE_PATH.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    text_evidence = EVIDENCE_TEXT_PATH.read_text(encoding="utf-8")
    trace_line = f"Trace ID tiêu biểu: {matched_trace.id}\n"
    if "Trace ID tiêu biểu:" not in text_evidence:
        EVIDENCE_TEXT_PATH.write_text(text_evidence + trace_line, encoding="utf-8")
    print(f"Trace ID       : {matched_trace.id}")
    print(f"Correlation ID : {correlation_id}")
    print(f"Session ID     : {session_id}")
    print(f"Trace latency  : {matched_trace.latency} giây")


if __name__ == "__main__":
    main()
