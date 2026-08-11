from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio

EVIDENCE_PATH = REPO_ROOT / "submission/evidence/checkpoint-3-investigation.json"


def main() -> None:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("view", choices=("metrics", "log"))
    args = parser.parse_args()
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))

    if args.view == "metrics":
        phases = evidence["phases"]
        print("=== CHECKPOINT 3: METRICS BEFORE / INCIDENT / AFTER ===")
        print(f"Challenge ID       : {evidence['challenge_id']}")
        print(f"Sinh viên          : Dương Tiến Dũng - 2A202602020")
        print(f"Ngưỡng latency     : {evidence['latency_threshold_ms']} ms")
        print(f"Baseline P95       : {phases['baseline']['latency_p95_ms']} ms")
        print(f"Incident P95       : {phases['incident']['latency_p95_ms']} ms")
        print(f"Recovery P95       : {phases['recovery']['latency_p95_ms']} ms")
        print(f"Vi phạm ngưỡng     : {evidence['threshold_breached']}")
        print(f"Recovery thành công: {evidence['recovery_confirmed']}")
        print(f"Trace ID           : {evidence.get('representative_trace_id', 'chưa gắn')}")
    else:
        log = evidence["root_cause_log_sample"]
        print("=== CHECKPOINT 3: ROOT CAUSE LOG ===")
        for field in ("ts", "level", "service", "event", "correlation_id", "session_id", "feature", "latency_ms"):
            print(f"{field:16}: {log.get(field)}")
        print(f"incident        : {log['payload']['incident']}")
        print(f"incident_active : {log['payload']['incident_active']}")
        print(f"trace_id        : {evidence.get('representative_trace_id', 'chưa gắn')}")
        print("Kết luận        : rag_slow làm span retrieve chậm khoảng 2.5 giây")


if __name__ == "__main__":
    main()
