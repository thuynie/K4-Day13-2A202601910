# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:
  - Hoàng Thị Thuyên (`2A202601910`) — Logging & PII (Checkpoint 1)

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100 (Checkpoint 1; baseline Checkpoint 0 là 30/100)
- Tổng số traces: 9 trace có tag `lab` đã xác minh trên Langfuse sau setup (sẽ bổ sung/chuẩn hóa evidence ở Checkpoint 2)
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard:

### Evidence Checkpoint 0

- Health (`ok=true`, tracing bật): [`evidence/checkpoint-0-health.png`](evidence/checkpoint-0-health.png)
- Swagger API docs và danh sách endpoint: [`evidence/checkpoint-0-api-docs.png`](evidence/checkpoint-0-api-docs.png)
- Metrics baseline trước load test: [`evidence/checkpoint-0-metrics-baseline.png`](evidence/checkpoint-0-metrics-baseline.png)
- Chi tiết môi trường dạng text: [`evidence/checkpoint-0-health.txt`](evidence/checkpoint-0-health.txt)
- Load test và baseline log: [`evidence/checkpoint-0-baseline.txt`](evidence/checkpoint-0-baseline.txt)
- Commit tại thời điểm kiểm tra: `5ba64725aaf0b5b4d51c28772973373d98d0f149`

## 3. Logging và tracing

- Evidence correlation ID: [`evidence/checkpoint-1-correlation-pii.txt`](evidence/checkpoint-1-correlation-pii.txt)
- Evidence PII redaction: [`evidence/checkpoint-1-correlation-pii.txt`](evidence/checkpoint-1-correlation-pii.txt)
- Kết quả validator 100/100: [`evidence/checkpoint-1-validation.txt`](evidence/checkpoint-1-validation.txt)
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`:
- Evidence dashboard:
- SLO đã chọn và lý do:
- Alert rules và runbook:

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
