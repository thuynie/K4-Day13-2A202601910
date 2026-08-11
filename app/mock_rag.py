from __future__ import annotations

import time

from .incidents import STATE
from .logging_config import get_logger
from .pii import summarize_text
from .tracing import observe

log = get_logger()

CORPUS = {
    "refund": ["Refunds are available within 7 days with proof of purchase."],
    "monitoring": ["Metrics detect incidents, traces localize them, logs explain root cause."],
    "policy": ["Do not expose PII in logs. Use sanitized summaries only."],
}


@observe(as_type="span")
def retrieve(message: str) -> list[str]:
    started = time.perf_counter()
    incident_active = STATE["rag_slow"]
    try:
        if STATE["tool_fail"]:
            raise RuntimeError("Vector store timeout")
        if incident_active:
            time.sleep(2.5)
        lowered = message.lower()
        for key, docs in CORPUS.items():
            if key in lowered:
                result = docs
                break
        else:
            result = ["No domain document matched. Use general fallback answer."]

        log.info(
            "retrieval_completed",
            service="retrieval",
            latency_ms=int((time.perf_counter() - started) * 1000),
            payload={
                "incident": "rag_slow" if incident_active else None,
                "incident_active": incident_active,
                "query_preview": summarize_text(message),
                "result_count": len(result),
            },
        )
        return result
    except Exception as exc:
        log.error(
            "retrieval_failed",
            service="retrieval",
            latency_ms=int((time.perf_counter() - started) * 1000),
            error_type=type(exc).__name__,
            payload={"query_preview": summarize_text(message)},
        )
        raise
