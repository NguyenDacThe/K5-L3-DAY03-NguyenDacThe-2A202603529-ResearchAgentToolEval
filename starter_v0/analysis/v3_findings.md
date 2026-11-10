# V3 — Demo, kiểm tra chéo và gom lỗi

## Phạm vi

Gom lỗi v2 thành quy tắc routing/arguments rõ ràng; giữ nguyên implementation tool và hai dataset base/group. Hoàn thiện UI v3, demo API thật và nơi lưu phản hồi người thử. Không có nhóm khác tham gia thử chéo trong phiên này; suite cross là tự kiểm tra tự động, không phải phản hồi từ con người.

## Thay đổi

- Prompt có thứ tự ưu tiên: phạm vi nghiên cứu → xác nhận xuất bản → hỏi dữ liệu thiếu → chọn nguồn/tool theo trạng thái hội thoại mới nhất.
- Yêu cầu khai báo rõ response_type, topic=news, timeframe và số kết quả. Xử lý tên hiển thị/handle, cập nhật giá trị mới, tránh gọi lại tool đã hoàn thành.
- Telegram hỏi yes_no trước; nếu thiếu nội dung/đích thì chỉ hỏi ý định chuẩn bị. Không xem câu trả lời đó là duyệt gửi nội dung chưa biết. Sau khi đủ chi tiết phải xác nhận lại bản nháp cuối.
- Làm rõ mô tả clarify/lookup/social_search/send/fetch/format và quy ước tham số. clarify yêu cầu cả question và response_type trong schema.
- UI có v0/v1/v2/v3, mặc định v3; thêm điểm cross, chọn bộ cross để chạy, tab Demo & gom lỗi, form lưu phản hồi kèm version/hash. Không đổi snapshot cũ hoặc sửa log để tăng điểm.

V3 là bản sửa lỗi tích lũy với một giả thuyết chung về sự rõ ràng của routing, không phải phép đo cô lập từng rule. Vì thay cả prompt và khai báo tool, không thể quy mức cải thiện cho riêng một dòng.

## Kết quả cấu hình release

Provider/model: OpenRouter / openai/gpt-4o-mini.

| Bộ | v2 | v3 release |
|---|---:|---:|
| Base | 19/20 (95%) | 19/20 (95%) |
| Group, cùng 10 case | 7/10 (70%) | 10/10 (100%) |
| Cross tự động, 8 case mới | Chưa đo | 8/8 (100%) |

Không cộng điểm các bộ thành một chỉ số chung. Base không tăng; group tăng 30 điểm phần trăm. Base routing v3 là 95%, multiturn 83,33% (v2 tương ứng 100%, 100%): có regression M06. Group/cross routing, arguments và multiturn đều đạt 100% trong lần đo release. Không có provider error hoặc tool error trong ba log release.

- Base: `runs/v3_B_base_openrouter_20261110T132750335091.json`.
- Group: `runs/v3_B_group_openrouter_20261110T132711597898.json`.
- Cross: `runs/v3_B_cross_openrouter_20261110T132704827763.json`.
- Snapshot UI/release: `artifacts/versions/v3/release/`.

## Các lần thử trước được giữ nguyên

| Cấu hình | Base | Group | Cross |
|---|---:|---:|---:|
| Prompt ban đầu, tools v2 | 17/20 | 10/10 | 8/8 |
| Prompt làm rõ ưu tiên, tools v2 | 19/20 | 9/10 | 8/8 |
| Release: prompt ưu tiên + mô tả tool rõ hơn | 19/20 | 10/10 | 8/8 |

Snapshot đầu nằm trực tiếp trong `artifacts/versions/v3/`; lượt hai trong `final/`; release trong `release/`. Mọi run và hash đều được ghi vào `artifacts/version_log.csv`, kể cả các lượt có regression. UI chỉ lấy điểm khớp hash release hiện tại.

Suite cross đã được dùng lại qua các ứng viên, nên không còn là holdout độc lập cho release. Không tuyên bố các tỷ lệ này chứng minh tổng quát hóa hoặc độ ổn định qua nhiều lần chạy.

