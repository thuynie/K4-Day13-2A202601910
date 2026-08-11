from __future__ import annotations

import concurrent.futures
import json
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.challenge import ChallengeConfig, load_challenge, ordered_queries
from app.cli import configure_utf8_stdio

BASE_URL = "http://127.0.0.1:8000"
EVIDENCE_JSON = REPO_ROOT / "submission/evidence/checkpoint-3-investigation.json"
EVIDENCE_TEXT = REPO_ROOT / "submission/evidence/checkpoint-3-investigation.txt"


@dataclass(frozen=True)
class RequestResult:
    correlation_id: str
    session_id: str
    status_code: int
    latency_ms: float


def percentile(values: list[float], percentile_value: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round(percentile_value / 100 * len(ordered) + 0.5) - 1))
    return round(ordered[index], 1)


def run_batch(
    client: httpx.Client,
    challenge: ChallengeConfig,
    phase: str,
    run_token: str,
) -> list[RequestResult]:
    phase_prefix = {"baseline": "b", "incident": "c", "recovery": "f"}[phase]

    def send(index_and_payload: tuple[int, dict[str, str]]) -> RequestResult:
        index, payload = index_and_payload
        correlation_id = f"req-{phase_prefix}{run_token}{index:02x}"
        started = time.perf_counter()
        response = client.post(
            f"{BASE_URL}/chat",
            json=payload,
            headers={"x-request-id": correlation_id},
        )
        latency_ms = (time.perf_counter() - started) * 1000
        response.raise_for_status()
        actual_correlation_id = response.headers.get("x-request-id", response.json()["correlation_id"])
        return RequestResult(actual_correlation_id, payload["session_id"], response.status_code, round(latency_ms, 1))

    indexed = list(enumerate(ordered_queries(challenge), start=1))
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        return list(executor.map(send, indexed))


def summarize_phase(results: list[RequestResult]) -> dict[str, Any]:
    latencies = [item.latency_ms for item in results]
    return {
        "request_count": len(results),
        "latency_p50_ms": percentile(latencies, 50),
        "latency_p95_ms": percentile(latencies, 95),
        "latency_max_ms": round(max(latencies), 1),
        "latency_mean_ms": round(statistics.mean(latencies), 1),
        "requests": [asdict(item) for item in results],
    }


def related_logs(correlation_ids: set[str]) -> list[dict[str, Any]]:
    log_path = REPO_ROOT / "data/logs.jsonl"
    if not log_path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("correlation_id") in correlation_ids and record.get("event") in {
            "retrieval_completed",
            "response_sent",
        }:
            records.append(record)
    return records


def render_text(evidence: dict[str, Any]) -> str:
    baseline = evidence["phases"]["baseline"]
    incident = evidence["phases"]["incident"]
    recovery = evidence["phases"]["recovery"]
    log_sample = evidence["root_cause_log_sample"]
    return "\n".join(
        [
            "=== CHECKPOINT 3: ĐIỀU TRA CHALLENGE CHÍNH THỨC ===",
            f"Sinh viên: Dương Tiến Dũng - 2A202602020",
            f"Challenge ID: {evidence['challenge_id']}",
            f"Incident: {evidence['incident']}",
            f"Ngưỡng challenge: {evidence['latency_threshold_ms']} ms",
            "",
            f"Baseline P95: {baseline['latency_p95_ms']} ms",
            f"Incident P95: {incident['latency_p95_ms']} ms",
            f"Recovery P95: {recovery['latency_p95_ms']} ms",
            f"Vi phạm ngưỡng: {evidence['threshold_breached']}",
            f"Phục hồi thành công: {evidence['recovery_confirmed']}",
            "",
            "Metrics -> Traces -> Logs:",
            "1. Metrics: P95 của batch incident vượt ngưỡng challenge.",
            "2. Traces: mở trace theo correlation ID bên dưới và kiểm tra span retrieve.",
            f"3. Logs: {json.dumps(log_sample, ensure_ascii=False)}",
            "",
            f"Correlation ID tiêu biểu: {evidence['representative_correlation_id']}",
            "Root cause: incident rag_slow làm retrieval chờ khoảng 2500 ms.",
            "Fix action: tắt rag_slow và xác minh lại bằng batch recovery.",
            "Preventive measure: alert P95, timeout retrieval, fallback và đối chiếu trace/log theo correlation ID.",
        ]
    ) + "\n"


