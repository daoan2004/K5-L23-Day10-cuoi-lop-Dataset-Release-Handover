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
- Số ứng viên trên lô sạch (`--no-faults`): <<ĐIỀN: chạy `py -X utf8 validator/validate.py runs/clean/delivery --out runs/clean/errors.json --candidates runs/clean/candidates.json` rồi chép dòng "N ứng viên">>; hàng đợi trên seed 2207: **9 ảnh** (bbox_drift 3, instance_merge 2, class_swap|category_swap 2, missing_box 2), cả 9 đều `confirmed` sau khi xem ảnh (`submission/r2207/review_log.csv`), nên 9/9 ứng viên là lỗi thật, không có ca `rejected`.
- Ngưỡng đã chọn và cách chọn (không dùng `_private`): đối chiếu bằng **pixel của mask**, không chỉ IoU bbox, vì vật bị che làm IoU bbox giảm dù box đúng. Ngưỡng mặc định trong `validate.py`: ghép cùng lớp IoU ≥ 0.3; `bbox_drift` khi dưới 95% pixel segment nằm trong box (`--drift-cov 0.95`); `class_swap|category_swap` khi IoU ≥ 0.7 mà khác lớp; `instance_merge` khi một segment chia cho 2 box cùng lớp, mỗi box ≥ 15% pixel, không box nào ≥ 85%, tổng ≥ 85%; `missing_box` khi segment ≥ 0.4% ảnh và không box cùng lớp nào phủ ≥ 70% (`--missing-cov 0.7`, chỉnh trong commit r2207). Mỗi ảnh giữ tối đa một ứng viên điểm cao nhất vì lỗi gài tối đa một lỗi/ảnh. Ngưỡng chọn dựa trên lô sạch (`runs/clean`) và các seed luyện tập, không dùng `_private/` hay COCO gốc.

## 2. Vì sao báo hết ứng viên làm F1 giảm?
F1 = 2PR/(P+R); mỗi ứng viên báo thừa là một false positive làm precision giảm, nên hạ F1 gần như bằng một lỗi bỏ sót làm recall giảm. COCO vốn lệch giữa detection và panoptic (vật bị che, crowd), nên ghép thô cho nhiều ứng viên không phải lỗi; không xem ảnh mà báo hết thì các ứng viên đó đều thành FP.

Số của nhóm trên seed 2207: tổng 19 lỗi gài (10 lỗi luật + 9 lỗi gán nhãn). Chỉ kiểm luật: TP = 10, FP = 0, FN = 9, nên P = 1, R = 10/19 = 0.53, F1 = 0.69 (khớp "khoảng 0,7" của bộ tự đo). Thêm đối chiếu với ngưỡng đã chọn và xem ảnh: hàng đợi 9 ứng viên, 9 `confirmed`, nên TP = 19, FP = 0, FN = 0 theo kết quả review (chưa đối chiếu với đáp án ẩn); nếu có ứng viên sai hoặc bỏ sót thì F1 thấp hơn 1. Nếu ghép thô và báo hết mà không xem ảnh, mỗi ứng viên thừa trừ vào precision (đề bài đo được khoảng 0,6, thấp hơn cả chỉ kiểm luật).

## 3. Quyết định và lineage
<<QC v1 a/b, kết luận, vì sao R-021 phải xem lại hoặc train lại.>>

## 4. Hash chứng minh gì, không chứng minh gì?
<<>>

## 5. Truy vết
<<Tiêu chí tầng a/b, vì sao lấy guideline theo job.>>

## 6. Bug hoặc điểm chưa rõ trong lab (nếu có)
<<>>
