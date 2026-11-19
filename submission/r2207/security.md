# Bảo mật khi làm việc — seed 2207

## 1. Ca USB khi hết giờ làm

Lô seed 2207 gồm ảnh COCO công khai cùng nhãn, thông tin job, người gán và người kiểm giả lập. Trong tình huống dữ liệu dự án thật của bài lab, tôi dừng công việc và xin người phụ trách phương án tiếp tục trên máy hoặc môi trường được cấp quyền. Việc chép lô ra USB, gửi email cá nhân hoặc chuyển cho người quen làm hộ làm mất kiểm soát nơi lưu dữ liệu và người được tiếp cận. Nếu cần làm từ xa, tôi dùng môi trường và kênh chia sẻ đã được dự án cho phép, giữ quyền truy cập theo job.

## 2. Năm việc được hoặc không được làm

- Được mở job được giao trên máy công ty bằng tài khoản cá nhân đã cấp quyền, trong phạm vi nhiệm vụ của mình.
- Không chụp màn hình dữ liệu dự án gửi người quen, vì ảnh chụp cũng chứa dữ liệu cần kiểm soát và người nhận chưa được cấp quyền.
- Không tự chép lô dữ liệu dự án ra USB. Việc chuyển dữ liệu phải dùng phương án được người phụ trách và dự án cho phép.
- Không tự dán nhãn hay ảnh thật của dự án vào chatbot bên ngoài. Với riêng COCO công khai của lab, quy tắc lớp cho phép hỏi AI và yêu cầu ghi prompt, nhưng người trong nhóm vẫn phải tự review ảnh.
- Không đưa tài khoản CVAT cho đồng nghiệp. Người cần làm việc phải được cấp tài khoản và quyền riêng để giữ truy vết thao tác.

## 3. Ca khuôn mặt có yêu cầu làm mờ

Trạng thái xử lý là **Hold + báo người phụ trách**. Khi phát hiện mặt người rõ nhưng guideline yêu cầu làm mờ, tôi ghi mã ảnh và vị trí cần xử lý vào kênh nội bộ được phép, báo reviewer và người phụ trách dữ liệu để xác nhận quy trình. Chỉ thực hiện thay đổi trên bản làm việc được giao sau khi thống nhất cách làm mờ, kiểm tra lại nhãn và phát hành bản có truy vết. Tự làm mờ hoặc xoá ảnh có thể làm thay đổi vật thể, nhãn và số liệu bàn giao mà nhóm chưa kiểm tra tác động.

Ví dụ trong lô seed 2207:
- **000000006763**: ảnh chụp cận hai người trong một quán, nhìn thẳng vào máy, khuôn mặt chiếm phần lớn nửa trên khung hình và nhìn rất rõ. Triết mở ảnh này khi kiểm lỗi wrong_hash. Ảnh vẫn nằm trong lô v2 (ảnh còn nguyên, chỉ manifest v1 ghi sai hash), nên nếu guideline yêu cầu làm mờ mặt thì ảnh này phải Hold, không phát hành, và báo người phụ trách trước khi đưa vào v2.
- **000000001000**: ảnh nhóm trẻ em và người lớn trên sân tennis, nhiều khuôn mặt trẻ em nhìn rõ. Nhóm xem ảnh này khi review lỗi missing_box. Ảnh đang ở rework_queue, nhưng khi gán lại xong cũng phải qua bước kiểm khuôn mặt trước khi phát hành; ảnh có trẻ em cần được người phụ trách xem xét kỹ hơn.

Ở cả hai ảnh, nhóm không tự làm mờ hay xoá: làm mờ đổi bytes ảnh nên đổi sha256 trong manifest, có thể che mất vật thể đã gán nhãn (person), và phải được ghi thành phiên bản mới trong lineage. Việc này do người phụ trách quyết định theo quy trình của dự án.