def main() -> None:
    configure_utf8_stdio()
    challenge = load_challenge()
    if challenge.incident != "rag_slow":
        raise RuntimeError("Script CP3 này chỉ tự động hóa challenge rag_slow đã được Lab Coach release.")

    with httpx.Client(timeout=30.0) as client:
        health = client.get(f"{BASE_URL}/health")
        health.raise_for_status()
        client.post(f"{BASE_URL}/incidents/{challenge.incident}/disable").raise_for_status()
        run_token = f"{time.time_ns() & 0xFFFFF:05x}"
        warmup_payload = ordered_queries(challenge)[0]
        client.post(
            f"{BASE_URL}/chat",
            json=warmup_payload,
            headers={"x-request-id": f"req-a{run_token}00"},
        ).raise_for_status()
        baseline_results = run_batch(client, challenge, "baseline", run_token)
        try:
            client.post(f"{BASE_URL}/incidents/{challenge.incident}/enable").raise_for_status()
            incident_results = run_batch(client, challenge, "incident", run_token)
        finally:
            client.post(f"{BASE_URL}/incidents/{challenge.incident}/disable").raise_for_status()
        recovery_results = run_batch(client, challenge, "recovery", run_token)
        final_health = client.get(f"{BASE_URL}/health").json()

    baseline = summarize_phase(baseline_results)
    incident = summarize_phase(incident_results)
    recovery = summarize_phase(recovery_results)
    incident_ids = {item.correlation_id for item in incident_results}
    logs = related_logs(incident_ids)
    slow_retrieval_logs = [
        record
        for record in logs
        if record.get("event") == "retrieval_completed"
        and record.get("payload", {}).get("incident_active") is True
    ]
    representative = max(incident_results, key=lambda item: item.latency_ms)
    representative_logs = [
        record for record in slow_retrieval_logs if record.get("correlation_id") == representative.correlation_id
    ]

    evidence = {
        "student": {"name": "Dương Tiến Dũng", "student_id": "2A202602020"},
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "challenge_id": challenge.challenge_id,
        "incident": challenge.incident,
        "affected_feature": challenge.affected_feature,
        "latency_threshold_ms": challenge.latency_threshold_ms,
        "phases": {"baseline": baseline, "incident": incident, "recovery": recovery},
        "threshold_breached": incident["latency_p95_ms"] > challenge.latency_threshold_ms,
        "recovery_confirmed": recovery["latency_p95_ms"] < challenge.latency_threshold_ms,
        "representative_correlation_id": representative.correlation_id,
        "root_cause_log_sample": representative_logs[0] if representative_logs else None,
        "incident_log_count": len(logs),
        "final_incident_state": final_health["incidents"],
    }
    if not evidence["threshold_breached"]:
        raise RuntimeError("P95 incident chưa vượt ngưỡng; chưa đủ bằng chứng challenge.")
    if not evidence["recovery_confirmed"]:
        raise RuntimeError("P95 recovery chưa trở lại dưới ngưỡng.")
    if evidence["root_cause_log_sample"] is None:
        raise RuntimeError("Không tìm thấy retrieval log cùng correlation ID để chứng minh root cause.")

    EVIDENCE_JSON.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    EVIDENCE_TEXT.write_text(render_text(evidence), encoding="utf-8")
    print(render_text(evidence), end="")
    print(f"Evidence JSON: {EVIDENCE_JSON.relative_to(REPO_ROOT)}")
    print(f"Evidence text: {EVIDENCE_TEXT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
