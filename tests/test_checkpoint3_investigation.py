from scripts.run_checkpoint3_challenge import RequestResult, percentile, summarize_phase


def test_checkpoint3_phase_summary_uses_batch_latency() -> None:
    results = [
        RequestResult("req-00000001", "s01", 200, 150.0),
        RequestResult("req-00000002", "s02", 200, 2650.0),
        RequestResult("req-00000003", "s03", 200, 2600.0),
    ]

    summary = summarize_phase(results)

    assert summary["request_count"] == 3
    assert summary["latency_p95_ms"] == 2650.0
    assert summary["latency_max_ms"] == 2650.0


def test_checkpoint3_percentile_handles_empty_input() -> None:
    assert percentile([], 95) == 0.0
