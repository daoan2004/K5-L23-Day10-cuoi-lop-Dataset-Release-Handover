# Báo cáo nhóm CuoiLop

## 1. Số liệu luyện tập
- Kết quả Pha 1 (chỉ lỗi luật, chưa gộp review), chạy ngày 19/11/2026 bằng validator hiện tại và `score_findings.py` ở chế độ học viên:
- Chạy ngày 19/11/2026 bằng validator/validate.py và score_findings.py ở chế độ học viên, chỉ dùng lỗi luật (chưa gộp review):

  | Lô | Số lỗi luật phát hiện | F1 lỗi luật ≈ | F1 tổng ≈ |
  |---|---:|---:|---:|
  | Seed 2207 (250 ảnh) | 10 | 1.0 | 0.7 |
  | Seed 2208 (250 ảnh) | 7 | 1.0 | 0.6 |
  | Lô sạch seed 5 (50 ảnh, pool calib) | 0 | 1.0 | 1.0 |

  Seed 2207 có 10 lỗi luật: wrong_hash 1, duplicate_box 1, invalid_class 2, bbox_out_of_bounds 1, guideline_mismatch 2, scene_leak 1, thing_overlap 2. Lô sạch không báo lỗi luật nào. F1 là số làm tròn một chữ số từ bộ tự đo. F1 tổng ở bước này chưa gồm lỗi gán nhãn nên chưa phải kết quả cuối.
  F1 trên là số làm tròn một chữ số từ bộ tự đo, không khẳng định giá trị chính xác là 1.0. Hai lô luyện tập chưa có lỗi gán nhãn trong danh sách nộp nên bộ chấm hiển thị F1 gán nhãn là `—`; F1 tổng này chưa phải kết quả cuối bài. F1 lô sạch không đánh giá khả năng phát hiện lỗi gán nhãn vì lô đó không có lỗi gài.

  Lệnh tái lập cho từng run: `python validator/validate.py runs/r2207/delivery --out runs/r2207/rules.json, chép rules.json thành errors.json, rồi python scripts/score_findings.py --run runs/r2207.` 
- Số ứng viên trên lô sạch (`--no-faults`, 50 ảnh calib): **0** ở ngưỡng chuẩn cuối (missing-cov 0.7), cũng **0** ở ngưỡng chuẩn ban đầu (missing-cov 0.3) và ngưỡng lỏng (drift-cov 0.98, missing-frac 0.002, swap-iou 0.5). Chỉ ở ngưỡng cực lỏng (drift-cov 0.999, missing-frac 0.0005, missing-cov 0.9, swap-iou 0.3) mới có **1** ứng viên: missing_box ở 000000063047, là mảnh vụn của một người đứng sau bị che gần hết (87,6% pixel đã nằm trong box person có sẵn); nhóm mở ảnh và kết luận là lệch tự nhiên. Hàng đợi trên seed 2207: **9 ảnh** (bbox_drift 3, instance_merge 2, class_swap|category_swap 2, missing_box 2), cả 9 đều `confirmed` sau khi xem ảnh (`submission/r2207/review_log.csv`), không có ca `rejected`.
- Ngưỡng đã chọn và cách chọn (không dùng `_private`): đối chiếu bằng **pixel của mask**, không chỉ IoU bbox, vì vật bị che làm IoU bbox giảm dù box đúng. Ngưỡng mặc định trong `validate.py`: ghép cùng lớp IoU ≥ 0.3; `bbox_drift` khi dưới 95% pixel segment nằm trong box (`--drift-cov 0.95`); `class_swap|category_swap` khi IoU ≥ 0.7 mà khác lớp; `instance_merge` khi một segment chia cho 2 box cùng lớp, mỗi box ≥ 15% pixel, không box nào ≥ 85%, tổng ≥ 85%; `missing_box` khi segment ≥ 0.4% ảnh và không box cùng lớp nào phủ ≥ 70% (`--missing-cov 0.7`, chỉnh trong commit r2207). Mỗi ảnh giữ tối đa một ứng viên điểm cao nhất vì lỗi gài tối đa một lỗi/ảnh. Ngưỡng chọn dựa trên lô sạch (`runs/clean`) và các seed luyện tập, không dùng `_private/` hay COCO gốc. Ban đầu missing-cov là 0.3; xem ứng viên mới ở ngưỡng cực lỏng thì phát hiện 000000001000 (người phụ nữ áo tối đứng sau cậu bé mũ đỏ, không có box riêng, 37,4% pixel rơi vào box của cậu bé) là lỗi thật bị bỏ sót. Nhóm đổi lên 0.7, nằm giữa ca lỗi thật (0,374) và ca nhiễu tự nhiên duy nhất ở lô sạch (0,876); lô sạch vẫn 0 ứng viên, F1 lỗi gán nhãn từ ≈ 0.9 lên ≈ 1.0.

## 2. Vì sao báo hết ứng viên làm F1 giảm?
- F1 = 2PR/(P+R). Mỗi ứng viên báo thừa là một false positive làm precision giảm, nên F1 giảm gần như một lỗi bỏ sót làm giảm recall. Detection và panoptic của COCO vốn lệch nhau tự nhiên (vật bị che, crowd, vật nhỏ), nên nếu ghép lỏng rồi báo hết mà không xem ảnh, các ca lệch tự nhiên đều thành FP.

