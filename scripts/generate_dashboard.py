from __future__ import annotations

import argparse
import html
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio
from app.metrics import percentile


LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"
CONFIG_PATH = REPO_ROOT / "config" / "dashboard.yaml"
DEFAULT_OUTPUT = REPO_ROOT / "submission" / "evidence" / "checkpoint-2-dashboard.html"


def read_records(minutes: int) -> list[dict]:
    if not LOG_PATH.exists():
        raise SystemExit("Không tìm thấy data/logs.jsonl. Hãy chạy load test trước.")
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    records = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        timestamp = datetime.fromisoformat(record["ts"].replace("Z", "+00:00"))
        if timestamp >= cutoff:
            records.append(record)
    return records


def threshold(panel: dict) -> str:
    item = panel["threshold"]
    operator = "≤" if item["operator"] == "lte" else "≥"
    return f"SLO: {item['aggregation']} {operator} {item['value']} {panel['unit']}"


def card(title: str, value: str, detail: str, threshold_text: str, state: str) -> str:
    return f"""
    <section class="panel {state}">
      <div class="panel-title">{html.escape(title)}</div>
      <div class="value">{html.escape(value)}</div>
      <div class="detail">{html.escape(detail)}</div>
      <div class="threshold">{html.escape(threshold_text)}</div>
    </section>"""


def build_dashboard(records: list[dict], config: dict) -> str:
    panels = {panel["id"]: panel for panel in config["dashboard"]["panels"]}
    requests = [item for item in records if item.get("event") == "request_received"]
    responses = [item for item in records if item.get("event") == "response_sent"]
    failures = [item for item in records if item.get("event") == "request_failed"]

    latencies = [int(item["latency_ms"]) for item in responses]
    p50 = percentile(latencies, 50)
    p95 = percentile(latencies, 95)
    p99 = percentile(latencies, 99)
    latency_limit = panels["latency"]["threshold"]["value"]

    timestamps = [datetime.fromisoformat(item["ts"].replace("Z", "+00:00")) for item in requests]
    observed_minutes = max(1.0, ((max(timestamps) - min(timestamps)).total_seconds() / 60)) if timestamps else 1.0
    rate = len(requests) / observed_minutes

    error_rate = (len(failures) / len(requests) * 100) if requests else 0.0
    errors = Counter(item.get("error_type", "unknown") for item in failures)
    error_detail = ", ".join(f"{key}: {value}" for key, value in errors.items()) or "No errors"

    total_cost = sum(float(item.get("cost_usd", 0)) for item in responses)
    tokens_in = sum(int(item.get("tokens_in", 0)) for item in responses)
    tokens_out = sum(int(item.get("tokens_out", 0)) for item in responses)
    quality_values = [float(item["quality_score"]) for item in responses if "quality_score" in item]
    quality = mean(quality_values) if quality_values else 0.0

    cards = [
        card(
            panels["latency"]["title"],
            f"P95 {p95:.0f} ms",
            f"P50 {p50:.0f} ms · P99 {p99:.0f} ms",
            threshold(panels["latency"]),
            "ok" if p95 <= latency_limit else "bad",
        ),
        card(
            panels["traffic"]["title"],
            f"{len(requests)} requests",
            f"{rate:.2f} requests/minute",
            threshold(panels["traffic"]),
            "ok" if rate >= panels["traffic"]["threshold"]["value"] else "warn",
        ),
        card(
            panels["errors"]["title"],
            f"{error_rate:.2f}%",
            error_detail,
            threshold(panels["errors"]),
            "ok" if error_rate <= panels["errors"]["threshold"]["value"] else "bad",
        ),
        card(
            panels["cost"]["title"],
            f"${total_cost:.6f}",
            f"{len(responses)} successful responses",
            threshold(panels["cost"]),
            "ok" if total_cost <= panels["cost"]["threshold"]["value"] else "bad",
        ),
        card(
            panels["tokens"]["title"],
            f"{tokens_in + tokens_out:,} tokens",
            f"Input {tokens_in:,} · Output {tokens_out:,}",
            threshold(panels["tokens"]),
            "ok" if max(tokens_in, tokens_out) <= panels["tokens"]["threshold"]["value"] else "bad",
        ),
        card(
            panels["quality"]["title"],
            f"{quality:.2f}",
            "Mean heuristic quality score",
            threshold(panels["quality"]),
            "ok" if quality >= panels["quality"]["threshold"]["value"] else "warn",
        ),
    ]

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    refresh = config["dashboard"]["refresh_seconds"]
    time_range = config["dashboard"]["time_range_minutes"]
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="{refresh}">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Day 13 AI Observability</title>
  <style>
    :root {{ color-scheme: dark; font-family: Inter, Segoe UI, sans-serif; }}
    body {{ margin: 0; background: #07111f; color: #e7eef9; }}
    header {{ padding: 28px 38px; border-bottom: 1px solid #26364d; background: #0b1729; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; }}
    .meta {{ color: #9fb0c8; display: flex; gap: 24px; flex-wrap: wrap; }}
    main {{ display: grid; grid-template-columns: repeat(3, minmax(260px, 1fr)); gap: 18px; padding: 28px 38px; }}
    .panel {{ min-height: 190px; padding: 22px; border-radius: 14px; border: 1px solid #2a3b55; background: #101e32; box-shadow: 0 8px 24px #0004; }}
    .panel.ok {{ border-top: 5px solid #26c281; }} .panel.warn {{ border-top: 5px solid #f4b942; }} .panel.bad {{ border-top: 5px solid #ef6262; }}
    .panel-title {{ color: #b9c8db; font-weight: 650; font-size: 17px; }}
    .value {{ font-size: 35px; font-weight: 750; margin: 25px 0 12px; }}
    .detail {{ color: #a8b8cc; min-height: 38px; }}
    .threshold {{ margin-top: 18px; padding-top: 13px; border-top: 1px dashed #41526b; color: #70d6a7; font-family: Consolas, monospace; }}
    footer {{ padding: 4px 38px 30px; color: #7f91aa; }}
    @media (max-width: 1000px) {{ main {{ grid-template-columns: repeat(2, 1fr); }} }}
  </style>
</head>
<body>
  <header>
    <h1>Day 13 AI Observability</h1>
    <div class="meta"><span>Source: data/logs.jsonl</span><span>Time range: Last {time_range} minutes</span><span>Auto refresh: {refresh}s</span><span>Generated: {generated}</span></div>
  </header>
  <main>{''.join(cards)}</main>
  <footer>Owner: Đặng Quang Trung · 2A202601510 · Metrics → Traces → Logs</footer>
</body>
</html>"""


def main() -> None:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Generate the Checkpoint 2 dashboard")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    minutes = int(config["dashboard"]["time_range_minutes"])
    records = read_records(minutes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_dashboard(records, config), encoding="utf-8")
    print(f"Dashboard generated: {args.output}")
    print(f"Records in last {minutes} minutes: {len(records)}")


if __name__ == "__main__":
    main()
