# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: VibeCode
- Members:
- Provider/model: xkiro / mistralai/mistral-large-2512

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Lab là trợ lý nghiên cứu tìm tin trên web, tìm bài mạng xã hội, đọc URL và tổng hợp thông tin có nguồn. Giao diện Streamlit giữ lịch sử hội thoại để người dùng bổ sung tài khoản hoặc URL khi agent hỏi lại; hiện là bản thử nghiệm v0/v1.

**Link dùng thử (deploy):**

Local: http://localhost:8501 (chỉ dùng trên máy chạy app). Chưa triển khai link public.

Khởi chạy: `.\.venv\Scripts\python.exe -m streamlit run app.py` trong `starter_v0`.
Hướng dẫn: `UI-README.md`. Telegram tắt trong UI; eval base vẫn giữ khai báo send để kiểm tra hành vi xác nhận.

## A2. Tool agent có

> Liệt kê các tool agent đang dùng (gồm tool mới nhóm tự thêm). Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin | không |
| timeline | lấy bài gần đây của một tài khoản X | không |
| social_search | tìm bài X theo từ khóa | không |
| lookup | tìm thông tin/tin tức web qua Tavily | không |
| fetch | đọc nội dung URL qua Firecrawl | không |
| format | trình bày dữ liệu đã có thành digest | không |
| policy | tìm trong bộ chính sách giả lập nội bộ | không |
| papers | tìm paper arXiv | không |
| paper_text | tải và trích nội dung paper arXiv | không |

Tool mới tự viết: chưa thực hiện ở mốc v1. Các tool bonus arXiv chưa được kiểm thử live trong công việc này.

## A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1. Tin AI hôm nay có gì nổi bật?
2. Lấy 3 tweet mới nhất của @sama.
3. Tóm tắt bài viết này giúp mình. (Sau câu hỏi của agent, bổ sung URL.)
4. Tìm các bài đăng về AI trên X.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Điểm lấy từ run JSON thật; metric trước/sau là case_accuracy.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Đo starter | — | 65.00% | `runs/v0_B_base_xkiro_20261110T103347177059.json` |
| v1 | system_prompt.md | Hỏi clarify thay vì tự đoán khi thiếu tài khoản hoặc URL sẽ sửa R10/R11. | 65% | 72.22% | `runs/v1_B_base_xkiro_20261110T104702359334.json` |
| v2 | Chưa thực hiện | | | | |
| v3 | Chưa thực hiện | | | | |

| Version | Passed / total | Measured cases | Provider errors | Routing | Arguments | Multiturn |
|---|---|---:|---:|---:|---:|---:|
| v0 | 13/20 | 20 | 0 | 85.00% | 65.00% | 66.67% |
| v1 | 13/20 | 18 | 2 | 88.89% | 72.22% | 50.00% |

case_accuracy loại provider_error khỏi mẫu số. Không kết luận tăng chất lượng chỉ từ điểm này khi số measured_cases khác nhau.

## B2. Failure Analysis

Phân tích baseline v0. Nhãn case khác lỗi quan sát ở R03/R13: tool đúng, query không khớp bộ chấm.

| Case ID | Observed mismatch | Actual Tool Calls | What Failed | Fix hypothesis |
|---|---|---|---|---|
| R03 | wrong_arg_value | lookup | query chứa cả câu/ngày; bộ chấm mong AI | Mô tả query là từ khóa, thời gian ở timeframe |
| R10 | missing_tool_call | timeline(screenname=Sam Altman) | Tự đoán tài khoản thay vì hỏi | v1: clarify khi thiếu tài khoản |
| R11 | missing_tool_call | fetch(url=https://vnexpress.net) | Tự đoán URL | v1: clarify khi thiếu URL |
| R12 | missing_tool_call | Tên tool không hợp lệ; args lồng send | Không gọi clarify yes_no; giả lập đồng ý khi hết giờ | Vòng sau: xác nhận rõ ràng, không coi im lặng là đồng ý |
| R13 | wrong_arg_value | lookup + social_search | Gọi đủ tool nhưng query của lookup không khớp AI | Quy ước query |
| M02 | wrong_arg_value | lookup | timeframe đúng; query không khớp robotics | Quy ước query |
| M03 | wrong_arg_value | timeline(screenname=Andrej Karpathy, limit=3) | Dùng tên người thay vì handle karpathy | Mô tả handle và quy tắc ánh xạ/hỏi lại |

provider_error_cases=0 không chứng minh mọi API tool thành công: v0 có tool timeline trả JSONDecodeError. Cần kiểm tra tool_results riêng.

v1 so với v0: cải thiện R13_parallel_web_and_tweets, M02_carryover_timeframe; hồi quy M05_correction_limit, M06_switch_tool.

Mỗi phiên bản mới chạy một lần; biến động ngoài R10/R11 chưa đủ để kết luận do thay đổi prompt.

Kết luận v1: giả thuyết hỏi lại chưa được chứng minh. R10 không trả tool call; R11 lỗi API 409 duplicate request; R12 lỗi TypeError ở đường gọi provider. Vẫn 13/20 case đúng, multiturn giảm từ 66,67% xuống 50%. Cần xử lý/kiểm tra lại lỗi provider và cải tiến hướng dẫn clarify trong vòng tiếp theo.

## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
|  |  |  |  |

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) |  |  |  |
| arXiv/company policy |  |  |  |
| UI (bắt buộc theo Scope) | `app.py`, `analysis/ui_validation.md` | Streamlit, giữ ngữ cảnh, chọn v0/v1, lưu/tải transcript; health check HTTP 200 | Local, chưa public; send bị chặn |
| Tool unit tests (`tests/`) | `analysis/ui_validation.md` | 65 passed, 17 skipped; gồm 3 test UI mới | 17 TODO chưa hoàn thành; chưa có tool mới |

Tool unit tests: số test đã viết, số bug tìm được trong tool có sẵn (nếu có), và một ví dụ lỗi mà unit test bắt được nhưng eval không bắt được.

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
- Which fixes belonged in `tools.yaml`?
- Which failure needed manual review instead of automatic grading?
- What would you improve next?

## B7. Small Local Model Challenge (bonus)

Only fill if your team did the local model challenge.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | (cloud) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v4-local |  |  |  |  |  |  |  |
| v5-local |  |  |  |  |  |  |  |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern | Count | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool |  |  |  |  |
| invalid JSON args (`_invalid_json_arguments`) |  |  |  |  |
| no tool call / answered directly |  |  |  |  |
| missed `clarify` |  |  |  |  |
| repeated / unnecessary calls |  |  |  |  |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?
