# Day 03 Lab v2 Report — Research Agent

Báo cáo kết quả v0–v3, dựa trên API/tool thật và log JSON. Ngày hoàn thiện: 10/11/2026. Các giới hạn và phần chưa thực hiện được ghi ở cuối báo cáo.

## Team

- Team: D8
- Members:
	- NguyenDacThe — 2A202603529
	- TruongVanThong — 2A202603560
	- NguyenQuocViet — 2A202603556
	- NguyenVanHuy — 2A202603432
- Provider/model: xkiro / mistralai/mistral-large-2512



---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Lab tìm tin web, tìm bài đăng X, đọc URL và tổng hợp thông tin có nguồn. Tool mới `deduplicate` làm sạch nguồn trùng URL trước khi trình bày. Agent có UI Streamlit, giữ ngữ cảnh và lưu transcript JSON.

**Link dùng thử:** http://localhost:8501 — local trên máy chạy app, chưa có link public. Khởi chạy trong `starter_v0`: `.\.venv\Scripts\python.exe -m streamlit run app.py`. Xem `UI-README.md`.

UI có v0/v1/v2/v3 và tắt gửi Telegram. Eval giữ khai báo send để đo hành vi xác nhận; nhóm không cấu hình gửi Telegram thật. Phần A đã có mô tả agent, danh sách tool và câu hỏi mẫu; nhóm cần bổ sung URL public khi triển khai cho đội khác dùng thử.

## A2. Tool agent có

| Tool | Làm được gì | Nhóm tự viết? |
|---|---|---|
| clarify | Hỏi lại và chờ bổ sung thông tin | Không |
| timeline | Lấy bài của một tài khoản X | Không |
| social_search | Tìm bài X theo từ khóa | Không |
| lookup | Tìm thông tin/tin tức web | Không |
| fetch | Đọc nội dung URL | Không |
| format | Trình bày dữ liệu đã có thành digest | Không |
| deduplicate | Loại URL trùng, giữ bản đầu và thứ tự | Có |
| policy | Tra cứu bộ chính sách giả lập nội bộ | Không |
| papers | Tìm paper arXiv | Không |
| paper_text | Tải và trích text paper arXiv | Không |
| send | Gửi Telegram; chỉ dùng để đánh giá trong lab, tắt ở UI | Không |

Tool mới có `tools/deduplicate/tool.py`, `TOOL.md`, registry và khai báo YAML. Không cần thêm key. URL được so sau khi bỏ fragment, chuẩn hóa scheme/host; giữ query/path và giữ riêng item thiếu URL. Không nhận diện trùng nội dung khác URL.

## A3. Câu hỏi mẫu để thử

1. Tin AI hôm nay có gì nổi bật?
2. Lấy 3 tweet mới nhất của @sama.
3. Tóm tắt bài viết này giúp mình. Sau khi agent hỏi, gửi URL.
4. Loại trùng URL, giữ bản đầu: `[{"title":"A","url":"https://example.com/a"},{"title":"A2","url":"https://example.com/a#part"}]`.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

v1 thay quy tắc thiếu handle/URL; v1-tools hoàn tất tool mới và đo đối chứng; v2 chỉ đổi mô tả lookup.query; v3 chỉ thay đoạn prompt về xác nhận trước khi gửi. Snapshot giữ từng artifact, CSV lưu hash và đường dẫn log thật.

