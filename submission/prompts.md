# Dùng AI

| # | Ai dùng | Công cụ | Prompt (tóm tắt) | AI sai ở đâu | Nhóm kiểm lại thế nào |
|---|---|---|---|---|---|
| 1 | Nguyễn Hữu Thịnh (thinkabu) | Codex | Tìm hiểu quy trình QC, điều kiện Release/Hold và đầu vào cần thiết cho truy vết ticket, lineage theo phân công. | Hướng dẫn đầu dùng seed minh họa 3007, đã đổi sang seed thật 2207 sau khi đọc TEAM.md. | Đối chiếu yêu cầu với GUIDE.md, TEAM.md, TEAM_WORKFLOW.md, mẫu trace và script lineage trong phiên hỗ trợ. |
| 2 | Nguyễn Hữu Thịnh (thinkabu) | Codex | Chẩn đoán tải panoptic bị đứng và tìm cách tiếp tục tải dữ liệu phục vụ lab. | Script tải không hiển thị tiến độ và ghi lại file .part từ đầu khi retry. Đây là đặc điểm được phát hiện khi chẩn đoán. | Codex kiểm tra dung lượng file .part, phản hồi HTTP và khả năng tải theo từng phần của máy chủ, sau đó hướng dẫn tải tiếp bằng curl. |
| 3 | Nguyễn Hữu Thịnh (thinkabu) | Codex | Triển khai công cụ truy vết, phần tài liệu được giao và ghi rõ đầu vào còn thiếu từ thành viên khác. | Bản đầu chưa giữ các tùy chọn CLI đã có trên main. Khi merge đã bổ sung tương thích --class, --old, --scenes và kiểm thử ghi đè scene. | Codex chạy 5 kiểm thử tổng hợp đạt. Trên delivery seed 2207, kết quả gồm 4 ảnh tầng A, 3 ảnh tầng B, notify A01 và Q02. Nhóm còn cần đối chiếu kết quả và trực tiếp review ảnh. |
| 4 | Nguyễn Hữu Thịnh (thinkabu) | Codex | Hỗ trợ tích hợp Git, xử lý xung đột công cụ trace và cập nhật báo cáo theo bản chung. | Hai nhánh cùng thêm trace_query.py gây add/add conflict; báo cáo local cũng xung đột với số liệu mới của nhóm. | Công cụ trace được gộp và chạy kiểm thử trước khi push. Theo yêu cầu của Thịnh, REPORT.md sau đó được khôi phục theo origin/main để dùng báo cáo chung. |

ĐANG CHỜ prompts_daoan2004.md, prompts_Bennguyen05.md, prompts_dinhhuuthaian.md và prompts_Napplee.md từ các thành viên để tổng hợp. Bảng hiện ghi nhận phần hỗ trợ cho thinkabu.

Chi tiết đóng góp kỹ thuật và các bước còn cần kiểm chứng nằm trong prompts_thinkabu.md. Các yêu cầu trong bảng là tóm tắt trao đổi thực tế với AI.
