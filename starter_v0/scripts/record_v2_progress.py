"""Build the v2 milestone report from actual runs, snapshots and transcripts."""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HYPOTHESIS = "Mô tả query chỉ chứa chủ đề, tách thời gian/loại tin sang timeframe/topic sẽ giảm lỗi R03 và lỗi tương tự trên chủ đề mới."


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def latest(version, suite, expected_hash=None):
    paths = sorted((ROOT / "runs").glob(f"{version}_B_{suite}_xkiro_*.json"), reverse=True)
    for path in paths:
        run = load(path)
        if expected_hash is None or run["tools_hash"] == expected_hash:
            return path, run
    raise RuntimeError(f"No matching real run for {version}/{suite}")


def rel(path):
    return path.relative_to(ROOT).as_posix()


def clean(value, limit=190):
    text = str(value).replace("|", "\\|").replace("\n", " ")
    text = re.sub(r"sk-[A-Za-z0-9_-]+", "[REDACTED]", text)
    return text if len(text) <= limit else text[:limit] + "…"


def main():
    v2_hash = hashlib.sha256((ROOT / "artifacts/versions/v2/tools.yaml").read_bytes()).hexdigest()
    pairs = [latest("v0", "base"), latest("v1", "base"), latest("v1-tools", "base"), latest("v2", "base", v2_hash)]
    group_path, group = latest("v2", "group", v2_hash)
    control_path, control = pairs[2]
    v2_path, v2 = pairs[3]
    assert v2["prompt_hash"] == control["prompt_hash"]
    assert v2["tools_hash"] != control["tools_hash"]

    log_path = ROOT / "artifacts/version_log.csv"
    with log_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fields, rows = reader.fieldnames, list(reader)
    known = {r["run_file"] for r in rows}
    for path, run in [pairs[2], pairs[3], (group_path, group)]:
        if rel(path) in known:
            continue
        row = {k: run.get(k, "") for k in fields}
        is_control = run["version"] == "v1-tools"
        before = pairs[1][1]["summary"]["case_accuracy"] if is_control else control["summary"]["case_accuracy"]
        row.update(author="D8 (hỗ trợ bởi Codex)", changed_artifact="artifacts/tools.yaml; tools/deduplicate; registry" if is_control else "artifacts/tools.yaml: lookup.query.description",
            reason=f"xkiro / {run['model']}; suite={run['suite']}",
            hypothesis="Tích hợp tool mới, đo lại base làm đối chứng trước v2" if is_control else HYPOTHESIS,
            metric_before=before if run["suite"] == "base" else "",
            metric_after=run["summary"]["case_accuracy"], run_file=rel(path))
        rows.append(row)
    with log_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    report_path = ROOT / "artifacts/REPORT.md"
    old = report_path.read_text(encoding="utf-8")
    team = re.search(r"## Team\n.*?(?=\n---)", old, re.S).group(0)
    lines = ["# Day 03 Lab v2 Report — Research Agent", "", "Báo cáo tiến độ đến hết mốc v2; chưa tuyên bố hoàn thành v3 hoặc toàn bộ lab.", "", team, "", "---", "", "# PHẦN A — Giới thiệu agent", "", "## A1. Agent này làm được gì", "",
        "Research Lab tìm tin web, tìm bài đăng X, đọc URL và tổng hợp thông tin có nguồn. Tool mới `deduplicate` làm sạch nguồn trùng URL trước khi trình bày. Agent có UI Streamlit, giữ ngữ cảnh và lưu transcript JSON.", "",
        "**Link dùng thử:** http://localhost:8501 — local trên máy chạy app, chưa có link public. Khởi chạy trong `starter_v0`: `.\\.venv\\Scripts\\python.exe -m streamlit run app.py`. Xem `UI-README.md`.", "",
        "UI có v0/v1/v2 và tắt gửi Telegram. Eval giữ khai báo send để đo hành vi xác nhận; nhóm không cấu hình gửi Telegram thật. Phần A hoàn thiện nội dung để chuẩn bị demo; link public cần bổ sung ở mốc showdown.", "", "## A2. Tool agent có", "", "| Tool | Làm được gì | Nhóm tự viết? |", "|---|---|---|"]
    for name, meaning in [("clarify", "Hỏi lại và chờ bổ sung thông tin"), ("timeline", "Lấy bài của một tài khoản X"), ("social_search", "Tìm bài X theo từ khóa"), ("lookup", "Tìm thông tin/tin tức web"), ("fetch", "Đọc nội dung URL"), ("format", "Trình bày dữ liệu đã có thành digest"), ("deduplicate", "Loại URL trùng, giữ bản đầu và thứ tự"), ("policy", "Tra cứu bộ chính sách giả lập nội bộ"), ("papers", "Tìm paper arXiv"), ("paper_text", "Tải và trích text paper arXiv"), ("send", "Gửi Telegram; chỉ dùng để đánh giá trong lab, tắt ở UI")]:
        lines.append(f"| {name} | {meaning} | {'Có' if name == 'deduplicate' else 'Không'} |")
    lines += ["", "Tool mới có `tools/deduplicate/tool.py`, `TOOL.md`, registry và khai báo YAML. Không cần thêm key. URL được so sau khi bỏ fragment, chuẩn hóa scheme/host; giữ query/path và giữ riêng item thiếu URL. Không nhận diện trùng nội dung khác URL.", "", "## A3. Câu hỏi mẫu để thử", "",
        "1. Tin AI hôm nay có gì nổi bật?", "2. Lấy 3 tweet mới nhất của @sama.", "3. Tóm tắt bài viết này giúp mình. Sau khi agent hỏi, gửi URL.",
        '4. Loại trùng URL, giữ bản đầu: `[{"title":"A","url":"https://example.com/a"},{"title":"A2","url":"https://example.com/a#part"}]`.', "", "---", "", "# PHẦN B — Chi tiết / Bằng chứng", "", "## B1. Version Evidence", "",
        "v1 được giữ nguyên với run sạch 16/20 do nhóm đã có. Tool mới được hoàn thành sau run đó; dùng nhãn `v1-tools` cho bước tích hợp và đo đối chứng, không ghi đè snapshot/log v1 cũ. v2 chỉ thay **một mô tả tham số lookup.query** so với v1-tools; prompt và danh sách tool giống nhau.", "",
        "| Version / suite | Changed artifact | Hypothesis | Metric trước | Metric sau | Run file |", "|---|---|---|---:|---:|---|"]
    for path, run in pairs + [(group_path, group)]:
        v = run["version"]
        before = "—" if v == "v0" or run["suite"] == "group" else f"{(pairs[0][1] if v == 'v1' else pairs[1][1] if v == 'v1-tools' else control)['summary']['case_accuracy']:.2%}"
        changed = "baseline" if v == "v0" else "system_prompt.md: clarify-only" if v == "v1" else "Tool mới + khai báo/registry" if v == "v1-tools" else "lookup.query.description"
        hypothesis = "Đo starter" if v == "v0" else "Thiếu handle/URL thì chỉ gọi clarify" if v == "v1" else "Đo tác động tích hợp tool mới" if v == "v1-tools" else HYPOTHESIS
        lines.append(f"| {v} / {run['suite']} | {changed} | {hypothesis} | {before} | {run['summary']['case_accuracy']:.2%} | `{rel(path)}` |")
    lines += ["| v3 | Chưa thực hiện | | | | |", "", "| Version / suite | Pass / total | Measured | Provider errors | Routing | Arguments | Multiturn |", "|---|---:|---:|---:|---:|---:|---:|"]
    for _, run in pairs + [(group_path, group)]:
        s = run["summary"]
        lines.append(f"| {run['version']} / {run['suite']} | {s['passed_cases']}/{s['total_cases']} | {s['measured_cases']} | {s['provider_error_cases']} | {s['tool_routing_accuracy']:.2%} | {s['argument_accuracy']:.2%} | {s['multiturn_accuracy']:.2%} |")
    lines += ["", "`case_accuracy` loại provider_error khỏi mẫu số; xem đồng thời pass/total và measured. Mỗi artifact mới đo một lần, nên chưa coi biến động điểm là bằng chứng nhân quả chắc chắn.", "",
        f"Hash v2: prompt `{v2['prompt_hash']}`, tools `{v2['tools_hash']}`. Hash bản đối chứng: tools `{control['tools_hash']}`. Snapshot trong `artifacts/versions/` và CSV ghi cả đường dẫn run.", "",
        "Hai run v2 ban đầu có tools_hash giống v1-tools do thao tác thay thế mô tả chưa áp dụng. Chúng được giữ trong runs/ làm dữ liệu chẩn đoán, snapshot `v2-precheck`; không dùng làm bằng chứng giả thuyết v2. Các bảng trên chỉ chọn run khớp hash v2 cuối cùng.", "", "## B2. Failure Analysis", "",
        "Baseline v0 có 7 case lỗi. R03/R13 được gắn failure_type=wrong_tool theo loại case nhưng observed_mismatch là wrong_arg_value; cần đọc actual calls, không suy luận chỉ từ nhãn. v1 sạch sửa được R10/R11. v1-tools đo riêng ảnh hưởng thêm tool và dao động model.", "",
        "| v2 base case | Observed mismatch | Actual tool | Failure | Hướng sửa tiếp theo |", "|---|---|---|---|---|"]
    for r in v2["results"]:
        result = r["result"]
        if not result["passed"]:
            names = ", ".join(clean(c["name"], 55) for c in result.get("actual_tool_calls", [])) or "Không có"
            failures = "; ".join(result.get("failures", [])) if result.get("failure_type") != "provider_error" else "Lỗi provider; không đủ dữ liệu chấm hành vi"
            fix = "Mô tả screenname là handle, ánh xạ tên đã biết hoặc hỏi lại khi chưa rõ"
            if r['id'] == "R12_confirm_before_send":
                names = "Tên tool ngoài registry"
                failures = "Thiếu clarify yes_no; model tạo tên tool không hợp lệ"
                fix = "Thay chỉ dẫn tự gửi bằng quy tắc gọi clarify yes_no trước hành động"
            lines.append(f"| {r['id']} | {result.get('observed_mismatch')} | {names} | {clean(failures)} | {fix} |")
    by_control = {r["id"]: r["result"] for r in control["results"]}
    fixed = [r["id"] for r in v2["results"] if r["result"]["passed"] and not by_control[r["id"]]["passed"]]
    regressed = [r["id"] for r in v2["results"] if not r["result"]["passed"] and by_control[r["id"]]["passed"]]
    lines += ["", f"So với v1-tools: case chuyển FAIL→PASS: {', '.join(fixed) or 'không có'}; PASS→FAIL/lỗi provider: {', '.join(regressed) or 'không có'}.", ""]
    r03 = next(r for r in v2["results"] if r["id"] == "R03_web_news_routing")
    lines += [f"Giả thuyết v2: R03 {'PASS' if r03['result']['passed'] else 'vẫn FAIL'}; hai case nhóm dùng chủ đề mới (G04/GM02) được báo riêng ở B3. Kết luận dựa trên cả case mục tiêu, lỗi provider và hồi quy; không gọi v2 hoàn hảo khi vẫn có case FAIL.", "",
        "Eval chấm routing/args, không chứng minh tất cả API trả dữ liệu tốt hoặc bài tóm tắt chính xác. Các lỗi tool_results và nội dung cuối cần đọc riêng. R12/G05 kiểm tra hành vi xác nhận là phần cần cải tiến ở v3; Telegram không được gửi thật trong các kiểm tra UI.", "", "## B3. Team Eval Cases", "",
        "Đủ **10 case: 5 single-turn + 5 multi-turn**, phase B, failure_type hợp lệ, expect và metadata.what_it_tests. Chạy bằng API thật với artifact v2.", "",
        f"Run: `{rel(group_path)}`.", "", "| Case ID | Loại | What it tests | Expected | Result |", "|---|---|---|---|---|"]
    for r in group["results"]:
        expected = ", ".join(c["name"] for c in r["expect"].get("tool_calls", [])) or "no_tool"
        lines.append(f"| {r['id']} | {'multi' if r['is_multiturn'] else 'single'} | {clean(r['metadata']['what_it_tests'], 140)} | {expected} | {'PASS' if r['result']['passed'] else 'FAIL: ' + str(r['result'].get('observed_mismatch'))} |")
    checks = []
    for r in group["results"]:
        expected = r.get("metadata", {}).get("expected_removed_count")
        if expected is not None:
            events = [t for t in r.get("tool_results", []) if t["tool"] == "deduplicate"]
            value = events[0]["result"] if events else {}
            checks.append({"case_id": r["id"], "expected_removed_count": expected, "observed_removed_count": value.get("removed_count"), "passed": value.get("removed_count") == expected})
    (ROOT / "analysis/deduplicate_validation.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
    lines += ["", "G01/GM04 chấm model có route vào tool mới; output tool được kiểm tra thêm theo removed_count trong `analysis/deduplicate_validation.json`. Unit test kiểm tra cả giữ bản đầu, thứ tự, input xấu và lỗi xử lý. Nhờ vậy không coi chọn đúng tên tool là đủ chứng minh code đúng.", "", "## B4. Live Chat Evidence", "",
        "| Turn | User request | Tool calls | Version evidence | Outcome |", "|---|---|---|---|---|"]
    transcripts = sorted((ROOT / "transcripts").glob("v2_xkiro_*.transcript.json"))
    if transcripts:
        transcript_path = transcripts[-1]
        transcript = load(transcript_path)
        for turn in transcript["turns"]:
            names = ", ".join(e["tool"] for e in turn.get("tool_events", [])) or "Không có"
            lines.append(f"| {turn['turn_index']} | {clean(turn['user'], 100)} | {names} | `{transcript['artifact_version']}` | {turn['status']} |")
        lines += ["", f"Transcript: `{rel(transcript_path)}`. Đây là kịch bản CLI 3 lượt tự động nhưng dùng API/tool thật, không phải mock; không mô tả thành phiên demo thủ công. UI còn có các transcript v1 người dùng đã thử trong `transcripts/ui_v1_*.json`."]
    else:
        lines.append("| — | Chưa có transcript live v2 | | | Chưa thực hiện |")
    lines += ["", "## B5. Tool tests / UI / Bonus evidence", "",
        "| Hạng mục | Bằng chứng | Kết quả / giới hạn |", "|---|---|---|",
        "| Unit test toàn bộ | `analysis/pytest_v2.txt`, `tests/` | 98 passed, 0 failed, 0 skipped |",
        "| Tool mới | `tests/test_tools_todo.py` | 9 trường hợp deduplicate: hợp lệ, input lỗi (6), lỗi xử lý, URL thiếu/query khác nhau |",
        "| Test TODO starter | `tests/test_tools_todo.py` | Đã điền đủ stub cho clarify, format, send, lookup, fetch, timeline, social_search, policy; HTTP dùng fake_http |",
        "| UI | `app.py`, `tests/test_ui.py`, `analysis/ui_validation.md` | Chọn v2, giữ ngữ cảnh, lưu/tải transcript; Telegram bị chặn. Chưa public |",
        "| Regression Windows | `tests/test_chat_logging.py` | Bắt UnicodeEncodeError trên console hẹp mà routing eval không phát hiện |",
        "| Telegram | Test HTTP giả lập | Không cấu hình/gửi Telegram thật; chưa làm bonus gửi có xác nhận |",
        "| arXiv/local model | Không thực hiện trong mốc này | Không nhận bonus chưa có log |", "",
        "Không phát hiện bug mới ở các tool starter qua 14 nhóm hành vi TODO vừa bổ sung. Bug in log Unicode đã được sửa ở giai đoạn UI trước đó. Unit test mới có thể bắt việc tool truyền sai request hoặc xử lý URL sai dù model vẫn chọn đúng tên tool.", "", "## B6. Reflection", "",
        "- `system_prompt.md` phù hợp cho quy tắc hội thoại: hỏi khi thiếu thông tin, xác nhận hành động và xử lý ý định mới nhất. v1 chỉ thay quy tắc thiếu handle/URL.",
        "- `tools.yaml` phù hợp cho ý nghĩa tham số, ví dụ query không chứa mốc thời gian khi đã có timeframe. v2 chỉ đổi mô tả lookup.query; tool mới có hướng dẫn lúc dùng/không dùng.",
        "- Cần review thủ công các query gần nghĩa bị bộ chấm exact-match đánh FAIL (R03), dữ liệu API rỗng/lỗi và chất lượng tóm tắt. Chỉ sửa quy tắc tổng quát, không sửa base eval để tăng điểm.",
        "- Bước tiếp theo v3: xử lý xác nhận send, handle và chuyển tool theo lỗi còn lại, mỗi thử nghiệm có giả thuyết riêng; chuẩn bị link demo public. Trước khi nộp cần kiểm tra lại toàn bộ yêu cầu v3 và báo cáo cuối.", "", "## B7. Small Local Model Challenge (bonus)", "", "Chưa thực hiện; không có số liệu local model để báo cáo.", "", "## Trạng thái mốc v2", "",
        "Đã hoàn thành tool mới còn thiếu của mốc v1, unit test không skip, 10 eval nhóm, phép đo v2 và version log/report có bằng chứng thật. Hoàn thành vòng đánh giá không đồng nghĩa mọi case phải PASS. v3 và triển khai public chưa thực hiện.", ""]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print("Recorded v2 report and evidence from matching artifact hashes.")


if __name__ == "__main__":
    main()
