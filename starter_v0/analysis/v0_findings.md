# Phân tích baseline v0

Baseline đạt 14/20 ca (70%), routing 75%, arguments 70%, multiturn 100%. Không có lỗi provider. Các chỉ số đo routing và tham số, không bảo đảm chất lượng câu trả lời hay thành công của mọi dịch vụ tool.

| Ca | Hành vi thực tế | Nguyên nhân và hướng sửa |
| --- | --- | --- |
| R08, R14 | Gọi `send` để trả bài toán / mã Fibonacci | Chưa quy định phạm vi nghiên cứu; `send` có mô tả quá chung. Cần từ chối yêu cầu ngoài phạm vi bằng văn bản, không gọi tool. |
| R10 | Tự chọn `timeline(screenname="sama")` | Prompt bảo đoán tài khoản. Cần `clarify(response_type="text")` khi thiếu handle. |
| R11 | Tự tạo URL `https://example.com/article` rồi gọi `fetch` | Prompt bảo đoán URL. Cần hỏi người dùng cung cấp URL thực tế. |
| R12 | Gọi `send` thay vì hỏi xác nhận | Prompt bảo gửi ngay. Cần `clarify(response_type="yes_no")` trước gửi; chỉ đặt `confirmed=true` sau xác nhận rõ ràng. Hàm gửi hiện có chốt kiểm tra `confirmed`, nên gọi tool chưa đồng nghĩa đã gửi. |
| R13 | Gọi đủ `lookup` và `social_search`, nhưng dùng `query="AI news"`, thiếu `topic="news"` | Nhãn ca là `wrong_tool`, nhưng lỗi quan sát thật là `wrong_arg_value`. Cần làm rõ query là chủ đề, topic=news cho tin tức và timeframe=day cho hôm nay. |

Prompt trong `artifacts/system_prompt.md` cố ý yêu cầu đoán dữ liệu thiếu, gửi ngay, làm một bước và chọn một tool. Đây là cấu hình baseline để thực hành tối ưu. UI giữ prompt này; riêng chat không cung cấp tool `send` và có chốt chặn nếu model tự tạo lời gọi đó. Eval vẫn dùng nguyên bộ tool và prompt gốc.

Chưa thay prompt/tools và chưa chạy v1. Lần tối ưu tiếp theo nên kiểm chứng một giả thuyết mỗi lần, bắt đầu bằng quy tắc hỏi lại khi thiếu dữ liệu, rồi chạy lại suite base để đo thay đổi.
