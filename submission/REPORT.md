# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:
  - Hoàng Thị Thuyên (`2A202601910`) — Logging & PII (Checkpoint 1)
  - Đặng Quang Trung (`2A202601510`) — Metrics, tracing, prompt versioning, dashboard, SLO và alerts (Checkpoint 2)

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100 (Checkpoint 1; baseline Checkpoint 0 là 30/100)
- Tổng số traces: 10 trace Checkpoint 2 đã xác minh với metadata prompt trên Langfuse
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard: `http://127.0.0.1:8000/dashboard` và [`evidence/checkpoint-2-dashboard.html`](evidence/checkpoint-2-dashboard.html)

### Evidence Checkpoint 0

- Health (`ok=true`, tracing bật): [`evidence/checkpoint-0-health.png`](evidence/checkpoint-0-health.png)
- Swagger API docs và danh sách endpoint: [`evidence/checkpoint-0-api-docs.png`](evidence/checkpoint-0-api-docs.png)
- Metrics baseline trước load test: [`evidence/checkpoint-0-metrics-baseline.png`](evidence/checkpoint-0-metrics-baseline.png)
- Chi tiết môi trường dạng text: [`evidence/checkpoint-0-health.txt`](evidence/checkpoint-0-health.txt)
- Load test và baseline log: [`evidence/checkpoint-0-baseline.txt`](evidence/checkpoint-0-baseline.txt)
- Commit tại thời điểm kiểm tra: `5ba64725aaf0b5b4d51c28772973373d98d0f149`

## 3. Logging và tracing

- Evidence correlation ID: [`evidence/checkpoint-1-correlation-id.png`](evidence/checkpoint-1-correlation-id.png) và [`evidence/checkpoint-1-correlation-pii.txt`](evidence/checkpoint-1-correlation-pii.txt)
- Evidence PII redaction: [`evidence/checkpoint-1-pii-redaction.png`](evidence/checkpoint-1-pii-redaction.png) và [`evidence/checkpoint-1-correlation-pii.txt`](evidence/checkpoint-1-correlation-pii.txt)
- Kết quả validator 100/100: [`evidence/checkpoint-1-validator.png`](evidence/checkpoint-1-validator.png) và [`evidence/checkpoint-1-validation.txt`](evidence/checkpoint-1-validation.txt)
- Evidence trace waterfall: [`evidence/checkpoint-2-trace-waterfall.png`](evidence/checkpoint-2-trace-waterfall.png); danh sách root observations tại [`evidence/checkpoint-2-trace-list.png`](evidence/checkpoint-2-trace-list.png); nhóm baseline tại [`evidence/checkpoint-2-trace-list-baseline.png`](evidence/checkpoint-2-trace-list-baseline.png); nhóm candidate tại [`evidence/checkpoint-2-trace-list-candidate.png`](evidence/checkpoint-2-trace-list-candidate.png); đủ 10 trace ID tại [`evidence/checkpoint-2-traces.txt`](evidence/checkpoint-2-traces.txt)
- Giải thích một span đáng chú ý: Trace `d7a059843566f61256f6cbd4746f07de` tách root `run` thành `retrieve` và `generate`. `retrieve` gần 0 giây trong baseline, còn `generate` khoảng 0.15 giây; metadata chứa correlation ID `req-b0842072`. Khi chạy incident `rag_slow`, span `retrieve` sẽ tăng khoảng 2.5 giây và giúp khoanh vùng root cause.

## 4. Prompt versioning

- Prompt name: `day13-chat`
- Version/label baseline: Version 1 — `baseline`, `production` (trạng thái cuối sau rollback)
- Version/label candidate: Version 2 — `candidate`
- Danh sách prompt versions: [`evidence/checkpoint-2-prompt-versions.png`](evidence/checkpoint-2-prompt-versions.png). Project có thêm version 3 mang label hệ thống `latest` do thành viên khác tạo; evidence Checkpoint 2 của Trung dùng v1/v2.
- Trace ID của mỗi version: v1 `b01ec2b51e5bde8d5398d46c14e595db` — [`evidence/checkpoint-2-trace-baseline.png`](evidence/checkpoint-2-trace-baseline.png), [`evidence/checkpoint-2-trace-baseline-metadata.png`](evidence/checkpoint-2-trace-baseline-metadata.png); v2 `461353c368e45cfe93ae90fe56a858f3` — [`evidence/checkpoint-2-trace-candidate.png`](evidence/checkpoint-2-trace-candidate.png), [`evidence/checkpoint-2-trace-candidate-metadata.png`](evidence/checkpoint-2-trace-candidate-metadata.png); đủ 10 ID tại [`evidence/checkpoint-2-traces.txt`](evidence/checkpoint-2-traces.txt)
- Bằng chứng đổi label hoặc rollback: trạng thái ban đầu [`evidence/checkpoint-2-prompt-production-v3.png`](evidence/checkpoint-2-prompt-production-v3.png), promote sang v2 [`evidence/checkpoint-2-prompt-promoted-v2.png`](evidence/checkpoint-2-prompt-promoted-v2.png), rollback về v1 [`evidence/checkpoint-2-prompt-rollback.png`](evidence/checkpoint-2-prompt-rollback.png), và nhật ký [`evidence/checkpoint-2-prompt-rollback.txt`](evidence/checkpoint-2-prompt-rollback.txt)

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: HỢP LỆ 6/6 panel — [`evidence/checkpoint-2-dashboard-validator.png`](evidence/checkpoint-2-dashboard-validator.png) và [`evidence/checkpoint-2-dashboard-validator.txt`](evidence/checkpoint-2-dashboard-validator.txt)
- Evidence dashboard: [`evidence/checkpoint-2-dashboard.png`](evidence/checkpoint-2-dashboard.png) và [`evidence/checkpoint-2-dashboard.html`](evidence/checkpoint-2-dashboard.html)
- SLO đã chọn và lý do: P95 ≤ 3000 ms, error rate ≤ 2%, cost ≤ 2.5 USD, quality ≥ 0.75; bám trực tiếp trải nghiệm người dùng và contract chung.
- Alert rules và runbook: [`../config/alert_rules.yaml`](../config/alert_rules.yaml) và [`../docs/alerts.md`](../docs/alerts.md)

## 6. Điều tra challenge

- Challenge ID:
- Triệu chứng từ metrics:
- Trace ID liên quan:
- Log line/correlation ID liên quan:
- Root cause:
- Fix action:
- Preventive measure:

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Hoàng Thị Thuyên (`2A202601910`) | Correlation ID, structured-log enrichment, PII redaction và evidence Checkpoint 1 | `c7c169d` và commit evidence tiếp theo | Correlation ID xuyên request, contextvars, thứ tự processor và redaction trước khi ghi log |
| Đặng Quang Trung (`2A202601510`) | Metrics, Langfuse traces, prompt versioning, dashboard, SLO và alerts | `ca970cc` | Đọc SLI/SLO, liên kết prompt version với trace và thiết kế alert theo triệu chứng người dùng |
