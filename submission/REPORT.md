# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 30/100 (baseline Checkpoint 0, trước khi triển khai Logging & PII)
- Tổng số traces: 9 trace có tag `lab` đã xác minh trên Langfuse sau setup (sẽ bổ sung/chuẩn hóa evidence ở Checkpoint 2)
- Số PII leak còn lại: 0 trong baseline
- Link/đường dẫn dashboard:

### Evidence Checkpoint 0

- Health (`ok=true`, tracing bật): [`evidence/checkpoint-0-health.png`](evidence/checkpoint-0-health.png)
- Swagger API docs và danh sách endpoint: [`evidence/checkpoint-0-api-docs.png`](evidence/checkpoint-0-api-docs.png)
- Metrics baseline trước load test: [`evidence/checkpoint-0-metrics-baseline.png`](evidence/checkpoint-0-metrics-baseline.png)
- Chi tiết môi trường dạng text: [`evidence/checkpoint-0-health.txt`](evidence/checkpoint-0-health.txt)
- Load test và baseline log: [`evidence/checkpoint-0-baseline.txt`](evidence/checkpoint-0-baseline.txt)
- Commit tại thời điểm kiểm tra: `5ba64725aaf0b5b4d51c28772973373d98d0f149`

## 3. Logging và tracing

- Evidence correlation ID:
- Evidence PII redaction:
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
| | | | |