- Số của nhóm trên seed 2207: tổng 19 lỗi gài (10 lỗi luật + 9 lỗi gán nhãn). Chỉ kiểm luật: TP = 10, FP = 0, FN = 9, nên P = 1, R = 10/19 = 0.53, F1 = 0.69 (khớp "khoảng 0,7" của bộ tự đo). Thêm đối chiếu với ngưỡng đã chọn và xem ảnh: hàng đợi 9 ứng viên, 9 `confirmed`, nên TP = 19, FP = 0, FN = 0 theo kết quả review (chưa đối chiếu với đáp án ẩn); nếu có ứng viên sai hoặc bỏ sót thì F1 thấp hơn 1. Nếu ghép thô và báo hết mà không xem ảnh, mỗi ứng viên thừa trừ vào precision (đề bài đo được khoảng 0,6, thấp hơn cả chỉ kiểm luật).

## 3. Quyết định và lineage
QC v1 = 19/250 = 7,6%: 10 lỗi luật + 9 lỗi gán nhãn đã xác nhận; mỗi ảnh mang tối đa một lỗi, scene_leak tính là một ảnh. Vượt ngưỡng 2% (Day 7), nên Hold v1. Đã ghi lineage.py record --event decision --release-id lab250_5051888ec7d5 --decision HOLD.

lineage.py impact --release-id lab250_5051888ec7d5 cho R-021: affected=True action=review_or_retrain.

Vì sao R-021 phải xem lại hoặc train lại: R-021 đã học từ v1, trong đó 10 ảnh có nhãn detection sai (3 box lệch, 2 vật thiếu box, 1 box sai lớp, 2 class id không hợp lệ, 1 box lặp, 1 box tràn mép) và một cảnh rò train/val (scene_541) làm điểm val bị lạc quan. Sửa dataset không làm model quên những gì đã học sai, nên phải đánh giá lại R-021 và train lại trên v2 nếu ảnh hưởng đáng kể.

v2 lab250_5051888ec7d5_v2 được ghi release --parent lab250_5051888ec7d5. v1 giữ nguyên, v2 là lô con có truy vết. check_handover.py H14 PASS.

## 4. Hash chứng minh gì, không chứng minh gì?
Chứng minh:
  - File không bị thay đổi kể từ lúc lập manifest. manifest.csv của v2 có sha256 cho 480 file (240 ảnh + 240 nhãn); file .sha256 khớp zip đóng gói lại (H8, H15).
  - v1 không bị ghi đè: release_id của v1 là hash của manifest.json + metadata.json, và bộ kiểm so lại hash nhãn v1 (H1). Nhãn trong v2 trùng byte với v1 (H7), tức nhóm không sửa tay nhãn.

Không chứng minh:
  - Nhãn đúng. Ví dụ 000000007386 có hash khớp nhưng box xe máy vẫn lệch, hở bánh sau. Phải đối chiếu nguồn và xem ảnh mới biết.
  - Ảnh đúng nội dung hay hỏng. Ví dụ 000000006763 sai hash trong manifest v1 nhưng mở ra thấy ảnh còn nguyên (375×500, hai người trong quán), nên chỉ manifest ghi sai. Hash chỉ báo "khác", không nói bên nào đúng.
  - Ai tạo file, file có được phép phát hành không (ví dụ ảnh có mặt người).

## 5. Truy vết
- Ticket của team AI báo model hay bỏ sót cup bị che hoặc ở mép ảnh, thấy rõ ở scene_167 và scene_502. Changelog: v1.3 đổi quy tắc lớp cup (vật bị che trên 50% hoặc cắt ở mép vẫn phải gán box; v1.2 cho phép bỏ qua).
- Điều kiện chung: ảnh thuộc job theo guideline cũ v1.2 (J01–J03, đọc từ jobs.csv) và có ít nhất một box detection lớp cup trong labels/.
- tier_a = ảnh thoả điều kiện, nằm trong 2 cảnh bị báo: 4 ảnh (000000002592, 000000002685, 000000003845, 000000003934).
- tier_b = ảnh thoả điều kiện ở cảnh khác, chưa ai báo: 3 ảnh (000000002157, 000000002431, 000000003661).
- notify = người gán và người kiểm của các job chứa ảnh tầng a và b: A01, Q02.
- Vì sao lấy guideline theo job: guideline là phiên bản người gán dùng khi làm cả job. Phiên bản ghi ở từng ảnh có thể sai, và chính lô này có lỗi guideline_mismatch ở 000000001818 và 000000011699. Lọc theo metadata ảnh sẽ bỏ sót hoặc kéo nhầm ảnh.

## 6. Bug hoặc điểm chưa rõ trong lab (nếu có)
- Bug của validator nhóm (đã sửa): missing-cov 0.3 sót người bị che một phần (000000001000), vì một phần pixel rơi vào box của người đứng trước. Đổi lên 0.7, lô sạch vẫn 0 ứng viên (mục 1.2).
- Bug của validator nhóm (sửa trước khi dùng): bản đầu bbox_drift dùng thêm điều kiện IoU bbox thấp, nên báo nhầm vật bị che (IoU giảm nhưng pixel vẫn nằm trong box). Bỏ điều kiện IoU, chỉ dùng độ phủ pixel.
- Điểm chưa rõ trong lab: download_public.py không hiện tiến độ khi tải zip panoptic (~820 MB) và tải lại từ đầu nếu bị ngắt (file .part bị ghi đè). Nhóm chuyển sang tải trên Colab.
- Giới hạn: validator đọc mask bằng Python thuần, mất vài phút cho 250 ảnh. Với đề ẩn, nhóm chạy ngưỡng chuẩn rồi thêm một lượt ngưỡng cực lỏng để soát các ca sát ngưỡng.
