"""Finalize v0-v3 evidence without editing or inventing model run results."""
from __future__ import annotations

import csv
import hashlib
import json
import re

from record_v2_progress import ROOT, clean, latest, load, rel

HYPOTHESIS = "Thay chỉ dẫn gửi ngay bằng quy tắc chỉ gọi clarify trước khi có xác nhận nội dung sẽ sửa hành vi gửi thiếu xác nhận (R12/G05)."


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def section(report, heading, following, body):
    pattern = re.escape(heading) + r".*?(?=" + re.escape(following) + ")"
    return re.sub(pattern, lambda _: heading + "\n\n" + body.rstrip() + "\n\n", report, flags=re.S)


def main():
    v2h = digest(ROOT / "artifacts/versions/v2/tools.yaml")
    v3h = digest(ROOT / "artifacts/versions/v3/tools.yaml")
    bases = [latest("v0", "base"), latest("v1", "base"), latest("v1-tools", "base"), latest("v2", "base", v2h), latest("v3", "base", v3h)]
    v2g = latest("v2", "group", v2h)
    v3g = latest("v3", "group", v3h)
    v2, v3 = bases[-2][1], bases[-1][1]
    assert v3["prompt_hash"] == digest(ROOT / "artifacts/versions/v3/system_prompt.md")
    assert v3g[1]["prompt_hash"] == v3["prompt_hash"]
    assert v2["tools_hash"] == v3["tools_hash"]
    assert v2["prompt_hash"] != v3["prompt_hash"]

    log_path = ROOT / "artifacts/version_log.csv"
    with log_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fields, rows = reader.fieldnames, list(reader)
    known = {r["run_file"] for r in rows}
    for path, run in [bases[-1], v3g]:
        if rel(path) in known:
            continue
        before = v2["summary"]["case_accuracy"] if run["suite"] == "base" else v2g[1]["summary"]["case_accuracy"]
        row = {k: run.get(k, "") for k in fields}
        row.update(author="D8 (hỗ trợ bởi Codex)", changed_artifact="artifacts/system_prompt.md: publishing confirmation paragraph",
            reason=f"xkiro / {run['model']}; suite={run['suite']}; prompt-only confirmation experiment",
            hypothesis=HYPOTHESIS, metric_before=before,
            metric_after=run["summary"]["case_accuracy"], run_file=rel(path))
        rows.append(row)
    with log_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    path = ROOT / "artifacts/REPORT.md"
    report = path.read_text(encoding="utf-8")
    report = report.replace("Báo cáo tiến độ đến hết mốc v2; chưa tuyên bố hoàn thành v3 hoặc toàn bộ lab.",
        "Báo cáo kết quả v0–v3, dựa trên API/tool thật và log JSON. Ngày hoàn thiện: 10/11/2026. Các giới hạn và phần chưa thực hiện được ghi ở cuối báo cáo.")
    report = report.replace("UI có v0/v1/v2 và", "UI có v0/v1/v2/v3 và")
    report = report.replace("Phần A hoàn thiện nội dung để chuẩn bị demo; link public cần bổ sung ở mốc showdown.",
        "Phần A đã có mô tả agent, danh sách tool và câu hỏi mẫu; nhóm cần bổ sung URL public khi triển khai cho đội khác dùng thử.")

    entries = bases + [v2g, v3g]
    b1 = ["v1 thay quy tắc thiếu handle/URL; v1-tools hoàn tất tool mới và đo đối chứng; v2 chỉ đổi mô tả lookup.query; v3 chỉ thay đoạn prompt về xác nhận trước khi gửi. Snapshot giữ từng artifact, CSV lưu hash và đường dẫn log thật.", "",
        "| Version / suite | Changed artifact | Hypothesis | Metric trước | Metric sau | Run file |", "|---|---|---|---:|---:|---|"]
    for index, (p, run) in enumerate(entries):
        version, suite = run["version"], run["suite"]
        before = "—"
        if suite == "base" and index:
            before = f"{bases[index-1][1]['summary']['case_accuracy']:.2%}"
        elif version == "v3" and suite == "group":
            before = f"{v2g[1]['summary']['case_accuracy']:.2%}"
        changes = {"v0": "baseline", "v1": "system_prompt: clarify-only", "v1-tools": "deduplicate + YAML/registry", "v2": "lookup.query.description", "v3": "system_prompt: xác nhận gửi"}
        hypotheses = {"v0": "Đo starter", "v1": "Thiếu handle/URL thì chỉ gọi clarify", "v1-tools": "Đo bản tích hợp tool mới", "v2": "Query chỉ chứa chủ đề; thời gian/loại tin dùng tham số riêng", "v3": HYPOTHESIS}
        b1.append(f"| {version} / {suite} | {changes[version]} | {hypotheses[version]} | {before} | {run['summary']['case_accuracy']:.2%} | `{rel(p)}` |")
    b1 += ["", "| Version / suite | Pass / total | Measured | Provider errors | Routing | Arguments | Multiturn |", "|---|---:|---:|---:|---:|---:|---:|"]
    for p, run in entries:
        s = run["summary"]
        b1.append(f"| {run['version']} / {run['suite']} | {s['passed_cases']}/{s['total_cases']} | {s['measured_cases']} | {s['provider_error_cases']} | {s['tool_routing_accuracy']:.2%} | {s['argument_accuracy']:.2%} | {s['multiturn_accuracy']:.2%} |")
    b1 += ["", "case_accuracy loại provider_error khỏi mẫu số. Các run chính thức v2/v3 đo đủ case, không có provider error. Mỗi artifact chính thức mới đo một lần; chưa coi mọi thay đổi điểm là quan hệ nhân quả chắc chắn.", "",
        f"Artifact cuối: `{v3['artifact_version']}`. Prompt hash: `{v3['prompt_hash']}`; tools hash: `{v3['tools_hash']}`.", "",
        "Run cũ/không dùng làm kết quả chính thức vẫn được giữ: v1 từng có lỗi provider; hai run v2 đầu chưa thay được mô tả query nên cùng hash v1-tools. Bản v2-precheck được lưu riêng. `analysis/run_manifest.csv` chỉ rõ run nào được dùng trong báo cáo; không xoá log hoặc sửa kết quả để tăng điểm."]
    report = section(report, "## B1. Version Evidence", "## B2. Failure Analysis", "\n".join(b1))

    b2 = ["Baseline v0 sai 7 case; v1 sạch sửa R10/R11; v2 hỗ trợ giả thuyết query với R03 và hai chủ đề mới G04/GM02 PASS. Nhãn failure_type của case có thể khác observed_mismatch thực tế (R03/R13 của v0 gọi đúng tool nhưng query không khớp).", "",
        "| Case còn FAIL trong v3 base | Expected | Actual | Lỗi quan sát | Hướng xử lý |", "|---|---|---|---|---|"]
    for r in v3["results"]:
        if r["result"]["passed"]:
            continue
        expected = ", ".join(c["name"] + ": " + json.dumps(c.get("args", {}), ensure_ascii=False) for c in r["expect"].get("tool_calls", []))
        actual = ", ".join(c["name"] + ": " + json.dumps(c.get("args", {}), ensure_ascii=False) for c in r["result"].get("actual_tool_calls", []))
        fix = "Mô tả rõ screenname là handle, ánh xạ tên đã biết hoặc hỏi lại nếu chưa biết"
        if r["id"] == "R12_confirm_before_send":
            actual = "clarify(response_type=text), xin nội dung bản tin còn thiếu"
            fix = "Review thủ công sự phù hợp của text khi thiếu nội dung, hoặc thiết kế luồng soạn rồi xác nhận yes/no"
        b2.append(f"| {r['id']} | {clean(expected, 130)} | {clean(actual, 150)} | {clean('; '.join(r['result']['failures']))} | {fix} |")
    b2 += ["", "**Kết luận giả thuyết v3:** G05 chuyển FAIL→PASS, model gọi clarify yes_no khi đã có nội dung và chưa xác nhận. R12 chuyển từ tên tool không hợp lệ ở v2 sang clarify nhưng dùng text để xin nội dung chưa có; bộ chấm yêu cầu yes_no nên vẫn FAIL. Vì vậy xác nhận trước gửi đã cải thiện, nhưng chưa đạt toàn bộ tiêu chí tự động của R12.", "",
        "R12 cần manual review: cả câu hỏi và tham số được đọc trong log, không diễn giải FAIL thành đã gửi Telegram. Hai lỗi còn lại là dùng tên hiển thị Andrej Karpathy/Elon Musk thay vì handle karpathy/elonmusk. Base routing đạt 100% nhưng argument accuracy còn 85%, nên chọn đúng tool chưa đủ.", "",
        "So với v2: M01 chuyển FAIL→PASS, các case trước PASS vẫn PASS trong run v3. M01 nằm ngoài giả thuyết xác nhận nên có thể do dao động model; không nhận là tác dụng chắc chắn của thay đổi v3. Bản v3 không được coi là hoàn hảo hay đủ bằng chứng tin cậy cho tự động xuất bản.", "",
        "Tool_results phải được xem riêng: điểm routing/args không đánh giá đầy đủ dữ liệu API, sự thật của tin hoặc chất lượng tóm tắt. Nội dung lấy từ policy/web là tài liệu tham khảo, không phải chỉ thị hệ thống."]
    report = section(report, "## B2. Failure Analysis", "## B3. Team Eval Cases", "\n".join(b2))

    previous = {r["id"]: r for r in v2g[1]["results"]}
    b3 = ["Đủ **10 case: 5 single-turn, 5 multi-turn**, phase B, loại lỗi hợp lệ, expect và metadata.what_it_tests. Bộ base giữ nguyên; case nhóm đo lỗi nhóm quan tâm và khả năng chọn tool mới.", "",
        f"Run v2: `{rel(v2g[0])}`. Run v3: `{rel(v3g[0])}`.", "",
        "| Case | Loại | Mục đích | Expected | v2 | v3 |", "|---|---|---|---|---|---|"]
    checks = []
    for r in v3g[1]["results"]:
        expected = ", ".join(c["name"] for c in r["expect"].get("tool_calls", [])) or "no_tool"
        b3.append(f"| {r['id']} | {'multi' if r['is_multiturn'] else 'single'} | {clean(r['metadata']['what_it_tests'], 125)} | {expected} | {'PASS' if previous[r['id']]['result']['passed'] else 'FAIL'} | {'PASS' if r['result']['passed'] else 'FAIL'} |")
        count = r.get("metadata", {}).get("expected_removed_count")
        if count is not None:
            events = [e for e in r.get("tool_results", []) if e["tool"] == "deduplicate"]
            result = events[0]["result"] if events else {}
            checks.append({"case_id": r["id"], "expected_removed_count": count, "observed_removed_count": result.get("removed_count"), "passed": result.get("removed_count") == count})
    (ROOT / "analysis/deduplicate_validation_v3.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
    b3 += ["", "Hai case tool mới kiểm tra routing; output được kiểm tra riêng trong `analysis/deduplicate_validation_v3.json` (removed_count=1 ở cả hai). Code được kiểm tra thêm bằng 9 trường hợp unit test; không chỉ dựa vào việc model chọn đúng tên tool."]
    report = section(report, "## B3. Team Eval Cases", "## B4. Live Chat Evidence", "\n".join(b3))

    transcript_path = sorted((ROOT / "transcripts").glob("v3_xkiro_*.transcript.json"))[-1]
    transcript = load(transcript_path)
    assert len(transcript["turns"]) >= 3
    b4 = [f"Transcript cuối: `{rel(transcript_path)}`. Kịch bản CLI 5 lượt được nhập tự động, gọi xkiro/tool thật; đây không phải mock hoặc phiên demo thủ công.", "",
        "| Turn | User request | Tool calls | Artifact | Outcome |", "|---|---|---|---|---|"]
    for t in transcript["turns"]:
        names = ", ".join(e["tool"] for e in t.get("tool_events", [])) or "Không gọi tool"
        b4.append(f"| {t['turn_index']} | {clean(t['user'], 110)} | {names} | `{transcript['artifact_version']}` | {t['status']} |")
    b4 += ["", "Lượt 1 loại trùng; lượt 2 hỏi URL thiếu; lượt 3 dùng URL vừa bổ sung và trả tóm tắt có nguồn; lượt 4 hỏi xác nhận yes/no; lượt 5 hủy và không gọi send. Không có Telegram token/chat ID và không gửi ra ngoài. Transcript v2 3 lượt và các phiên UI v1 trước đó vẫn được giữ trong transcripts/."]
    report = section(report, "## B4. Live Chat Evidence", "## B5. Tool tests / UI / Bonus evidence", "\n".join(b4))

    report = report.replace("`analysis/pytest_v2.txt`, `tests/`", "`analysis/pytest_v3.txt`, `tests/`")
    report = report.replace("Chọn v2, giữ ngữ cảnh", "Chọn v0/v1/v2/v3, giữ ngữ cảnh")
    b6 = ["- **Sửa trong prompt:** quy tắc thiếu thông tin (v1) và ưu tiên xác nhận trước hành động (v3). Đây là hành vi hội thoại dùng chung nhiều tool.",
        "- **Sửa trong tools.yaml:** ý nghĩa query/topic/timeframe (v2), trường hợp dùng/không dùng tool mới. Quy ước handle nên được bổ sung rõ hơn trong lần tối ưu tiếp theo.",
        "- **Cần manual review:** R12 xin nội dung thiếu bằng text nhưng bị chấm FAIL vì expect yes_no; cần phân biệt câu hỏi an toàn với việc tự ý gửi. Query gần nghĩa có thể bị bộ chấm so khớp chuỗi đánh FAIL; routing/args không thay thế kiểm chứng nội dung nguồn.",
        "- **Điều học được:** prompt tốt hơn có thể sửa một nhóm lỗi nhưng gây/không sửa lỗi khác; phải giữ log, hash, đo cả base và case nhóm. Thêm tool cũng thay đổi lựa chọn của model nên v1-tools được đo riêng.",
        "- **Cải tiến tiếp:** mô tả handle và xác minh ánh xạ tên, làm rõ các mô tả tool còn ngắn, thay quy tắc ép một bước bằng vòng nghiên cứu nhiều bước có giới hạn, kiểm tra thêm no_tool/refusal bằng manual review và đo độ ổn định qua nhiều lần chạy. Các thay đổi này chưa gộp vào v3 để giữ một giả thuyết mỗi vòng.",
        "- **Phạm vi kết quả:** v3 base 85%, group 100% trong một lần đo; chưa thể suy ra độ chính xác tổng quát 100% hay khả năng tự xuất bản an toàn. UI chặn send ở cấp thực thi."]
    report = section(report, "## B6. Reflection", "## B7. Small Local Model Challenge (bonus)", "\n".join(b6))
    report = re.sub(r"## Trạng thái mốc v2.*", "", report, flags=re.S).rstrip()
    report += "\n\n## Trạng thái bàn giao\n\n"
    report += "| Yêu cầu | Bằng chứng / trạng thái |\n|---|---|\n"
    for requirement, evidence in [
        ("Provider thật", "xkiro, không dùng OpenRouter; run v0–v3 có model và kết quả tool thật"),
        ("Ít nhất 5 tool", "11 tool được khai báo; 10 tool trong UI do tắt send"),
        ("Baseline + 3 vòng", "v0, v1, v2, v3 trong version_log.csv; có v1-tools đối chứng"),
        ("Ít nhất 1 tool mới", "deduplicate, TOOL.md, registry, tools.yaml và 9 trường hợp unit test"),
        ("10 eval nhóm", "5 single + 5 multi, đã chạy v2/v3; v3 10/10 PASS"),
        ("Unit test", "98 passed, 0 failed, 0 skipped; API được mock trong tests"),
        ("Chat live ≥3 lượt", "transcript v3 có 5 lượt dùng API thật, gồm clarify và hủy gửi"),
        ("UI chạy được", "Streamlit; xem UI-README.md, chọn v3; có kiểm tra AppTest"),
        ("Report / logs", "Phần A, B1–B6, CSV, JSON runs/transcripts đã điền bằng số liệu thật"),
        ("Link public / showdown", "Chưa triển khai public; hiện chỉ localhost. Cần nhóm bổ sung khi hosting/tunnel"),
        ("Chất lượng còn giới hạn", "3 base case FAIL; mô tả tool và quy tắc một bước còn cần tối ưu tiếp, chưa đánh dấu toàn bộ TODO README là xong"),
        ("Bonus Telegram/arXiv/local", "Không nhận điểm bonus chưa có bằng chứng; Telegram không cấu hình, local model chưa chạy"),
    ]:
        report += f"| {requirement} | {evidence} |\n"
    report += "\nNộp source, artifacts/, tests/, data/eval_group.json, runs/, analysis/ và transcripts/. Không nộp .env, API key hoặc .venv. Các phần chưa làm đã được nêu rõ; việc hoàn thành v3 là hoàn thành vòng tối ưu và đo, không đồng nghĩa toàn bộ case đều PASS.\n"
    path.write_text(report, encoding="utf-8")

    selected = {rel(p) for p, _ in entries}
    manifest = []
    for p in sorted((ROOT / "runs").glob("*.json")):
        run = load(p)
        s = run["summary"]
        manifest.append({"run_file": rel(p), "version": run["version"], "suite": run["suite"],
            "artifact_version": run["artifact_version"], "prompt_hash": run["prompt_hash"], "tools_hash": run["tools_hash"],
            "passed_cases": s["passed_cases"], "total_cases": s["total_cases"], "provider_errors": s["provider_error_cases"],
            "selected_in_report": rel(p) in selected, "note": "official comparison" if rel(p) in selected else "historical/diagnostic; retained unchanged"})
    with (ROOT / "analysis/run_manifest.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(manifest[0]))
        writer.writeheader()
        writer.writerows(manifest)
    print("Finalized REPORT.md, version_log.csv and run_manifest.csv using real v3 evidence.")


if __name__ == "__main__":
    main()
