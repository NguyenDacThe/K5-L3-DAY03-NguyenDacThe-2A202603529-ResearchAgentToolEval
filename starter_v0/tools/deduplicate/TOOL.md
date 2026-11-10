---
name: deduplicate
track: core
kind: local_formatter
provider: local_python
requires_env: []
inputs: [items]
outputs: [items, item_count, removed_count]
side_effect: false
---
# deduplicate

Loại bài trùng URL trong danh sách đã có, giữ bản đầu tiên và thứ tự ban đầu.
Dùng khi người dùng yêu cầu bỏ trùng hoặc làm sạch các nguồn đã thu thập.
Không tìm kiếm, tải URL, tổng hợp nội dung, hay nhận diện hai bài khác URL có cùng ý nghĩa.

Input `items`: danh sách object (có thể rỗng), mỗi object có thể có title, url,
summary và các trường bổ sung. Không thay đổi dữ liệu đầu vào.

Chuẩn hóa để so sánh: bỏ khoảng trắng ngoài URL, bỏ fragment `#...`, viết thường
scheme/host, coi URL không có path là `/`. Giữ query string và chữ hoa/thường
trong path; không gộp HTTP với HTTPS. URL thiếu/rỗng/null được giữ riêng vì
không đủ bằng chứng trùng. URL không rỗng phải là HTTP(S) tuyệt đối, không chứa
thông tin đăng nhập. Input sai hoặc lỗi xử lý trả dict có `error`, không raise.

Ví dụ: hai item `https://example.com/a#one`, `https://example.com/a#two`
trả một item đầu tiên, `item_count=1`, `removed_count=1`.

Kiểm thử: `python -m pytest tests/test_tools_todo.py -k deduplicate -v`.
