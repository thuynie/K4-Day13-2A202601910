from __future__ import annotations

import json
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

import yaml

LOG_PATH = Path("data/logs.jsonl")
DASHBOARD_CONFIG_PATH = Path("config/dashboard.yaml")


def _load_config() -> dict:
    payload = yaml.safe_load(DASHBOARD_CONFIG_PATH.read_text(encoding="utf-8"))
    return payload["dashboard"]


def _read_records(window_minutes: int) -> list[dict]:
    if not LOG_PATH.exists():
        return []
    cutoff = time.time() - window_minutes * 60
    records = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = rec.get("ts")
        try:
            rec_time = datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp()
        except (TypeError, ValueError):
            continue
        if rec_time >= cutoff:
            records.append(rec)
    return records


def _percentile(values: list[float], p: int) -> float:
    if not values:
        return 0.0
    items = sorted(values)
    idx = max(0, min(len(items) - 1, round((p / 100) * len(items) + 0.5) - 1))
    return float(items[idx])


def compute_snapshot(window_minutes: int = 60) -> dict:
    records = _read_records(window_minutes)

    latencies = [
        r["latency_ms"] for r in records
        if r.get("event") == "response_sent" and isinstance(r.get("latency_ms"), (int, float))
    ]
    received = [r for r in records if r.get("event") == "request_received"]
    failed = [r for r in records if r.get("event") == "request_failed"]
    costs = [
        r["cost_usd"] for r in records
        if r.get("event") == "response_sent" and isinstance(r.get("cost_usd"), (int, float))
    ]
    tokens_in = sum(r.get("tokens_in") or 0 for r in records if r.get("event") == "response_sent")
    tokens_out = sum(r.get("tokens_out") or 0 for r in records if r.get("event") == "response_sent")
    quality = [
        r["quality_score"] for r in records
        if r.get("event") == "response_sent" and isinstance(r.get("quality_score"), (int, float))
    ]
    error_breakdown = Counter(r.get("error_type") or "unknown" for r in failed)

    total_requests = len(received)
    error_rate_pct = round((len(failed) / total_requests * 100), 2) if total_requests else 0.0

    return {
        "window_minutes": window_minutes,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "latency": {
            "p50": _percentile(latencies, 50),
            "p95": _percentile(latencies, 95),
            "p99": _percentile(latencies, 99),
        },
        "traffic": {
            "count": total_requests,
            "rate_per_minute": round(total_requests / window_minutes, 2) if window_minutes else 0.0,
        },
        "errors": {
            "error_rate_pct": error_rate_pct,
            "breakdown": dict(error_breakdown),
        },
        "cost": {"total": round(sum(costs), 4)},
        "tokens": {"tokens_in": tokens_in, "tokens_out": tokens_out},
        "quality": {"mean": round(mean(quality), 4) if quality else 0.0},
    }


def _threshold_ok(value: float, threshold: dict) -> bool:
    operator = threshold.get("operator")
    target = threshold.get("value")
    if operator == "lte":
        return value <= target
    if operator == "gte":
        return value >= target
    return True


def render_dashboard_html() -> str:
    config = _load_config()
    window_minutes = config.get("time_range_minutes", 60)
    snap = compute_snapshot(window_minutes)
    panels = config["panels"]

    panel_display = {
        "latency": (
            snap["latency"]["p95"],
            f'P50 {snap["latency"]["p50"]:.0f} · P95 {snap["latency"]["p95"]:.0f} · P99 {snap["latency"]["p99"]:.0f}',
        ),
        "traffic": (
            snap["traffic"]["rate_per_minute"],
            f'{snap["traffic"]["count"]} requests ({snap["traffic"]["rate_per_minute"]}/phút)',
        ),
        "errors": (
            snap["errors"]["error_rate_pct"],
            f'{snap["errors"]["error_rate_pct"]}% · {snap["errors"]["breakdown"] or "không lỗi"}',
        ),
        "cost": (snap["cost"]["total"], f'${snap["cost"]["total"]}'),
        "tokens": (
            snap["tokens"]["tokens_in"] + snap["tokens"]["tokens_out"],
            f'in {snap["tokens"]["tokens_in"]} · out {snap["tokens"]["tokens_out"]}',
        ),
        "quality": (snap["quality"]["mean"], f'{snap["quality"]["mean"]}'),
    }

    cards = []
    for panel in panels:
        pid = panel["id"]
        value, display = panel_display[pid]
        threshold = panel["threshold"]
        ok = _threshold_ok(value, threshold)
        status_class = "ok" if ok else "breach"
        cards.append(
            f'''
        <div class="card {status_class}">
          <h2>{panel["title"]}</h2>
          <div class="value">{display}</div>
          <div class="unit">Đơn vị: {panel["unit"]}</div>
          <div class="threshold">Threshold: {threshold["aggregation"]} {threshold["operator"]} {threshold["value"]} — {"OK" if ok else "VI PHẠM"}</div>
        </div>'''
        )

    return f'''<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="{config.get('refresh_seconds', 30)}">
<title>{config['title']}</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 24px; }}
  h1 {{ font-size: 1.4rem; margin-bottom: 4px; }}
  .meta {{ color: #94a3b8; margin-bottom: 20px; font-size: 0.9rem; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; }}
  .card {{ background: #1e293b; border-radius: 10px; padding: 16px 18px; border: 1px solid #334155; }}
  .card.ok {{ border-left: 4px solid #22c55e; }}
  .card.breach {{ border-left: 4px solid #ef4444; }}
  .card h2 {{ font-size: 1rem; margin: 0 0 8px; color: #cbd5e1; }}
  .value {{ font-size: 1.6rem; font-weight: 600; }}
  .unit, .threshold {{ font-size: 0.8rem; color: #94a3b8; margin-top: 4px; }}
</style>
</head>
<body>
  <h1>{config['title']}</h1>
  <div class="meta">Time range: {window_minutes} phút · Refresh: {config.get('refresh_seconds', 30)}s · Cập nhật lúc: {snap['generated_at']}</div>
  <div class="grid">
    {''.join(cards)}
  </div>
</body>
</html>'''