## Gom lỗi và giới hạn

| Ca / vấn đề | Kết quả release | Trạng thái |
|---|---|---|
| R12: kiểu hỏi xác nhận | clarify yes_no, không gửi ngay | Đạt rubric; vẫn cần đủ bản nháp/đích và duyệt cuối trước gửi |
| G03: thiếu response_type | Truyền rõ text | PASS |
| G05: thiếu topic=news | Truyền rõ news | PASS |
| G10: gọi search thừa | Không gọi thừa ở lần release | PASS, từng lỗi ở ứng viên hai |
| M03: tên hiển thị thay handle | Truyền đúng karpathy | PASS |
| M06: đã chuyển web nhưng vẫn gọi social | lookup và social_search | Còn lỗi; regression so với v2 |
| R08/R14: từ chối ngoài phạm vi | PASS no_tool, nhưng actual_text release vẫn giải bài toán/Fibonacci | Chưa sửa ổn định về ngữ nghĩa; không tính là đã xử lý đầy đủ |
| X03/X04: yêu cầu ngoài phạm vi mới | Có lời từ chối trong actual_text | Đạt ở hai câu đã kiểm tra; không phủ nhận lỗi R08/R14 |
| Thử chéo từ người khác | Chưa có phản hồi người thật | Đã chuẩn bị form và kịch bản, chưa có bằng chứng thực hiện |
| Link công khai | Chưa triển khai | Chỉ có localhost; chưa dùng được từ máy khác qua Internet |

Không sửa bộ chấm no_tool để che giới hạn ngữ nghĩa. Không dùng feedback giả làm phản hồi người thật. UI có thể tiếp tục ghi lỗi mới trong thư mục feedback/; trạng thái mặc định open.

## Demo hội thoại API thật

Transcript release: `transcripts/v3_live_demo_cf1bf41cf4214839a103b6f836dd3c4d.transcript.json`.

| Lượt | Thử gì | Tool / kết quả |
|---|---|---|
| 1 | Tổng hợp hai nguồn được cung cấp | format một lần, answered |
| 2 | Lấy tweet nhưng thiếu tài khoản | clarify text, waiting_for_user |
| 3 | Bổ sung sama, 2 tweet | timeline, answered |
| 4 | Chuẩn bị đăng nhưng thiếu chi tiết | clarify yes_no, waiting_for_user |
| 5 | Người dùng hủy đăng | answered, không gọi send |

Đây là kịch bản tự động gọi model thật, không phải hội thoại do một nhóm khác nhập. Hai nguồn ở lượt đầu là đoạn mẫu tổng hợp, không phải phát hiện nghiên cứu thật. Thực thi send bị chặn trong script demo; không gửi Telegram. Lượt hai/ba kiểm tra ngữ cảnh qua nhiều lượt và API timeline thật. Transcript lượt demo trước cũng được giữ nguyên với hash tương ứng.

## Kiểm tra và tái lập

119 unit test PASS, không fail/skip: tool contract, test tool cũ/mới, UI v3, form phản hồi, khóa bí mật được che khi lưu phản hồi. Unit test offline; tách biệt với số ca model eval.

```powershell
python -m streamlit run app.py --server.address 127.0.0.1
python run_eval.py --provider openrouter --version v3 --suite base --eval-cases data/eval_base.json --system-prompt artifacts/versions/v3/release/system_prompt.md --tools artifacts/versions/v3/release/tools.yaml
python run_eval.py --provider openrouter --version v3 --suite group --eval-cases data/eval_group.json --system-prompt artifacts/versions/v3/release/system_prompt.md --tools artifacts/versions/v3/release/tools.yaml
python run_eval.py --provider openrouter --version v3 --suite cross --eval-cases data/eval_cross.json --system-prompt artifacts/versions/v3/release/system_prompt.md --tools artifacts/versions/v3/release/tools.yaml
python scripts/demo_v3.py
```

Script demo gọi API thật; mỗi lần chạy có thể tính phí theo provider. Chưa phát hành công khai. Local Model Challenge đã hoàn thành sau mốc v3; xem REPORT B7 và version_log.csv.
