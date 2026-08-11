from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app import logging_config
from app.main import app


def _chat(client: TestClient, *, headers: dict[str, str] | None = None):
    return client.post(
        "/chat",
        headers=headers,
        json={
            "user_id": "student-2A202601910",
            "session_id": "checkpoint-1-session",
            "feature": "qa",
            "message": (
                "Contact student@vinuni.edu.vn, 090 123 4567, "
                "or card 4111 1111 1111 1111"
            ),
        },
    )


def test_checkpoint1_correlation_enrichment_and_pii(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    with TestClient(app) as client:
        response = _chat(client)

    assert response.status_code == 200
    correlation_id = response.headers["x-request-id"]
    assert re.fullmatch(r"req-[0-9a-f]{8}", correlation_id)
    assert response.json()["correlation_id"] == correlation_id
    assert int(response.headers["x-response-time-ms"]) >= 0

    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    api_records = [record for record in records if record.get("service") == "api"]
    assert api_records
    for record in api_records:
        assert record["correlation_id"] == correlation_id
        assert record["session_id"] == "checkpoint-1-session"
        assert record["feature"] == "qa"
        assert record["model"]
        assert record["env"] == "dev"
        assert record["user_id_hash"] != "student-2A202601910"

    rendered = log_path.read_text(encoding="utf-8")
    assert "student@vinuni.edu.vn" not in rendered
    assert "090 123 4567" not in rendered
    assert "4111 1111 1111 1111" not in rendered
    assert "REDACTED_EMAIL" in rendered
    assert "REDACTED_PHONE_VN" in rendered
    assert "REDACTED_CREDIT_CARD" in rendered


def test_checkpoint1_accepts_only_valid_request_ids(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(logging_config, "LOG_PATH", tmp_path / "logs.jsonl")

    with TestClient(app) as client:
        accepted = _chat(client, headers={"x-request-id": "req-deadbeef"})
        replaced = _chat(client, headers={"x-request-id": "unsafe-request-id"})

    assert accepted.headers["x-request-id"] == "req-deadbeef"
    assert re.fullmatch(r"req-[0-9a-f]{8}", replaced.headers["x-request-id"])
