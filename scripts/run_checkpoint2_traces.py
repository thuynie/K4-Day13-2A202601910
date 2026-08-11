from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio


def main() -> None:
    configure_utf8_stdio()
    load_dotenv(REPO_ROOT / ".env")
    os.environ["LANGFUSE_PROMPT_NAME"] = "day13-chat"

    from fastapi.testclient import TestClient
    from langfuse import get_client

    from app.main import app

    started = datetime.now(timezone.utc) - timedelta(minutes=1)
    with TestClient(app) as api:
        for label in ("baseline", "candidate"):
            os.environ["LANGFUSE_PROMPT_LABEL"] = label
            for index in range(5):
                response = api.post(
                    "/chat",
                    json={
                        "user_id": f"2A202601510-{index + 1}",
                        "session_id": f"checkpoint-2-{label}",
                        "feature": "monitoring",
                        "message": "Explain why metrics traces and logs work together.",
                    },
                )
                response.raise_for_status()
                print(f"label={label} request={index + 1} status={response.status_code}")

    langfuse = get_client()
    langfuse.flush()
    matched = []
    for attempt in range(1, 7):
        traces = langfuse.api.trace.list(
            limit=100,
            tags="lab",
            from_timestamp=started,
            order_by="timestamp.desc",
        )
        matched = [
            trace
            for trace in traces.data
            if (trace.metadata or {}).get("prompt_label") in {"baseline", "candidate"}
        ]
        if len(matched) >= 10:
            break
        print(f"Đang chờ Langfuse đồng bộ traces ({attempt}/6)...")
        time.sleep(5)

    for trace in matched:
        metadata = trace.metadata or {}
        print(
            f"trace_id={trace.id} label={metadata.get('prompt_label')} "
            f"version={metadata.get('prompt_version')} source={metadata.get('prompt_source')}"
        )
    print(f"checkpoint2_traces={len(matched)}")
    if len(matched) < 10:
        raise SystemExit("Chưa đủ 10 traces trên Langfuse. Chạy lại script sau vài giây.")


if __name__ == "__main__":
    main()
