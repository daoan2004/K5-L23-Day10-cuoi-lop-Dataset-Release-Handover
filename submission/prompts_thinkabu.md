# Ghi nhận dùng AI — Nguyễn Hữu Thịnh (thinkabu)

Ngày thực hiện 19/11/2026. Công cụ hỗ trợ là Codex trong workspace của nhóm, seed luyện tập 2207.

## Phạm vi đóng góp

Phần được phân công gồm truy vết ticket của team AI, lineage, tổng hợp báo cáo và bảo mật. Tôi yêu cầu làm rõ đầu vào của từng phần, triển khai theo TEAM.md và TEAM_WORKFLOW.md, đồng thời liệt kê kết quả cần nhận từ thành viên khác. Phần truy vết có thể hoàn thành từ delivery, còn quyết định phát hành cần kết quả QC, review và gói v2.

Codex hỗ trợ đọc tài liệu, viết công cụ, tạo kiểm thử và soạn nội dung ban đầu. Các phần cần kết luận bằng mắt, số liệu thực tế và xác nhận cuối của nhóm được ghi trong công việc còn chờ.

## Các yêu cầu đã trao đổi với AI

Các mục dưới đây tóm tắt nội dung trao đổi trong phiên.

1. Giải thích mục tiêu lab, thứ tự hoàn thành và đầu ra để hiểu vị trí của truy vết và lineage trong quy trình bàn giao dataset.
2. Xác định các file và dữ liệu cần bổ sung cho ticket, lineage trước khi triển khai.
3. Chẩn đoán tải panoptic bị đứng, tìm cách xem tiến độ và tiếp tục tải khi gián đoạn.
4. Thực hiện phần việc trong TEAM.md và TEAM_WORKFLOW.md, ghi rõ phần chưa thể hoàn thành do thiếu dữ liệu hoặc kết quả từ thành viên khác.
5. Hỗ trợ chọn file commit, xử lý xung đột trace_query.py và cập nhật main. Khi báo cáo local xung đột, tôi yêu cầu dùng bản báo cáo chung của nhóm.

## Cách hoạt động của công cụ truy vết

tools/trace_query.py nối thông tin từ ticket, changelog, metadata, jobs.csv, classes.txt và nhãn detection. Ticket seed 2207 nêu lớp cup ở scene_167 và scene_502. Changelog cho biết v1.3 yêu cầu gán box cho cup bị che trên 50% hoặc cắt ở mép ảnh, còn v1.2 cho phép bỏ qua.

Phạm vi truy vết dùng guideline của job trong jobs.csv. Trường guideline_version của ảnh có thể đang bị lỗi guideline_mismatch, nên dựa vào trường này có nguy cơ chọn sai phạm vi ảnh cần kiểm tra lại.

- Tầng A gồm ảnh trong scene bị báo, thuộc job guideline cũ và có ít nhất một box detection của lớp liên quan.
- Tầng B gồm ảnh ở scene khác, cùng điều kiện về guideline của job và lớp detection.
- Notify gom annotator và reviewer của các job liên quan, loại trùng và sắp xếp để dễ đối chiếu.

Công cụ đọc đường dẫn label từ manifest và kiểm tra đường dẫn nằm trong delivery. Nếu thiếu label hoặc không xác định rõ lớp hay guideline cũ, công cụ báo lỗi để kiểm tra đầu vào. Các tùy chọn --class-name/--class, --old-guideline/--old và --scenes hỗ trợ chỉ định thông tin đã đọc từ tài liệu khi cần.

## Lineage và điều kiện tích hợp

tools/lineage_status.py đọc release ID, nhật ký train và danh sách lỗi hiện có, hiển thị trạng thái cùng lệnh ghi sự kiện bằng scripts/lineage.py. Release v1 của seed 2207 là lab250_d80d4b4b3cb2, có training run R-021 được ghi nhận trong lineage.

Theo quy ước lab, tỷ lệ QC dùng số mục lỗi trên tổng số ảnh, mỗi scene_leak tính một ảnh. Với 250 ảnh, từ 6 ảnh lỗi đã vượt ngưỡng 2% và cần HOLD. Quyết định cuối phải dựa trên errors.json đã được nhóm chốt. Sự kiện release v2 cần parent là ID v1 và được ghi sau khi gói bàn giao hoàn thiện. Nếu R-021 đã học từ lô bị HOLD, nhóm phải đánh giá lại hoặc train lại run chịu ảnh hưởng.

## Kiểm chứng trong phiên hỗ trợ

Codex đã chạy 5 kiểm thử bằng dữ liệu tổng hợp trong tests/test_trace_query.py, tất cả đều đạt.

| Tình huống | Hành vi cần bảo đảm |
|---|---|
| Guideline của ảnh khác guideline của job | Chọn phạm vi theo job và box đúng lớp |
| Thiếu file label của ảnh cần kiểm tra | Báo lỗi để xử lý đầu vào |
| Changelog không xác định rõ guideline cũ | Yêu cầu tham số tường minh |
| Đường dẫn label vượt ra ngoài delivery | Từ chối đọc đường dẫn |
| Truyền danh sách scene tường minh | Chia lại tầng A/B theo danh sách được truyền |

Lệnh chạy lại kiểm thử từ gốc repo là

```powershell
python -X utf8 -m unittest discover -s tests -p test_trace_query.py -v
```

Chạy trên delivery seed 2207 cho kết quả 4 ảnh tầng A, 3 ảnh tầng B và notify A01, Q02. Kết quả được lưu trong runs/r2207/trace.json và submission/r2207/trace.json. Đây là kết quả chạy công cụ trong phiên hỗ trợ. Thành viên còn cần đối chiếu cuối trước khi nộp.

## Những điểm đã điều chỉnh khi dùng AI

- Hướng dẫn ban đầu dùng seed minh họa 3007. Sau khi đọc TEAM.md, công cụ và tài liệu đã chuyển sang seed thật 2207.
- Khi main có công cụ trace với CLI riêng, hai nhánh phát sinh xung đột add/add. Bản gộp giữ các tùy chọn --class, --old, --scenes và bổ sung kiểm thử truyền scene tường minh.
- Báo cáo do AI soạn ban đầu có các mục đang chờ dữ liệu. Khi nhóm cập nhật báo cáo chung, tôi yêu cầu khôi phục REPORT.md theo origin/main để tiếp tục từ bản của nhóm.

## Công việc còn cần xác nhận

- Tôi cần đối chiếu từng ảnh trong trace với ticket, job và box detection, đồng thời trực tiếp review các ảnh được phân công.
- Nhóm cần cung cấp errors.json đã chốt và số đo F1 để hoàn thiện quyết định QC, lineage và báo cáo.
- Phần bảo mật cần tên ảnh có khuôn mặt rõ do thành viên trực tiếp xem và xác nhận, cùng mô tả cụ thể trước khi hoàn tất bản nộp.
- Các thành viên cần gửi prompt riêng để tổng hợp nhật ký dùng AI chung.

Khi chuẩn bị vấn đáp, tôi cần giải thích được cách nối dữ liệu qua job_id, lý do dùng guideline của job, điều kiện chia tầng A/B, ngưỡng HOLD và tác động của lô v1 đến R-021. Đây là những điểm cần tự kiểm lại cùng code và dữ liệu của nhóm.