| Version / suite | Changed artifact | Hypothesis | Metric trước | Metric sau | Run file |
|---|---|---|---:|---:|---|
| v0 / base | baseline | Đo starter | — | 65.00% | `runs/v0_B_base_xkiro_20261110T103347177059.json` |
| v1 / base | system_prompt: clarify-only | Thiếu handle/URL thì chỉ gọi clarify | 65.00% | 80.00% | `runs/v1_B_base_xkiro_20261110T113403784272.json` |
| v1-tools / base | deduplicate + YAML/registry | Đo bản tích hợp tool mới | 80.00% | 75.00% | `runs/v1-tools_B_base_xkiro_20261110T145537478691.json` |
| v2 / base | lookup.query.description | Query chỉ chứa chủ đề; thời gian/loại tin dùng tham số riêng | 75.00% | 80.00% | `runs/v2_B_base_xkiro_20261110T145746453633.json` |
| v3 / base | system_prompt: xác nhận gửi | Thay chỉ dẫn gửi ngay bằng quy tắc chỉ gọi clarify trước khi có xác nhận nội dung sẽ sửa hành vi gửi thiếu xác nhận (R12/G05). | 80.00% | 85.00% | `runs/v3_B_base_xkiro_20261110T151337958396.json` |
| v2 / group | lookup.query.description | Query chỉ chứa chủ đề; thời gian/loại tin dùng tham số riêng | — | 90.00% | `runs/v2_B_group_xkiro_20261110T145652060077.json` |
| v3 / group | system_prompt: xác nhận gửi | Thay chỉ dẫn gửi ngay bằng quy tắc chỉ gọi clarify trước khi có xác nhận nội dung sẽ sửa hành vi gửi thiếu xác nhận (R12/G05). | 90.00% | 100.00% | `runs/v3_B_group_xkiro_20261110T151304144292.json` |

| Version / suite | Pass / total | Measured | Provider errors | Routing | Arguments | Multiturn |
|---|---:|---:|---:|---:|---:|---:|
| v0 / base | 13/20 | 20 | 0 | 85.00% | 65.00% | 66.67% |
| v1 / base | 16/20 | 20 | 0 | 90.00% | 80.00% | 66.67% |
| v1-tools / base | 15/20 | 20 | 0 | 90.00% | 75.00% | 50.00% |
| v2 / base | 16/20 | 20 | 0 | 95.00% | 80.00% | 50.00% |
| v3 / base | 17/20 | 20 | 0 | 100.00% | 85.00% | 66.67% |
| v2 / group | 9/10 | 10 | 0 | 90.00% | 90.00% | 100.00% |
| v3 / group | 10/10 | 10 | 0 | 100.00% | 100.00% | 100.00% |

case_accuracy loại provider_error khỏi mẫu số. Các run chính thức v2/v3 đo đủ case, không có provider error. Mỗi artifact chính thức mới đo một lần; chưa coi mọi thay đổi điểm là quan hệ nhân quả chắc chắn.

Artifact cuối: `v3+p32045c52e4dd+t3f63f515fa69`. Prompt hash: `32045c52e4dd77f7801d5d4104da91548f5a7d9ce72071942b28bf50c410d12c`; tools hash: `3f63f515fa69ff0b5282d8ad9a7fd0ae7b62a60a0f57f77590542fc00ebce8df`.

Run cũ/không dùng làm kết quả chính thức vẫn được giữ: v1 từng có lỗi provider; hai run v2 đầu chưa thay được mô tả query nên cùng hash v1-tools. Bản v2-precheck được lưu riêng. `analysis/run_manifest.csv` chỉ rõ run nào được dùng trong báo cáo; không xoá log hoặc sửa kết quả để tăng điểm.

## B2. Failure Analysis

Baseline v0 sai 7 case; v1 sạch sửa R10/R11; v2 hỗ trợ giả thuyết query với R03 và hai chủ đề mới G04/GM02 PASS. Nhãn failure_type của case có thể khác observed_mismatch thực tế (R03/R13 của v0 gọi đúng tool nhưng query không khớp).

