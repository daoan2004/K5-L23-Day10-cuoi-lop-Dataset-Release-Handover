# Dùng AI

| # | Ai dùng | Công cụ | Prompt (tóm tắt) | AI sai ở đâu | Nhóm kiểm lại thế nào |
|---|---|---|---|---|---|
| 1 | Đinh Hữu Thái An | Claude | Đọc repo nhóm, viết `validator/crosscheck.py` thành cửa ngõ gọi `validate.cross_check` và soạn REPORT mục 1–2 cho phần đối chiếu | Lần đầu tính lại số ứng viên lô sạch là không thể (không có dữ liệu trong môi trường của AI), nên AI không được điền số này | Chạy lại lệnh trên `runs/clean` và `runs/r2207`, chép số thật vào REPORT; đối chiếu số lỗi/ứng viên với `errors.json`, `candidates.json` |
