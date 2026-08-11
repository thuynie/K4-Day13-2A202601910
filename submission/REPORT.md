# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL: https://github.com/thuynie/K4-Day13-2A202601910
- Commit SHA cuối: `881493ea92bdb619024a8a8bf350928bc46a4cad` (nhánh `fix/observability-logging`)
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: **100/100** (4/4 hạng mục PASSED: JSON schema, correlation ID, log enrichment, PII scrubbing)
- Tổng số traces: **110** (project `day13`, org "Hoàng's Organization")
- Số PII leak còn lại: **0**
- Link/đường dẫn dashboard: `http://127.0.0.1:8000/dashboard` — ảnh: `submission/evidence/dashboard.png`

## 3. Logging và tracing

- Evidence correlation ID: mỗi request sinh ID dạng `req-<8 hex>` tại [app/middleware.py](../app/middleware.py), bind vào structlog contextvars và trả về header `x-request-id`. Validator ghi nhận 20 correlation ID duy nhất trên 42 log record, không còn ID nào là `MISSING`.
- Evidence PII redaction: `data/logs.jsonl` dòng 1, 9, 17 cho thấy email/số điện thoại/số thẻ đã bị thay bằng `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, `[REDACTED_CREDIT_CARD]`. Kiểm tra thủ công `grep -i "@"` và `grep "4111"` đều trả về 0 kết quả.
- Evidence trace waterfall: `submission/evidence/waterfall.png` — trace `d7a059843566f61256f6cbd4746f07de`, thấy rõ span `run` chứa `retrieve` (0.00s) và `generate` (0.15s), kèm Session `s05`, User ID hash `64f6ec689229`, tags `lab`/`qa`/`claude-sonnet-4-5`, metadata có `correlation_id: req-b0842072` và `query_preview` đã redact thành `[REDACTED_PHONE_VN]`
- Evidence danh sách traces: `submission/evidence/danh sách trace.png` — bảng Tracing lọc `isRootObservation:true`, tổng ≈90 traces
- Giải thích một span đáng chú ý: decorator `@observe` được gắn thêm ở [app/mock_rag.py](../app/mock_rag.py) và [app/mock_llm.py](../app/mock_llm.py) nên mỗi trace tách thành 3 span: `run` (cha) chứa `retrieve` (RAG) và `generate` (LLM). Nhờ vậy khi P95 tăng có thể nhìn ngay span nào chiếm thời gian — với incident `rag_slow` thì `retrieve` phình lên ~2.5s trong khi `generate` giữ nguyên ~0.15s.

## 4. Prompt versioning

- Prompt name: `day13-chat` (type: Text)
- Version/label baseline: **version 1**, label `baseline`
- Version/label candidate: **version 2**, label `candidate`
- Trace ID của mỗi version:

| Label | Version | Trace ID | Correlation ID | Session |
|---|---|---|---|---|
| `baseline` | 1 | `ca392991d77d87659d2d50a140eac11c` | `req-cca52035` | s01 |
| `candidate` | 2 | `daff2d4d35c23a24bf74154c698ca798` | `req-407bda6b` | s01 |
| `production` | 3 | `5e814c4fc8575ce845b9f23124d27fda` | `req-f90a557e` | s10 |

Mỗi đợt chạy 10 trace với cùng bộ input trong `data/sample_queries.jsonl`, chỉ khác `LANGFUSE_PROMPT_LABEL` trong `.env`. Metadata trace ghi đủ `prompt_name`, `prompt_label`, `prompt_version` và `prompt_source=langfuse`.

- Bằng chứng đổi label hoặc rollback: label `production` được di chuyển qua 3 version, mỗi bước có ảnh chụp màn hình trang Prompts:

| Bước | Trạng thái | Ảnh |
|---|---|---|
| Trước | `production` ở version 3 | `submission/evidence/rollback version 3.png` |
| Đổi label | `production` chuyển sang version 2 | `submission/evidence/rollback version2.png` |
| Rollback | `production` về version 1 | `submission/evidence/rollback version1.png` |

Rollback được xác minh end-to-end, không chỉ trên UI:

1. API trả về `production -> version 1` (labels: `baseline`, `production`)
2. Chạy lại `scripts/load_test.py` sau khi prompt cache (TTL 60s) hết hạn, trace mới ghi `prompt_version: 1` — ví dụ `correlation_id: req-7d629ce0`

Ba ảnh trên đồng thời là bằng chứng cho yêu cầu "ảnh danh sách hai prompt version": sidebar hiển thị đủ version 1 (`baseline`), version 2 (`candidate`) và version 3 (`latest`).

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: **HỢP LỆ — 6/6 panel** đúng contract `config/dashboard.yaml`
- Evidence dashboard: `submission/evidence/dashboard.png` — 6 panel (latency P50/P95/P99, traffic, error rate + breakdown, cost, tokens in/out, quality), time range 60 phút, auto refresh 30s, mỗi panel hiển thị threshold kèm trạng thái OK/VI PHẠM
- SLO đã chọn và lý do (`config/slo.yaml`):

| SLI | Objective | Lý do |
|---|---|---|
| `latency_p95_ms` | 3000ms | Ngưỡng người dùng còn chấp nhận chờ cho tác vụ hỏi–đáp; vượt mức này trải nghiệm xuống rõ rệt |
| `error_rate_pct` | < 2% | Lỗi 500 khiến người dùng không nhận được câu trả lời, cần ngưỡng chặt |
| `daily_cost_usd` | < $2.5/ngày | Ràng buộc ngân sách vận hành của lab |
| `quality_score_avg` | ≥ 0.75 | Ngưỡng proxy để phát hiện suy giảm chất lượng trả lời |

- Alert rules và runbook: 3 alert symptom-based trong [config/alert_rules.yaml](../config/alert_rules.yaml), runbook chi tiết tại [docs/alerts.md](../docs/alerts.md)

| Alert | Severity | Điều kiện | Owner |
|---|---|---|---|
| `high_latency_p95` | warning | `latency_p95 > 3000ms` trong 5 phút | on-call-engineer |
| `elevated_error_rate` | critical | `error_rate_pct > 5` trong 3 phút | on-call-engineer |
| `cost_budget_exceeded` | warning | `daily_cost_usd > 2.5` | team-lead |

Mỗi runbook gồm SLI/SLO liên quan, ảnh hưởng người dùng, ba bước kiểm tra đầu tiên (dashboard → trace waterfall → log theo correlation ID), mitigation tạm thời và owner.

## 6. Điều tra challenge

- Challenge ID: *(chờ Lab Coach release `config/challenge.json`)*
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

---

## Danh sách evidence

| File | Nội dung |
|---|---|
| `dashboard.png` | Dashboard 6 panel, time range 60 phút, threshold từng panel |
| `danh sách trace.png` | Bảng Traces (~90 traces, lọc root observation) |
| `waterfall.png` | Waterfall một trace: `run` → `retrieve` + `generate`, kèm metadata |
| `rollback version 3.png` | `production` ở version 3 (trước khi đổi) |
| `rollback version2.png` | `production` chuyển sang version 2 |
| `rollback version1.png` | `production` rollback về version 1 (sau) |

## Việc còn thiếu

- [ ] Điền tên nhóm, thành viên và bảng đóng góp cá nhân (mục 1 và 7)
- [ ] Mục 6 sau khi Lab Coach release `config/challenge.json`
