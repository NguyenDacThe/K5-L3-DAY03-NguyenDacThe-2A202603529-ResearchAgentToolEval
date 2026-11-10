# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật.

## Team

- Team: D8
- Members: NguyenVanHuy (2A202603432)
- Provider/model: openrouter / `openai/gpt-4o-mini`

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent: tìm tin theo từ khóa (web/news), tìm bài đăng theo tài khoản hoặc theo chủ đề, tìm thảo luận trên Hacker News, đọc một URL cụ thể, tìm/đọc paper arXiv, tra chính sách nội bộ công ty, tổng hợp thành digest, và gửi lên Telegram sau khi được người dùng xác nhận.

**Link dùng thử (deploy):**

> Chưa deploy public. Chạy local:
> - UI (Streamlit): `streamlit run app.py --browser.gatherUsageStats false` → http://localhost:8501 (cờ `gatherUsageStats false` để tránh lỗi ghi `~/.streamlit` khi thư mục home bị chặn quyền)
> - CLI: `python chat.py --provider openrouter --version v4` (transcript lưu trong `transcripts/`)

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin hoặc cần xác nhận trước khi ghi/gửi | không |
| timeline | lấy bài đăng gần đây của một tài khoản cụ thể (theo handle) | không |
| social_search | tìm bài đăng mạng xã hội theo chủ đề/từ khóa (Latest/Top) | không |
| lookup | tìm tin/thông tin trên web theo từ khóa (topic general/news, timeframe) | không |
| fetch | đọc nội dung của một URL cụ thể | không |
| format | trình bày các item đã thu thập thành digest (brief/sections/thread/...) | không |
| send | gửi văn bản lên Telegram (chỉ sau khi xác nhận) | không |
| policy | tra chính sách nội bộ công ty | không |
| papers | tìm bài báo khoa học trên arXiv | không |
| paper_text | lấy nội dung text của một bài báo arXiv | không |
| hn_search | tìm bài đăng/thảo luận trên Hacker News theo từ khóa (API công khai, không cần key) | **có** |

## A3. Câu hỏi mẫu để thử

