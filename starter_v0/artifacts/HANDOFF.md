# Kiểm tra trước khi nộp

Đã có: v0–v3 và log; tool mới deduplicate_sources với test; 10 case nhóm; transcript demo API thật; UI Streamlit; B7 với hai model local, hai vòng tối ưu và đối chứng cloud. Kiểm thử cuối: 119 passed, không fail/skip.

## Mở UI và nhờ người khác thử

Từ thư mục `starter_v0`, chạy:

```powershell
python -m streamlit run app.py --server.address 127.0.0.1
```

Mở http://127.0.0.1:8501. Có thể nhờ người khác thử trực tiếp trên máy này. Để thử từ máy khác qua Internet, cài Cloudflare Tunnel bằng PowerShell:

```powershell
winget install --id Cloudflare.cloudflared
```

Mở Terminal mới, giữ UI đang chạy và chạy:

```powershell
cloudflared tunnel --url http://127.0.0.1:8501
```

Dùng URL `https://…trycloudflare.com` mà lệnh thực tế trả về; ghi URL vào REPORT A1. Link hết hiệu lực khi dừng tunnel. Chia sẻ với người thử trong phiên có giám sát vì thao tác chat dùng API đã cấu hình trên máy. UI hiện tắt gửi Telegram.

## Kịch bản thử chéo người thật

Nhờ người thử tự nhập, không thay bằng kết quả eval tự động:

1. “Lấy 2 bài đăng mới nhất của sama.” Kỳ vọng gọi timeline, đúng tài khoản và số lượng.
2. Mở hội thoại mới: “Tóm tắt bài viết này.” Kỳ vọng hỏi URL. Người thử bổ sung URL thật và kiểm tra agent đọc đúng bài.
3. “Tìm 3 tin AI trong tuần qua.” Sau đó: “Đổi thành trong tháng qua.” Kỳ vọng giữ chủ đề/số lượng, đổi timeframe.
4. “Chuẩn bị đăng bản tin lên Telegram.” Sau đó: “Hủy.” Kỳ vọng hỏi xác nhận, không gửi.

Sau mỗi tình huống, dùng tab **Demo & gom lỗi** để ghi cách tái hiện, kỳ vọng và thực tế (kể cả ca đạt). Transcript nằm trong `transcripts/`, phản hồi nằm trong `feedback/`. Ghi tóm tắt kết quả thực sự quan sát được vào REPORT B4/B6. Hiện chưa có phản hồi người thật; không đánh dấu hoàn thành trước khi thử.

## Nộp bài

Nộp thư mục `starter_v0` với source, requirements, tests, tools, data, artifacts, analysis, runs và transcripts. Giữ các log thất bại để thể hiện quá trình tối ưu. Không nộp `.env`, khóa API, `.venv`, cache hoặc dữ liệu tải tạm. Các metric 100% trong báo cáo chỉ mô tả run tương ứng, không bảo đảm agent luôn trả lời đúng.

Poster và phần thưởng tự viết hơn ba tool mới là tùy chọn; không thiếu so với yêu cầu bắt buộc một tool mới. Chưa có bằng chứng về thời điểm hoàn thành phần A trước deadline hoặc việc đã nộp lên hệ thống lớp.
