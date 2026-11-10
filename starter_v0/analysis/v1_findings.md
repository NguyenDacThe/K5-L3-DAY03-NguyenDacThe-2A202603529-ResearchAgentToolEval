# V1 — Một giả thuyết, sửa một thứ, đo lại

Theo ảnh Mốc 3/7 và README Step 2–4b: tối ưu prompt theo một giả thuyết, đo lại base và thêm một tool có tài liệu, đăng ký, unit test. Không sửa dữ liệu base hoặc đổi provider/model.

## Giả thuyết và thay đổi

Thay đoạn prompt khuyến khích đoán tài khoản/URL bằng quy tắc gọi `clarify(response_type="text")` khi thiếu dữ liệu sẽ sửa R10/R11 mà không làm hỏng các ca đã có ngữ cảnh.

Chỉ sửa một đoạn prompt. Quy tắc gửi ngay và ép một bước còn giữ nguyên để kiểm chứng ở vòng sau. Snapshot v0/v1 trong `artifacts/versions/` lưu nguyên byte; bộ tool của base v1 có cùng hash với v0: `5b22a2476d41` (tiền tố; xem hash đầy đủ trong run JSON).

Tool mới được đăng ký và đo riêng sau phép đo base, tránh lẫn ảnh hưởng của tool mới vào giả thuyết prompt.

## Kết quả thật

| Chỉ số | v0 | v1 | Chênh lệch |
|---|---:|---:|---:|
| Case accuracy | 70% (14/20) | 95% (19/20) | +25 điểm phần trăm |
| Tool routing | 75% | 95% | +20 điểm phần trăm |
| Arguments | 70% | 95% | +25 điểm phần trăm |
| Multiturn | 100% | 100% | 0 |
| Provider errors | 0 | 0 | 0 |

- Baseline đối chiếu: `runs/v0_B_base_openrouter_20261110T115913574847.json`.
- V1: `runs/v1_B_base_openrouter_20261110T121931544434.json`.
- Provider/model: OpenRouter / `openai/gpt-4o-mini`.
- R10/R11 đã hỏi lại đúng; cả 14 ca PASS của v0 vẫn PASS v1.
- R12 vẫn FAIL: gọi `send` thay vì `clarify(response_type="yes_no")`. Tool trả `needs_confirmation`; không gửi Telegram.
- R13 truyền đúng query/topic ở lần này. Chưa thể quy toàn bộ thay đổi phụ cho giả thuyết hỏi lại chỉ từ một lần chạy; chưa đo độ ổn định qua nhiều lần lặp.
- R08/R14 PASS tự động vì không gọi tool, nhưng `actual_text` vẫn trả bài toán/Fibonacci thay vì từ chối theo `behavior=refuse`. Chưa coi hai ca này là đã sửa đầy đủ về ngữ nghĩa.

## Tool mới: deduplicate_sources

Lọc nguồn trùng URL từ danh sách có sẵn, giữ bản đầu và metadata. Khi so sánh bỏ khác biệt fragment/casing host, giữ nguyên path/query. Chạy local, không API key, không mạng, không ghi file. Input lỗi trả error dict.

- Code: `tools/deduplicate_sources/tool.py`.
- Contract: `tools/deduplicate_sources/TOOL.md`.
- Registry/schema: `tools/__init__.py`, `artifacts/tools.yaml`.
- 11 trường hợp unit test trong `tests/test_tools_todo.py`: dữ liệu hợp lệ, dữ liệu sai, lỗi parser, query khác nhau và danh sách rỗng.
- G01 trong `data/eval_group.json`: PASS với model thật; 3 nguồn → 2 nguồn, bỏ 1 nguồn trùng.
- Run: `runs/v1-tool_B_group_openrouter_20261110T122121127729.json`.
- Group mới có 1 ca single-turn cho mốc v1. Chưa hoàn thành 10 ca team eval (5 single + 5 multi) của toàn bài.

## Lỗi bộ chấm được phát hiện

Run group đầu `runs/v1-tool_B_group_openrouter_20261110T122008824726.json` bị gắn `provider_error`. Nguyên nhân thực: `normalize_value` dùng `sorted(list_of_dicts)` nên phát sinh TypeError trong scorer, không phải API.

Đã sửa `run_eval.py`: chuẩn hóa object đệ quy, sắp list bằng khóa JSON ổn định; giữ cách so sánh list không phụ thuộc thứ tự. Thêm hai test hồi quy trong `tests/test_eval_structured_args.py`. Chạy lại group đạt 1/1. Chấm lại offline 40 kết quả base v0/v1 đã lưu: không thay đổi điểm hoặc mismatch nào. Giữ log lỗi ban đầu để đối chiếu.

## Kiểm tra và giới hạn

`python -m pytest -q`: 83 passed, 14 skipped. Các skip là stub challenge của tool cũ. Test tool mới, contract, UI và hồi quy scorer đều PASS. Chưa hoàn thành challenge 0 skipped; chưa chạy v2/v3.

## Chạy lại

Từ `starter_v0`:

```powershell
python run_eval.py --provider openrouter --version v1 --suite base --eval-cases data/eval_base.json --system-prompt artifacts/versions/v1/system_prompt.md --tools artifacts/versions/v1/tools.yaml
python run_eval.py --provider openrouter --version v1-tool --suite group --eval-cases data/eval_group.json --system-prompt artifacts/versions/v1-tool/system_prompt.md --tools artifacts/versions/v1-tool/tools.yaml
```

Lệnh base dùng snapshot để tái lập phép đo prompt riêng. Chạy mặc định với `artifacts/tools.yaml` sẽ bao gồm tool mới, khác cấu hình base đã đo. UI dùng prompt v1 và bộ tool có `deduplicate_sources`, vẫn tắt `send`.