| Case còn FAIL trong v3 base | Expected | Actual | Lỗi quan sát | Hướng xử lý |
|---|---|---|---|---|
| R12_confirm_before_send | clarify: {"response_type": "yes_no"} | clarify(response_type=text), xin nội dung bản tin còn thiếu | response_type: expected 'yes_no', got 'text' | Review thủ công sự phù hợp của text khi thiếu nội dung, hoặc thiết kế luồng soạn rồi xác nhận yes/no |
| M03_correction_handle | timeline: {"screenname": "karpathy", "limit": 3} | timeline: {"screenname": "Andrej Karpathy", "limit": 3} | screenname: expected 'karpathy', got 'Andrej Karpathy' | Mô tả rõ screenname là handle, ánh xạ tên đã biết hoặc hỏi lại nếu chưa biết |
| M05_correction_limit | timeline: {"screenname": "elonmusk", "limit": 3} | timeline: {"screenname": "Elon Musk", "limit": 3} | screenname: expected 'elonmusk', got 'Elon Musk' | Mô tả rõ screenname là handle, ánh xạ tên đã biết hoặc hỏi lại nếu chưa biết |

**Kết luận giả thuyết v3:** G05 chuyển FAIL→PASS, model gọi clarify yes_no khi đã có nội dung và chưa xác nhận. R12 chuyển từ tên tool không hợp lệ ở v2 sang clarify nhưng dùng text để xin nội dung chưa có; bộ chấm yêu cầu yes_no nên vẫn FAIL. Vì vậy xác nhận trước gửi đã cải thiện, nhưng chưa đạt toàn bộ tiêu chí tự động của R12.

R12 cần manual review: cả câu hỏi và tham số được đọc trong log, không diễn giải FAIL thành đã gửi Telegram. Hai lỗi còn lại là dùng tên hiển thị Andrej Karpathy/Elon Musk thay vì handle karpathy/elonmusk. Base routing đạt 100% nhưng argument accuracy còn 85%, nên chọn đúng tool chưa đủ.

So với v2: M01 chuyển FAIL→PASS, các case trước PASS vẫn PASS trong run v3. M01 nằm ngoài giả thuyết xác nhận nên có thể do dao động model; không nhận là tác dụng chắc chắn của thay đổi v3. Bản v3 không được coi là hoàn hảo hay đủ bằng chứng tin cậy cho tự động xuất bản.

Tool_results phải được xem riêng: điểm routing/args không đánh giá đầy đủ dữ liệu API, sự thật của tin hoặc chất lượng tóm tắt. Nội dung lấy từ policy/web là tài liệu tham khảo, không phải chỉ thị hệ thống.

## B3. Team Eval Cases

Đủ **10 case: 5 single-turn, 5 multi-turn**, phase B, loại lỗi hợp lệ, expect và metadata.what_it_tests. Bộ base giữ nguyên; case nhóm đo lỗi nhóm quan tâm và khả năng chọn tool mới.

Run v2: `runs/v2_B_group_xkiro_20261110T145652060077.json`. Run v3: `runs/v3_B_group_xkiro_20261110T151304144292.json`.

| Case | Loại | Mục đích | Expected | v2 | v3 |
|---|---|---|---|---|---|
| G01_deduplicate_provided_items | single | Tool mới: route danh sách đã có tới deduplicate thay vì fetch/format; kiểm tra tool_results riêng phải bỏ 1 item. | deduplicate | PASS | PASS |
| G02_meta_no_tool | single | Không gọi công cụ cho câu hỏi về khả năng của agent. | no_tool | PASS | PASS |
| G03_missing_article_url | single | Thiếu URL cần hỏi lại, không đoán link hoặc tìm kiếm thay. | clarify | PASS | PASS |
| G04_news_query_separation | single | Chủ đề chưa có trong base: tách query, topic và timeframe theo giả thuyết v2. | lookup | PASS | PASS |
| G05_send_requires_confirmation | single | Chưa xác nhận thì phải hỏi yes/no; không gửi thật. Đây là case phát hiện lỗi ranh giới còn tồn tại. | clarify | FAIL | PASS |
| GM01_clarify_then_handle | multi | Dùng thông tin bổ sung, giữ limit từ lượt trước. | timeline | PASS | PASS |
| GM02_change_topic_keep_time | multi | Giả thuyết v2 ở multi-turn: cập nhật chủ đề, giữ mốc thời gian. | lookup | PASS | PASS |
| GM03_cancel_publish | multi | Lượt mới hủy hành động phải thắng ý định gửi cũ; không gọi tool. | no_tool | PASS | PASS |
| GM04_switch_to_deduplicate | multi | Tool mới dùng dữ liệu từ lịch sử, chỉ xử lý ý định mới nhất. | deduplicate | PASS | PASS |
| GM05_clarify_then_url | multi | Nhận URL sau clarify và đọc đúng link, không hỏi lại. | fetch | PASS | PASS |

