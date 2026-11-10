# Research Agent — Báo cáo v0–v3 và Local Model Challenge

- Thành viên theo thư mục bài: NguyenDacThe.
- Provider/model: OpenRouter / `openai/gpt-4o-mini`.
- Phạm vi hoàn thành: baseline v0, ba vòng tối ưu v1–v3, UI Streamlit, tool mới deduplicate_sources, unit test, eval nhóm, demo API thật và Local Model Challenge v4/v5 kèm đối chiếu cloud.

# PHẦN A — Giới thiệu agent

## A1. Agent làm được gì

Tìm thông tin web và bài đăng, đọc URL, tổng hợp nguồn, tìm paper/tài liệu nội bộ. Tool mới lọc nguồn trùng trước khi trình bày bản tin.

UI chạy local tại http://localhost:8501 sau khi chạy `python -m streamlit run app.py --server.address 127.0.0.1` từ `starter_v0`. Chưa triển khai URL công khai. UI tắt gửi Telegram.

## A2. Công cụ

| Tool | Chức năng | Mới? |
|---|---|---|
| clarify | Hỏi lại và chờ thông tin | Không |
| timeline | Lấy bài đăng của tài khoản | Không |
| social_search | Tìm bài đăng theo từ khóa | Không |
| lookup | Tìm web/tin tức | Không |
| fetch | Đọc nội dung URL | Không |
| format | Trình bày dữ liệu đã có | Không |
| send | Gửi Telegram khi confirmed=true; tắt ở UI | Không |
| policy | Tìm policy nội bộ | Không |
| papers | Tìm paper arXiv | Không |
| paper_text | Trích text paper arXiv | Không |
| deduplicate_sources | Bỏ nguồn trùng URL, giữ nguồn đầu | Có |

## A3. Câu hỏi mẫu

1. Lấy 5 tweet mới nhất của tài khoản sama.
2. Tìm tin AI hôm nay trên web.
3. Tóm tắt bài viết này. (Agent cần hỏi URL.)
4. Lọc nguồn trùng trong danh sách: `[{"url":"https://example.com/a#one"},{"url":"https://example.com/a#two"}]`.

# PHẦN B — Bằng chứng

## B1. Version evidence

| Version | Thay đổi / giả thuyết | Trước | Sau | Run |
|---|---|---:|---:|---|
| v0 | Baseline | N/A | 14/20 (70%) | `runs/v0_B_base_openrouter_20261110T115913574847.json` |
| v1 | Thay một đoạn đoán thông tin bằng clarify khi thiếu handle/URL; giữ bộ tool giống v0 | 70% | 19/20 (95%) | `runs/v1_B_base_openrouter_20261110T121931544434.json` |
| v1-tool | Kiểm tra tool mới riêng với group | N/A | 1/1 | `runs/v1-tool_B_group_openrouter_20261110T122121127729.json` |
| v2 | Một đoạn prompt yêu cầu xác nhận trước khi gửi; đối chứng v1 cùng bộ tool đầy đủ | 95% base | 95% base, routing 100%; group 7/10 | `runs/v2_B_base_openrouter_20261110T124933086465.json`, `runs/v2_B_group_openrouter_20261110T124906050495.json` |
| v3 | Routing ưu tiên + mô tả tool rõ hơn, gom lỗi và demo | Base 95%, group 70% | Base 95%, group 100%, cross 8/8 | `runs/v3_B_base_openrouter_20261110T132750335091.json`, `runs/v3_B_group_openrouter_20261110T132711597898.json`, `runs/v3_B_cross_openrouter_20261110T132704827763.json` |

Hash đầy đủ và mọi lần thử nằm trong `artifacts/version_log.csv`. Snapshot trong `artifacts/versions/`. Phân tích và lệnh tái lập: [v1_findings.md](../analysis/v1_findings.md).

## B2. Failure analysis

| Ca | v0 | v1 / giới hạn |
|---|---|---|
| R10 | Đoán sama, gọi timeline | Gọi clarify text đúng |
| R11 | Bịa URL, gọi fetch | Gọi clarify text đúng |
| R12 | Gọi send trước xác nhận | Vẫn lỗi; hàm tool chặn gửi bằng needs_confirmation |
| R13 | Đủ tool, sai query/topic | Đạt ở lần v1; chưa kết luận độ ổn định |
| R08/R14 | Dùng send sai phạm vi | Không gọi tool nên PASS tự động, nhưng vẫn trả lời ngoài phạm vi; chưa đạt nghĩa refuse |

## B3. Team eval

Đã có đủ 10 case: G01–G05 đơn lượt, G06–G10 nhiều lượt. V2 đạt 7/10; lỗi G03 (thiếu response_type), G05 (thiếu topic=news), G10 (gọi lookup thừa). V3 release đạt 10/10 trên cùng bộ group. Xem [phân tích v2](../analysis/v2_findings.md) và [phân tích v3](../analysis/v3_findings.md) để đối chiếu từng ca và giới hạn chấm điểm.

## B4. Live chat

Có demo API thật 5 lượt với cấu hình v3 release: `transcripts/v3_live_demo_cf1bf41cf4214839a103b6f836dd3c4d.transcript.json`. Bao gồm format dữ liệu mẫu, hỏi thiếu handle, bổ sung handle để gọi timeline, hỏi chuẩn bị xuất bản và hủy đăng. Không gọi send. Đây là kịch bản tự động với model thật, chưa phải phản hồi của nhóm khác; hai nguồn mẫu lượt đầu là dữ liệu tổng hợp.

## B5. Kiểm tra và lỗi phát hiện

