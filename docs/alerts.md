# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: High user-visible latency
- Severity: Warning
- SLI/SLO liên quan: `latency_p95_ms <= 3000` trong cửa sổ SLO 28 ngày.
- Điều kiện và thời gian duy trì: P95 latency lớn hơn 3000 ms liên tục 5 phút.
- Ảnh hưởng tới người dùng: Phản hồi chat chậm, tăng nguy cơ timeout và người dùng gửi lại request.
- Ba bước kiểm tra đầu tiên: (1) xác nhận time range và P95 trên dashboard; (2) mở trace chậm nhất để tìm span chiếm thời gian; (3) tìm log cùng correlation ID để xác nhận lỗi RAG/tool/model.
- Mitigation tạm thời: Giảm concurrency, tắt incident/feature gây chậm hoặc chuyển sang fallback trong khi điều tra.
- Owner: Đặng Quang Trung (`2A202601510`).

## Alert 2

- Tên: Elevated request error rate
- Severity: Critical
- SLI/SLO liên quan: `error_rate_pct <= 2`.
- Điều kiện và thời gian duy trì: Error rate lớn hơn 2% liên tục 5 phút.
- Ảnh hưởng tới người dùng: Request chat trả lỗi hoặc không có câu trả lời.
- Ba bước kiểm tra đầu tiên: (1) kiểm tra error breakdown; (2) mở trace lỗi đại diện; (3) đối chiếu `error_type` và correlation ID trong log.
- Mitigation tạm thời: Tắt dependency/incident lỗi, bật fallback và giới hạn traffic nếu cần.
- Owner: Đặng Quang Trung (`2A202601510`).

## Alert 3

- Tên: Quality proxy degradation
- Severity: Warning
- SLI/SLO liên quan: `quality_score_avg >= 0.75`.
- Điều kiện và thời gian duy trì: Quality score trung bình dưới 0.75 liên tục 10 phút.
- Ảnh hưởng tới người dùng: Câu trả lời kém liên quan hoặc không bám retrieved context.
- Ba bước kiểm tra đầu tiên: (1) xác nhận quality panel và feature bị ảnh hưởng; (2) so sánh trace theo prompt version; (3) kiểm tra retrieved docs và prompt metadata.
- Mitigation tạm thời: Rollback label `production` về prompt baseline đã biết ổn định.
- Owner: Đặng Quang Trung (`2A202601510`).