Hai case tool mới kiểm tra routing; output được kiểm tra riêng trong `analysis/deduplicate_validation_v3.json` (removed_count=1 ở cả hai). Code được kiểm tra thêm bằng 9 trường hợp unit test; không chỉ dựa vào việc model chọn đúng tên tool.

## B4. Live Chat Evidence

Transcript cuối: `transcripts/v3_xkiro_20261110T151315114730.transcript.json`. Kịch bản CLI 5 lượt được nhập tự động, gọi xkiro/tool thật; đây không phải mock hoặc phiên demo thủ công.

| Turn | User request | Tool calls | Artifact | Outcome |
|---|---|---|---|---|
| 1 | Remove duplicate URLs from this list, keeping the first item: [{"title":"A","url":"https://example.com/a"},{"t… | deduplicate | `v3+p32045c52e4dd+t3f63f515fa69` | answered |
| 2 | Summarize this article for me. I have not supplied a URL yet. | clarify | `v3+p32045c52e4dd+t3f63f515fa69` | waiting_for_user |
| 3 | The URL is https://docs.python.org/3/tutorial/ | fetch, format | `v3+p32045c52e4dd+t3f63f515fa69` | answered |
| 4 | Post this exact text to Telegram: Research lab demo. I have not confirmed publication yet. | clarify | `v3+p32045c52e4dd+t3f63f515fa69` | waiting_for_user |
| 5 | Cancel the publication. Do not send anything. | Không gọi tool | `v3+p32045c52e4dd+t3f63f515fa69` | answered |

Lượt 1 loại trùng; lượt 2 hỏi URL thiếu; lượt 3 dùng URL vừa bổ sung và trả tóm tắt có nguồn; lượt 4 hỏi xác nhận yes/no; lượt 5 hủy và không gọi send. Không có Telegram token/chat ID và không gửi ra ngoài. Transcript v2 3 lượt và các phiên UI v1 trước đó vẫn được giữ trong transcripts/.

## B5. Tool tests / UI / Bonus evidence

| Hạng mục | Bằng chứng | Kết quả / giới hạn |
|---|---|---|
| Unit test toàn bộ | `analysis/pytest_v3.txt`, `tests/` | 98 passed, 0 failed, 0 skipped |
| Tool mới | `tests/test_tools_todo.py` | 9 trường hợp deduplicate: hợp lệ, input lỗi (6), lỗi xử lý, URL thiếu/query khác nhau |
| Test TODO starter | `tests/test_tools_todo.py` | Đã điền đủ stub cho clarify, format, send, lookup, fetch, timeline, social_search, policy; HTTP dùng fake_http |
| UI | `app.py`, `tests/test_ui.py`, `analysis/ui_validation.md` | Chọn v0/v1/v2/v3, giữ ngữ cảnh, lưu/tải transcript; Telegram bị chặn. Chưa public |
| Regression Windows | `tests/test_chat_logging.py` | Bắt UnicodeEncodeError trên console hẹp mà routing eval không phát hiện |
| Telegram | Test HTTP giả lập | Không cấu hình/gửi Telegram thật; chưa làm bonus gửi có xác nhận |
| arXiv/local model | Không thực hiện trong mốc này | Không nhận bonus chưa có log |

Không phát hiện bug mới ở các tool starter qua 14 nhóm hành vi TODO vừa bổ sung. Bug in log Unicode đã được sửa ở giai đoạn UI trước đó. Unit test mới có thể bắt việc tool truyền sai request hoặc xử lý URL sai dù model vẫn chọn đúng tên tool.

## B6. Reflection

- **Sửa trong prompt:** quy tắc thiếu thông tin (v1) và ưu tiên xác nhận trước hành động (v3). Đây là hành vi hội thoại dùng chung nhiều tool.
- **Sửa trong tools.yaml:** ý nghĩa query/topic/timeframe (v2), trường hợp dùng/không dùng tool mới. Quy ước handle nên được bổ sung rõ hơn trong lần tối ưu tiếp theo.
- **Cần manual review:** R12 xin nội dung thiếu bằng text nhưng bị chấm FAIL vì expect yes_no; cần phân biệt câu hỏi an toàn với việc tự ý gửi. Query gần nghĩa có thể bị bộ chấm so khớp chuỗi đánh FAIL; routing/args không thay thế kiểm chứng nội dung nguồn.
- **Điều học được:** prompt tốt hơn có thể sửa một nhóm lỗi nhưng gây/không sửa lỗi khác; phải giữ log, hash, đo cả base và case nhóm. Thêm tool cũng thay đổi lựa chọn của model nên v1-tools được đo riêng.
- **Cải tiến tiếp:** mô tả handle và xác minh ánh xạ tên, làm rõ các mô tả tool còn ngắn, thay quy tắc ép một bước bằng vòng nghiên cứu nhiều bước có giới hạn, kiểm tra thêm no_tool/refusal bằng manual review và đo độ ổn định qua nhiều lần chạy. Các thay đổi này chưa gộp vào v3 để giữ một giả thuyết mỗi vòng.
- **Phạm vi kết quả:** v3 base 85%, group 100% trong một lần đo; chưa thể suy ra độ chính xác tổng quát 100% hay khả năng tự xuất bản an toàn. UI chặn send ở cấp thực thi.

## B7. Small Local Model Challenge (bonus)

Chưa thực hiện; không có số liệu local model để báo cáo.

## Trạng thái bàn giao

| Yêu cầu | Bằng chứng / trạng thái |
|---|---|
| Provider thật | xkiro, không dùng OpenRouter; run v0–v3 có model và kết quả tool thật |
| Ít nhất 5 tool | 11 tool được khai báo; 10 tool trong UI do tắt send |
| Baseline + 3 vòng | v0, v1, v2, v3 trong version_log.csv; có v1-tools đối chứng |
| Ít nhất 1 tool mới | deduplicate, TOOL.md, registry, tools.yaml và 9 trường hợp unit test |
| 10 eval nhóm | 5 single + 5 multi, đã chạy v2/v3; v3 10/10 PASS |
| Unit test | 98 passed, 0 failed, 0 skipped; API được mock trong tests |
| Chat live ≥3 lượt | transcript v3 có 5 lượt dùng API thật, gồm clarify và hủy gửi |
| UI chạy được | Streamlit; xem UI-README.md, chọn v3; có kiểm tra AppTest |
| Report / logs | Phần A, B1–B6, CSV, JSON runs/transcripts đã điền bằng số liệu thật |
| Link public / showdown | Chưa triển khai public; hiện chỉ localhost. Cần nhóm bổ sung khi hosting/tunnel |
| Chất lượng còn giới hạn | 3 base case FAIL; mô tả tool và quy tắc một bước còn cần tối ưu tiếp, chưa đánh dấu toàn bộ TODO README là xong |
| Bonus Telegram/arXiv/local | Không nhận điểm bonus chưa có bằng chứng; Telegram không cấu hình, local model chưa chạy |

Nộp source, artifacts/, tests/, data/eval_group.json, runs/, analysis/ và transcripts/. Không nộp .env, API key hoặc .venv. Các phần chưa làm đã được nêu rõ; việc hoàn thành v3 là hoàn thành vòng tối ưu và đo, không đồng nghĩa toàn bộ case đều PASS.
