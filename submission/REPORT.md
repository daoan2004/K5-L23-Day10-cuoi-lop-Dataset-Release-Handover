# Báo cáo nhóm <<XX>>

## 1. Số liệu luyện tập
- Kết quả Pha 1 (chỉ lỗi luật, chưa gộp review), chạy ngày 19/11/2026 bằng validator hiện tại và `score_findings.py` ở chế độ học viên:

  | Lô | Số lỗi luật phát hiện | F1 lỗi luật ≈ | F1 tổng ≈ |
  |---|---:|---:|---:|
  | Seed 2207 (250 ảnh) | 10 | 1.0 | 0.7 |
  | Seed 2208 (250 ảnh) | 7 | 1.0 | 0.6 |
  | Lô sạch seed 5 (50 ảnh, pool calib) | 0 | 1.0 | 1.0 |

  F1 trên là số làm tròn một chữ số từ bộ tự đo, không khẳng định giá trị chính xác là 1.0. Hai lô luyện tập chưa có lỗi gán nhãn trong danh sách nộp nên bộ chấm hiển thị F1 gán nhãn là `—`; F1 tổng này chưa phải kết quả cuối bài. F1 lô sạch không đánh giá khả năng phát hiện lỗi gán nhãn vì lô đó không có lỗi gài.

  Lệnh tái lập cho từng run: `py -X utf8 validator/validate.py runs/r2207/delivery --out runs/r2207/rules.json` (thay run tương ứng); khi chưa có kết quả review, dùng toàn bộ lỗi luật làm `errors.json`, sau đó chạy `py -X utf8 scripts/score_findings.py --run runs/r2207`. Không ghi đè danh sách đã gộp review để tái lập riêng Pha 1. Kết quả gốc ở `runs/<run>/rules.json`, `errors.json`, `report.md`.
- Số ứng viên trên lô sạch (`--no-faults`): <<...>>; hàng đợi trên seed luyện tập: <<... ảnh>>
- Ngưỡng đã chọn và cách chọn (không dùng `_private`): <<...>>

## 2. Vì sao báo hết ứng viên làm F1 giảm?
<<Trả lời bằng số của nhóm.>>

## 3. Quyết định và lineage
<<QC v1 a/b, kết luận, vì sao R-021 phải xem lại hoặc train lại.>>

## 4. Hash chứng minh gì, không chứng minh gì?
<<>>

## 5. Truy vết
<<Tiêu chí tầng a/b, vì sao lấy guideline theo job.>>

## 6. Bug hoặc điểm chưa rõ trong lab (nếu có)
<<>>
