from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio

EVIDENCE_PATH = REPO_ROOT / "submission/evidence/checkpoint-3-investigation.json"
REQUIRED_SCREENSHOTS = (
    "checkpoint-3-investigation.png",
    "checkpoint-3-root-cause-log.png",
    "checkpoint-3-trace-slow-retrieval.png",
    "checkpoint-3-dashboard-incident.png",
)


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> None:
    configure_utf8_stdio()
    if not EVIDENCE_PATH.exists():
        fail("Chưa có evidence CP3; chạy scripts/run_checkpoint3_challenge.py trước.")
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    phases = evidence.get("phases", {})
    required_phases = {"baseline", "incident", "recovery"}
    if set(phases) != required_phases:
        fail("Evidence phải có đủ baseline, incident và recovery.")
    if evidence.get("challenge_id") != "day13-k4-observability-v1":
        fail("Sai challenge ID chính thức của K4.")
    if evidence.get("student", {}).get("student_id") != "2A202602020":
        fail("Sai MSSV người phụ trách Checkpoint 3.")
    if any(phases[name].get("request_count") != 5 for name in required_phases):
        fail("Mỗi pha phải chạy đủ 5 input chính thức.")
    if not evidence.get("threshold_breached"):
        fail("P95 incident chưa vượt ngưỡng challenge.")
    if not evidence.get("recovery_confirmed"):
        fail("P95 recovery chưa trở lại dưới ngưỡng.")
    log = evidence.get("root_cause_log_sample") or {}
    if log.get("event") != "retrieval_completed" or log.get("service") != "retrieval":
        fail("Log chưa khoanh vùng đúng retrieval.")
    if log.get("correlation_id") != evidence.get("representative_correlation_id"):
        fail("Correlation ID giữa kết luận và log không khớp.")
    if log.get("payload", {}).get("incident") != "rag_slow":
        fail("Log chưa chứng minh incident rag_slow.")
    if log.get("latency_ms", 0) < 2000:
        fail("Retrieval log chưa chứng minh latency bất thường.")
    if not evidence.get("representative_trace_id"):
        fail("Evidence chưa gắn trace ID thật từ Langfuse.")
    if any(evidence.get("final_incident_state", {}).values()):
        fail("Vẫn còn incident bật sau khi chạy challenge.")
    evidence_dir = EVIDENCE_PATH.parent
    missing_screenshots = [
        name
        for name in REQUIRED_SCREENSHOTS
        if not (evidence_dir / name).is_file() or (evidence_dir / name).stat().st_size == 0
    ]
    if missing_screenshots:
        fail(f"Thiếu ảnh evidence: {', '.join(missing_screenshots)}")

    print("HỢP LỆ: Checkpoint 3 có đủ Metrics -> Traces -> Logs -> Root cause -> Recovery.")
    print("Evidence ảnh: 4/4")
    print(f"Challenge: {evidence['challenge_id']}")
    print(f"Baseline P95: {phases['baseline']['latency_p95_ms']} ms")
    print(f"Incident P95: {phases['incident']['latency_p95_ms']} ms")
    print(f"Recovery P95: {phases['recovery']['latency_p95_ms']} ms")
    print(f"Correlation ID: {evidence['representative_correlation_id']}")
    print(f"Trace ID: {evidence['representative_trace_id']}")
    print(f"Retrieval latency: {log['latency_ms']} ms")


if __name__ == "__main__":
    main()
