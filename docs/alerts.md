# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: high_latency_p95
- Severity: warning
- SLI/SLO liên quan: `latency_p95_ms` (objective 3000ms, target 99.5%)
- Điều kiện và thời gian duy trì: `latency_p95 > 3000ms` trong 5 phút liên tục
- Ảnh hưởng tới người dùng: Câu trả lời chat bị chậm rõ rệt, người dùng chờ lâu hơn mức chấp nhận được, có thể timeout ở phía client
- Ba bước kiểm tra đầu tiên:
  1. Xem panel Latency trên dashboard để xác nhận P95/P99 đang tăng và từ thời điểm nào
  2. Mở trace waterfall trên Langfuse của một request chậm gần nhất, xác định span nào chiếm phần lớn thời gian (RAG retrieve hay LLM generate)
  3. Tra log `data/logs.jsonl` theo `correlation_id` của trace đó để xem chi tiết event và có `error_type` đi kèm không
- Mitigation tạm thời: Nếu do RAG chậm (ví dụ incident `rag_slow`), tắt incident bằng `python scripts/inject_incident.py --scenario rag_slow --disable`; nếu do tải cao, giảm concurrency của load test hoặc scale thêm instance
- Owner: on-call-engineer

## Alert 2

- Tên: elevated_error_rate
- Severity: critical
- SLI/SLO liên quan: `error_rate_pct` (objective dưới 2%, target 99.0%)
- Điều kiện và thời gian duy trì: `error_rate_pct > 5` trong 3 phút liên tục
- Ảnh hưởng tới người dùng: Một phần request `/chat` trả lỗi 500, người dùng không nhận được câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Xem panel Error trên dashboard để xác nhận tỷ lệ lỗi và breakdown theo `error_type`
  2. Lọc log có `event == "request_failed"` trong `data/logs.jsonl`, đọc `payload.detail` và `correlation_id` để xác định exception cụ thể (ví dụ `RuntimeError` từ vector store)
  3. Kiểm tra trạng thái incident hiện tại qua `GET /health` (field `incidents`) để biết có đang bật `tool_fail` không
- Mitigation tạm thời: Nếu do incident thực hành (`tool_fail`), tắt bằng `python scripts/inject_incident.py --scenario tool_fail --disable`; nếu là lỗi thật từ dependency ngoài, failover sang fallback answer hoặc tạm thời trả cảnh báo bảo trì cho người dùng
- Owner: on-call-engineer

## Alert 3

- Tên: cost_budget_exceeded
- Severity: warning
- SLI/SLO liên quan: `daily_cost_usd` (objective dưới $2.5/ngày, target 100%)
- Điều kiện và thời gian duy trì: `daily_cost_usd > 2.5` (kiểm tra theo cửa sổ ngày, không cần duy trì liên tục vì cost là cộng dồn)
- Ảnh hưởng tới người dùng: Không ảnh hưởng trực tiếp trải nghiệm, nhưng vượt ngân sách vận hành và có thể dẫn tới việc phải giới hạn (rate limit) tính năng nếu không xử lý kịp
- Ba bước kiểm tra đầu tiên:
  1. Xem panel Cost và Tokens trên dashboard để xác nhận chi phí đang tăng bất thường so với baseline
  2. Lọc log `event == "response_sent"` để xem `tokens_out` của các request gần nhất có tăng đột biến không (dấu hiệu incident `cost_spike`)
  3. Kiểm tra `GET /health` xem incident `cost_spike` có đang bật không, đối chiếu với `quality_score` xem output có bất thường (lặp, dài dòng) không
- Mitigation tạm thời: Nếu do incident thực hành (`cost_spike`), tắt bằng `python scripts/inject_incident.py --scenario cost_spike --disable`; nếu là traffic tăng thật, giới hạn `max_tokens` đầu ra hoặc tạm dừng các feature không thiết yếu
- Owner: team-lead