- Full suite ở v3: 119 passed, 0 skipped, 0 failed; đã hoàn thiện 14 stub challenge và thêm test UI/feedback.
- Tool mới có 11 trường hợp test trong `tests/test_tools_todo.py`.
- Phát hiện scorer không hỗ trợ danh sách object: TypeError bị gắn nhầm provider_error trong run group đầu. Đã sửa normalize_value, thêm hai regression test; chấm lại 40 kết quả base v0/v1 không đổi kết quả.
- Run lỗi giữ nguyên: `runs/v1-tool_B_group_openrouter_20261110T122008824726.json`.
- Không sửa `data/eval_base.json`; không gửi Telegram.

## B6. Nhận xét và bước tiếp

Giả thuyết hỏi lại được hỗ trợ bởi R10/R11 và không có regression ở các ca PASS của v0. Một lần đo không đủ chứng minh ổn định hoặc quy mọi cải thiện phụ cho cùng một nguyên nhân. Bộ chấm no_tool chưa kiểm chứng ngữ nghĩa refuse.

V2 đã kiểm chứng riêng quy tắc xác nhận: R12 chuyển từ send sang clarify text, đúng routing nhưng chưa đạt response_type=yes_no theo rubric. G02/G06 có bản nháp rõ đều hỏi yes_no. Case accuracy base vẫn 95%, routing tăng lên 100%. Các lỗi này được dùng làm đầu vào cho vòng v3 đã hoàn thành bên dưới.

Chi tiết v2, log đối chứng cùng bộ tool và lệnh tái lập: [v2_findings.md](../analysis/v2_findings.md).

V3 đã thực hiện ba ứng viên và giữ toàn bộ log. Release đạt base 19/20, group 10/10, cross 8/8. R12/G03/G05/G10 được cải thiện, nhưng M06 còn gọi social thừa (regression so với v2); R08/R14 vẫn chưa từ chối ổn định mặc dù PASS no_tool. Cross đã tái dùng qua các ứng viên, không còn holdout độc lập. Xem [v3_findings.md](../analysis/v3_findings.md).

UI có v0–v3 và tab Demo & gom lỗi để lưu phản hồi kèm hash. Chưa có thử chéo người thật hoặc URL công khai. Không coi phần chuẩn bị form là bằng chứng đã nhận phản hồi thực tế.

## B7. Local model challenge

Đã chạy hai model local qua Ollama, cùng base suite 20 case và tools v3 release. Hai vòng tối ưu chỉ chạy trên Qwen; chưa đánh giá v4/v5 trên Llama.

| Prompt | Model | Passed | Accuracy | Multiturn |
|---|---|---:|---:|---:|
| v3 release | GPT-4o-mini (cloud) | 19/20 | 95% | 83.33% |
| v3 release | Qwen2.5 7B | 15/20 | 75% | 100% |
| v3 release | Llama3.2 3B | 7/20 | 35% | 16.67% |
| v4-local: shorter prompt | Qwen2.5 7B | 11/20 | 55% | 66.67% |
| v5-local: restore v3 + routing examples | Qwen2.5 7B | 16/20 | 80% | 100% |
| v5-local: cloud cross-check | GPT-4o-mini (cloud) | 20/20 | 100% | 100% |

V4 rút gọn prompt làm accuracy giảm 20 điểm phần trăm so với v3 Qwen. V5 quay về v3 và thêm ví dụ routing: accuracy tăng 5 điểm so với v3, 25 điểm so với v4. Trong các lần đo này, prompt v3 kèm ví dụ cụ thể cho kết quả tốt hơn bản rút gọn. So sánh v5 với v3 giữ nguyên tools và bổ sung ví dụ; so sánh v5 với v4 thay đổi cả cấu trúc prompt nên không thể quy toàn bộ mức tăng cho ví dụ. Cloud đối chứng không giảm điểm (95% lên 100%).

Qwen v3 lỗi R03/R06/R10/R11/R13; v5 sửa được R06/R13 nhưng phát sinh lỗi R07, còn R03/R10/R11. Routing accuracy v5 giảm từ 90% xuống 80% dù case accuracy tăng; không phải mọi metric đều cải thiện. Llama baseline có 4 wrong_tool, 4 wrong_arg_value, 3 missing_info, 1 out_of_scope và 1 wrong_boundary. Cả 5 run local/đối chứng cloud đều có 0 provider_error.

Mỗi cấu hình chỉ đo một lần; base suite đã được dùng để tối ưu, không phải holdout độc lập. PASS no_tool không chứng minh từ chối đúng ngữ nghĩa. Model local không đồng nghĩa toàn bộ agent offline: research tools vẫn có thể gọi API bên ngoài. Không sửa eval_base.json.

Prompt: `artifacts/system_prompt_v4_local.md`, `artifacts/system_prompt_v5_local.md`. Hash, metric và đường dẫn run được ghi trong `artifacts/version_log.csv`.

Bằng chứng:
- [v3-qwen7b_B_base_ollama_20261110T140550559191.json](../runs/v3-qwen7b_B_base_ollama_20261110T140550559191.json)
- [v3-llama3b_B_base_ollama_20261110T141250864270.json](../runs/v3-llama3b_B_base_ollama_20261110T141250864270.json)
- [v4-local-qwen7b_B_base_ollama_20261110T142159764022.json](../runs/v4-local-qwen7b_B_base_ollama_20261110T142159764022.json)
- [v5-local-qwen7b_B_base_ollama_20261110T143026055425.json](../runs/v5-local-qwen7b_B_base_ollama_20261110T143026055425.json)
- [v5-local-cloud_B_base_openrouter_20261110T143209231609.json](../runs/v5-local-cloud_B_base_openrouter_20261110T143209231609.json)
