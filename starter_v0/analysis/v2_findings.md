# V2 — Team eval, unit test và xác nhận Telegram

## Mục tiêu theo ảnh

Đủ 10 eval case (5 đơn lượt, 5 nhiều lượt), hoàn thiện unit test, chạy v2 thật và thêm v2 vào UI. Không đổi bộ base cố định.

## Một giả thuyết

Thay quy tắc gửi ngay bằng quy tắc xác nhận rõ nội dung/đích gửi trước khi đăng Telegram sẽ ngăn model gọi send quá sớm. Chỉ thay một đoạn prompt; giữ nguyên các đoạn khác và toàn bộ schema tool từ v1 đầy đủ, gồm deduplicate_sources.

Đã đo lại v1 với bộ tool đầy đủ để có đối chứng cùng hash tools. Không sửa prompt thêm sau khi nhìn kết quả v2.

## Kết quả API thật

Provider/model: OpenRouter / openai/gpt-4o-mini.

| Chỉ số | v1 đối chứng, tool đầy đủ | v2 base | v2 group |
|---|---:|---:|---:|
| Ca đạt | 19/20 (95%) | 19/20 (95%) | 7/10 (70%) |
| Tool routing | 95% | 100% | 90% |
| Arguments | 95% | 95% | 70% |
| Multiturn | 100% | 100% | 80% |
| Provider error | 0 | 0 | 0 |

Run đối chứng: `runs/v1_B_base_openrouter_20261110T124914625947.json`.

Run v2 base: `runs/v2_B_base_openrouter_20261110T124933086465.json`.

Run v2 group: `runs/v2_B_group_openrouter_20261110T124906050495.json`.

**R12:** v1 gọi send trước khi hỏi; v2 gọi clarify và hỏi nội dung bản tin bằng response_type=text. Routing đã đúng và không gửi ngay, nhưng rubric yêu cầu yes_no nên vẫn FAIL về tham số. Vì request chưa có nội dung bản tin, việc hỏi nội dung có ý nghĩa thực tế; cần đánh giá thủ công cùng tiêu chí xác nhận, không đổi rubric để tăng điểm. Các ca G02/G06 có bản nháp rõ ràng đều hỏi xác nhận yes_no và PASS.

Case accuracy base không tăng. Kết quả hỗ trợ cải thiện ranh giới hành động, chưa chứng minh v2 đạt toàn bộ tiêu chí. Chỉ chạy một lần mỗi cấu hình, chưa đo độ ổn định qua nhiều lần lặp. Các ca no_tool như R08/R14 vẫn cần kiểm tra ngữ nghĩa refuse, vì bộ chấm chỉ kiểm tra việc không gọi tool.

## 10 team eval case

| ID | Loại | Kiểm tra | Kết quả |
|---|---|---|---|
| G01 | Đơn lượt | Lọc nguồn trùng đã cung cấp | PASS |
| G02 | Đơn lượt | Hỏi xác nhận bản nháp Telegram | PASS |
| G03 | Đơn lượt | Hỏi URL thiếu | FAIL: gọi đúng clarify nhưng thiếu response_type trong args |
| G04 | Đơn lượt | Hỏi tài khoản thiếu | PASS |
| G05 | Đơn lượt | Tin robotics tuần qua | FAIL: thiếu topic=news |
| G06 | Nhiều lượt | Đổi bản nháp phải hỏi xác nhận lại | PASS |
| G07 | Nhiều lượt | Sửa tài khoản và số tweet | PASS |
| G08 | Nhiều lượt | Cung cấp URL sau khi hỏi lại | PASS |
| G09 | Nhiều lượt | Lọc nguồn từ ngữ cảnh | PASS |
| G10 | Nhiều lượt | Đổi timeframe, giữ chủ đề và số lượng | FAIL: gọi lookup hai lần, một lần thừa với topic=general |

G03 khi chạy thực tế nhận mặc định text từ hàm clarify, nhưng bộ chấm kiểm tra args model gửi nên vẫn FAIL. Không coi lỗi này đồng nghĩa với việc hỏi sai câu hỏi. G05/G10 cần quy định tham số và tránh gọi tool dư ở vòng sau.

Dataset: `data/eval_group.json`; bản lưu tại `artifacts/versions/v2/eval_group.json`. G01 được giữ nguyên, thêm 9 ca mới. Không so 7/10 với run group v1 cũ 1/1 như cùng một dataset.

## Unit test

`python -m pytest -q`: **115 passed, 0 failed, 0 skipped**.

Hoàn thiện 14 stub: clarify, format (nhóm/đánh số/rỗng), Telegram (mock HTTP, không gửi thật), lookup timeframe=None, fetch mapping/truncation, timeline limit/id, social_search search_type và policy (lọc nhóm, rỗng, tách prompt injection).

Thêm kiểm tra dataset đủ 5+5, v2 chỉ đổi một đoạn và giữ tools hash; UI dùng đúng prompt/hash v2. Test offline không gọi model/API thật. Các run eval trên là các phép kiểm tra model riêng.

## UI và tái lập

UI có v0, v1, v2; mặc định v2. Có bảng điểm base và số ca đạt group, chọn suite base/group để lấy lệnh chạy. Chat v2 dùng prompt và tool từ snapshot; tool gửi Telegram tiếp tục bị tắt trong UI.

```powershell
python -m streamlit run app.py --server.address 127.0.0.1
python run_eval.py --provider openrouter --version v2 --suite base --eval-cases data/eval_base.json --system-prompt artifacts/versions/v2/system_prompt.md --tools artifacts/versions/v2/tools.yaml
python run_eval.py --provider openrouter --version v2 --suite group --eval-cases artifacts/versions/v2/eval_group.json --system-prompt artifacts/versions/v2/system_prompt.md --tools artifacts/versions/v2/tools.yaml
```

Prompt hiện tại `artifacts/system_prompt.md` đã là v2. Snapshot v0/v1 và log cũ giữ nguyên. Kết quả và hash được ghi trong `artifacts/version_log.csv`; bảng phân tích chung ở `analysis/base_runs.csv`. Chưa chạy v3 hoặc triển khai public.
