# Research Lab UI

Chạy trong thư mục `starter_v0` bằng PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Mở http://localhost:8501. Key, endpoint và model lấy từ `.env`:
`XKIRO_API_KEY`, `XKIRO_BASE_URL`, `XKIRO_MODEL`.

- Chọn v0/v1 ở thanh bên. Mỗi phiên bản dùng snapshot trong `artifacts/versions/`.
- Chuyển phiên bản hoặc bấm **Cuộc trò chuyện mới** sẽ bắt đầu phiên chat mới.
- Khi agent hỏi lại, nhập câu trả lời vào cùng ô chat để giữ ngữ cảnh.
- Mở **Nguồn và công cụ đã dùng** để xem tham số và kết quả thực thi.
- Transcript tự lưu trong `transcripts/ui_*.transcript.json`; có nút tải JSON.
- Telegram bị vô hiệu hóa trong UI. Bộ base eval vẫn giữ nguyên để đo hành vi xác nhận.
- UI dùng bộ tool đã loại `send`, vì vậy không dùng transcript UI để thay thế điểm base eval.

Gợi ý thử thủ công: “Tóm tắt 3 tweet mới nhất” → trả lời “@sama” khi agent hỏi → “Đổi sang 2 tweet”.
Các phiên bản thử nghiệm có thể vẫn mắc lỗi; dùng log để kiểm tra thay vì giả định kết quả đã đúng.

UI hiện chạy local, chưa có link public. Streamlit cần Python server nên không triển khai
trực tiếp lên hosting Cloudflare Worker của Sites. Nếu cần demo cho nhóm khác,
giữ Streamlit chạy và dùng hướng dẫn Cloudflare Tunnel trong README chính,
hoặc triển khai lên Streamlit Community Cloud; cấu hình secrets tại dịch vụ hosting,
không đưa `.env` lên Git.

Tham khảo giao diện chat và kiểm thử:
- https://docs.streamlit.io/develop/api-reference/chat
- https://docs.streamlit.io/develop/api-reference/app-testing
