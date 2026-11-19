Release: lab250_5051888ec7d5_v2
Parent: lab250_5051888ec7d5
Số ảnh: 240
Số nhãn: 1633
Guideline: v1.2 (J01-J03), v1.3 (J04-J10)
QC v1: 19/250 = 7,6%
Kết luận v1: Hold — 19/250 ảnh/cảnh lỗi = 7,6% > 2% nên không Release
Kết luận v2: Release — đã tách 10 ảnh lỗi nhãn detection sang rework_queue, sửa split/hash/guideline trong v2; ảnh lỗi panoptic ở lại (nhãn detection đúng)
Ghi chú: 
- Split: cảnh scene_541 có ảnh 000000018737 nằm ở train trong khi các ảnh còn lại của cảnh nằm ở val (rò train/val). v2 đưa 000000018737 về val để cả cảnh một split; chỉ đổi cột split trong truyvet.csv, không sửa ảnh hay nhãn.
- Hash: 000000006763 có sha256 trong manifest v1 không khớp file. Nhóm đã mở ảnh: mở được, 375x500 RGB, nội dung bình thường (hai người trong quán). Ảnh còn nguyên nên giữ trong v2, manifest.csv của v2 ghi hash tính lại từ bytes của file.
- Guideline: 000000001818 và 000000011699 ghi sai phiên bản guideline ở metadata ảnh. v2 lấy phiên bản theo job trong jobs.csv (v1.2 cho J01-J03, v1.3 cho J04-J10) và ghi vào truyvet.csv.
- Rework: 10 ảnh lỗi nhãn detection được tách khỏi v2 và đưa vào rework_queue.csv, giao lại đúng người gán/người kiểm của job theo jobs.csv. A01/Q01: 000000001000 (thiếu box người phụ nữ đứng sau cậu bé). A01/Q02: 000000025424 (class id ngoài 0-79). A02/Q01: 000000018380 (box tràn mép ảnh). A02/Q02: 000000013004 (class id ngoài 0-79), 000000013201 (box ván trượt lệch trái), 000000015338 (thiếu box xe buýt). A03/Q01: 000000005477 (box lặp), 000000007386 (box xe máy lệch, hở bánh sau). A04/Q02: 000000021503 (chuột máy tính bị gán knife), 000000023023 (box túi xách lệch phải).
- Panoptic: 5 ảnh chỉ lỗi ở panoptic nên nhãn detection vẫn đúng, ảnh ở lại v2. Báo team panoptic sửa: 000000007977 và 000000017436 (thing_overlap, area khai lớn hơn số pixel thật), 000000017714 (hai cái nĩa bị gộp một segment), 000000022969 (hai con hươu bị gộp một segment), 000000018575 (đĩa thức ăn bị ghi cup thay vì bowl).
- Kết quả v2: 240/250 ảnh, 1633 nhãn, đã sửa split/hash/guideline; 10 ảnh chờ gán lại sẽ vào lô sau khi rework xong. Model R-021 đã train trên v1 phải được xem lại hoặc train lại vì v1 có 7,6% ảnh lỗi.