1. "Tin tức AI hôm nay có gì nổi bật?" → `lookup` (news, day)
2. "Trên Hacker News mọi người đang bàn gì về Rust?" → `hn_search`
3. "Tóm tắt bài này giúp mình: https://openai.com/research/" → `fetch`
4. "Cho mình các tweet phổ biến (top) nhất về OpenAI" → `social_search` (Top)
5. "Đăng bản tin này lên Telegram giúp mình" → `clarify` (hỏi xác nhận, KHÔNG tự gửi)

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Nguồn: [version_log.csv](file:///d:/VIN-UNI/lap/DAY%203/K5-L3-DAY03-NguyenDacThe-2A202603529-ResearchAgentToolEval/starter_v0/artifacts/version_log.csv) và `runs/*.json`.

Chuỗi version được chạy lại **sạch** từ v0 gốc (khôi phục từ git HEAD); mỗi version lưu snapshot 2 file artifact vào `artifacts/versions/vN/` để tái lập 100%.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline (starter prompt + tools, khôi phục từ git) | đo baseline trước khi tối ưu | - | 0.70 | `runs/v0_B_base_openrouter_20261110T125330852244.json` |
| v1 | `versions/v1/system_prompt.md` | prompt dạng luật (hỏi trước khi đoán, xác nhận trước khi gửi, scope, routing) sẽ sửa được hành vi đoán/over-act của starter | 0.70 | 0.85 | `runs/v1_B_base_openrouter_20261110T125516916944.json` |
| v2 | `versions/v2/tools.yaml` | mô tả tool rõ "khi nào dùng / khi nào KHÔNG" + convention args sẽ giảm wrong_arg và thiếu clarify | 0.85 | 0.90 | `runs/v2_B_base_openrouter_20261110T125814703915.json` |
| v3 | `versions/v3/system_prompt.md` | luật chống fan-out + đổi nguồn giữa hội thoại + clarify-on-ambiguous sẽ sửa nốt R10 | 0.90 | 0.95 | `runs/v3_B_base_openrouter_20261110T125930458684.json` |
| v4 | `versions/v4/system_prompt.md` | luật "mọi yêu cầu gửi/đăng phải bắt đầu bằng xác nhận yes_no" sẽ sửa R12 | 0.95 | **1.00** | `runs/v4_B_base_openrouter_20261110T130118111623.json` |

Snapshot artifacts mỗi version: `artifacts/versions/v{0,1,2,3,4}/{system_prompt.md,tools.yaml}`. Artifact version của bản tốt nhất: `v4+p199bae9a8703+t32dd975693c5` (prompt hash `199bae9a8703…`, tools hash `32dd975693c5…`).

> Base suite (20 case) đạt **1.00** ở v4. Group suite (10 case nhóm tự viết) chạy ở v4 đạt **1.00** (`runs/v4_B_group_openrouter_20261110T130244996370.json`). Extension suite (policy/arXiv) chạy ở v4 đạt 0.50 — suite tuỳ chọn, chưa tối ưu (`runs/v4_B_extension_openrouter_20261110T130344386088.json`).

## B2. Failure Analysis

Lỗi thật ở v0 (6 case fail, base accuracy 0.70), lấy từ `runs/v0_...json` → `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R08_out_of_scope | out_of_scope | `send(text=...)` | trả lời toán (nguyên hàm x^2) nhưng lại gọi `send` → có tool call ngoài phạm vi | v1: thêm luật scope "câu ngoài research → trả lời trực tiếp, KHÔNG gọi tool" |
| R10_missing_handle | missing_info | `timeline(screenname="sama")` | "Tóm tắt 5 tweet mới nhất" thiếu tài khoản → đoán bừa `sama` thay vì hỏi lại | v1 + v3: luật clarify khi thiếu tài khoản, cấm đoán handle/topic |
| R11_missing_url | missing_info | `fetch(url="https://example.com/article")` | "bài viết này" không có link → bịa URL thay vì hỏi | v2: `fetch` ghi rõ "KHÔNG bịa URL — hỏi lại bằng clarify" |
| R12_confirm_before_send | wrong_boundary | `send(text=...)` | yêu cầu gửi → tự gọi `send` luôn, không hỏi xác nhận | v1 + v2: quy trình bắt buộc clarify(yes_no) trước `send` |
| R13_parallel_web_and_tweets | wrong_tool | `lookup(query="AI news", timeframe="day")` + `social_search(query="AI")` | `lookup` thiếu `topic=news` và query thừa "news" | v2: convention `lookup.topic` (news/general) + query chỉ chủ đề chính |
| R14_out_of_scope_coding | out_of_scope | `send(text="...fibonacci...")` | câu coding ngoài phạm vi → gọi `send` | v1: luật scope (như R08) |

## B3. Team Eval Cases

10 case nhóm thêm vào `data/eval_group.json` (5 single + 5 multi). Kết quả từ `runs/v4_B_group_openrouter_20261110T130244996370.json` — **10/10 PASS**.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_hn_search_routing | nhắc "Hacker News" → route đúng tool mới | `hn_search` | PASS |
| G02_send_needs_confirmation | yêu cầu đăng Telegram → phải hỏi xác nhận | `clarify` | PASS |
| G03_out_of_scope_translation | dịch thuật ngoài phạm vi → không gọi tool | no_tool (refuse) | PASS |
| G04_missing_account_ask_back | thiếu tài khoản → hỏi lại, không đoán | `clarify` | PASS |
| G05_news_timeframe_month | "tháng này" → timeframe=month, topic=news | `lookup{topic:news,timeframe:month}` | PASS |
| G06_scope_switch_twitter_to_web | đổi nguồn giữa hội thoại → chỉ gọi tool mới | `lookup` (không `timeline`) | PASS |
| G07_multiturn_send_confirmation | yêu cầu gửi ở lượt cuối → hỏi xác nhận | `clarify` | PASS |
| G08_multiturn_url_followup | lượt cuối có URL → đọc đúng link | `fetch{url:...}` | PASS |
| G09_multiturn_social_search_type | "mới nhất" → không giữ Top của lượt trước | `social_search{search_type:Latest}` | PASS |
| G10_multiturn_hn_limit | đổi chủ đề + số lượng → hn_search limit=10 | `hn_search{limit:10}` | PASS |

## B4. Live Chat Evidence

Nguồn: `transcripts/v4_openrouter_20261110T114211929612.transcript.json` (provider openrouter, model gpt-4o-mini, artifact_version `v4+p661969dae356+t32dd975693c5`).

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | "What is the latest AI news today?" | `lookup(query=AI, topic=news, timeframe=day)` | v4 | answered — trả 5 tin AI kèm nguồn |
| 2 | "What is Hacker News discussing about Rust?" | `hn_search(query=Rust, limit=5)` | v4 (tool mới) | answered — 5 thảo luận HN + link item |
| 3 | "Post this digest to Telegram for me" | `clarify(response_type=yes_no)` | v4 | waiting_for_user — hỏi xác nhận, KHÔNG tự gửi |

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `runs/v0_...json` R12; `transcripts/v4_...json` turn 3 | chỉ gửi sau khi xác nhận; `confirmed=false` → `needs_confirmation` | hệ thống chặn tự gửi; eval R12/G02/G07 kiểm tra |
| arXiv/company policy | `runs/v4_B_extension_openrouter_20261110T130344386088.json` | tool `policy`/`papers`/`paper_text` chạy được | extension suite 0.5 (chưa tối ưu) |
| UI | `app.py` (Streamlit, chạy được tại http://localhost:8501) | chat UI dùng lại đúng tool loop của `chat.py`; có guardrail hỏi xác nhận | chưa deploy public |
| Provider khác | `providers/` (openai/anthropic/gemini/ollama) | adapter đọc key riêng, kiểm key trong `complete()` | cần key riêng trong `.env` mới chạy (xem ghi chú) |
| Tool unit tests (`tests/`) | `pytest tests/` output | **84 passed, 0 skipped, 0 failed** | phủ 10 tool cũ + `hn_search` |

Tool unit tests: đã viết **17 test** (điền hết stub) + **3 test** cho tool mới `hn_search`. Ví dụ lỗi unit test bắt được mà eval không bắt: `send(confirmed=True)` khi thiếu `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` trả error dict và **không** gọi HTTP — eval không chạm tới nhánh env này. Ngoài ra `hn_search` với `query=""` phải raise → trả `{"error": "ValueError"}` chứ không được gọi mạng.

## B6. Reflection

- **Fix thuộc `system_prompt.md`**: hành vi/ranh giới — hỏi lại khi thiếu thông tin, xác nhận trước khi gửi, giữ trong phạm vi, không fan-out, tôn trọng đổi nguồn. Đây là các luật routing/boundary nên sửa ở prompt (v1, v3).
- **Fix thuộc `tools.yaml`**: convention tham số và "khi nào dùng/khi nào không" của từng tool (handle không kèm `@`, `topic`, `timeframe`, `search_type`, và boundary của `send`). Mô tả tool là hợp đồng model nhìn thấy nên thuộc tools.yaml (v2).
- **Cần review thủ công thay vì chấm tự động**: chất lượng câu trả lời tự do (trích nguồn đúng, không bịa) và việc tuân thủ injection probe trong `source-citation-policy.md` — eval chỉ chấm tool_calls + args nên không bắt được.
- **Cải thiện tiếp**: tối ưu extension suite (đang 0.5): thêm luật routing cho `policy`/`papers` và các case đa tool; thêm deploy UI public; thử Small Local Model Challenge (Ollama).

## B7. Small Local Model Challenge (bonus)

Chưa thực hiện.
