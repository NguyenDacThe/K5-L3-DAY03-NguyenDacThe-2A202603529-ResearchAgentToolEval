# Chạy UI Research Lab

Mở Terminal PowerShell trong VS Code, từ thư mục gốc dự án:

```powershell
cd starter_v0
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1
```

Truy cập http://localhost:8501. Dừng server bằng Ctrl+C.

Ứng dụng đọc khóa từ `.env`, không cần nhập khóa trên giao diện. Nếu chưa có `.env`, sao chép `.env.example` thành `.env` và điền khóa thật.

- **Trò chuyện:** chọn provider/model, hỏi agent, xem tool và tải lịch sử. Transcript tự lưu trong `transcripts/`. Mỗi lượt chat có thể gọi API nhiều vòng và phát sinh phí theo nhà cung cấp.
- **Đánh giá & lỗi:** chọn run trong `runs/`, xem điểm, lọc ca lỗi, đối chiếu expected/actual và đọc phân tích baseline.
- **Công cụ:** xem khai báo từ snapshot phiên bản đang chọn.

## Chọn và tạo phiên bản

- Chọn **Phiên bản** ở thanh bên: `v0` là baseline đã chạy (14/20), `v1` gồm prompt tối ưu và tool mới. Base v1 đạt 19/20 khi đo prompt riêng; tool mới được kiểm tra group 1/1. Hai phép đo cùng thuộc v1, không tách thành phiên bản trên UI.
- Chat và danh sách tool dùng đúng snapshot đang chọn. Chuyển phiên bản/provider/model sẽ bắt đầu cuộc trò chuyện mới; transcript đã lưu vẫn còn.
- Tab **Phiên bản** có bảng tên version, bản cha, giả thuyết, điểm và hash. Điểm chỉ xuất hiện khi log khớp tên version và hai hash; không lấy điểm bản cha cho bản mới.
- Trong **Tạo version mới**, chọn bản cha, nhập tên (ví dụ `v2`), giả thuyết, chỉnh prompt/YAML rồi bấm **Tạo version**. Snapshot lưu trong `artifacts/versions/<tên>/`, kèm metadata. Không ghi đè version cũ và không gọi API khi tạo.
- Chọn bản mới ở thanh bên để chat thử. Sao chép lệnh đánh giá hiển thị trong tab Phiên bản vào Terminal để chạy eval thật; bảng tự cập nhật sau khi tải lại UI.
- UI tiếp tục tắt tool gửi Telegram. Điểm baseline là kết quả eval đã lưu với nguyên bộ tool, không phải điểm được chấm từ UI chat.

UI mặc định chọn v3 với snapshot `artifacts/versions/v3/release/`. Thanh bên có v0, v1, v2, v3. Bảng hiển thị base, group và cross riêng; chọn bộ tương ứng để lấy lệnh Terminal. V3 release đạt base 19/20, group 10/10, cross 8/8; còn lỗi M06 và giới hạn kiểm tra từ chối ngoài phạm vi. Các snapshot/log trước giữ nguyên. Chat luôn tắt gửi Telegram.

Tab **Demo & gom lỗi** có câu hỏi mẫu (bấm chạy sẽ gọi API thật), kịch bản nhờ người khác thử, lỗi eval mới nhất và form lưu cách tái hiện/kỳ vọng/thực tế vào `feedback/`. Phản hồi gắn với version/hash. Chưa có thử chéo người thật hoặc link công khai; suite cross chỉ là kiểm tra tự động. Chạy `python scripts/demo_v3.py` để tạo transcript 5 lượt demo bằng model thật, có chốt chặn thực thi send.

## Bàn giao và thử chéo

Xem [HANDOFF.md](artifacts/HANDOFF.md) để mở link dùng thử, chạy kịch bản thử chéo và thu phản hồi thật. Kết quả B7 đã có trong REPORT; giao diện vẫn mặc định dùng v3 release, các prompt v4/v5 được chạy riêng qua CLI.
