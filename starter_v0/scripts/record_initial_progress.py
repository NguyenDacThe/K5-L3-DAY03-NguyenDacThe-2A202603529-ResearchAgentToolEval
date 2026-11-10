"""Record actual v0/v1 evidence without inventing results for later lab steps."""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HYPOTHESIS = "Hỏi clarify thay vì tự đoán khi thiếu tài khoản hoặc URL sẽ sửa R10/R11."


def main():
    runs = []
    for version in ("v0", "v1"):
        paths = sorted((ROOT / "runs").glob(f"{version}_B_base_xkiro_*.json"))
        if paths:
            path = paths[-1]
            runs.append((path, json.loads(path.read_text(encoding="utf-8"))))
    log = ROOT / "artifacts/version_log.csv"
    with log.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)
    known = {r["run_file"] for r in rows}
    for path, run in runs:
        relative = path.relative_to(ROOT).as_posix()
        if relative in known:
            continue
        row = {k: run.get(k, "") for k in fields}
        row.update(author="Nhóm (hỗ trợ bởi Codex)",
            changed_artifact="baseline" if run["version"] == "v0" else "artifacts/system_prompt.md",
            reason=f"xkiro / {run['model']}; one missing-information policy change" if run["version"] == "v1" else f"Baseline xkiro / {run['model']}",
            hypothesis=HYPOTHESIS if run["version"] == "v1" else "Đo starter trước khi tối ưu",
            metric_before="0.65" if run["version"] == "v1" else "",
            metric_after=run["summary"]["case_accuracy"], run_file=relative)
        rows.append(row)
    with log.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    report_path = ROOT / "artifacts/REPORT.md"
    report = report_path.read_text(encoding="utf-8")
    report = report.replace("- Provider/model:", "- Provider/model: xkiro / mistralai/mistral-large-2512", 1) if "- Provider/model:\n" in report else report
    section = "## B1. Version Evidence\n\nĐiểm lấy từ run JSON thật; metric trước/sau là case_accuracy.\n\n"
    section += "| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |\n|---|---|---|---:|---:|---|\n"
    for path, run in runs:
        v = run["version"]
        section += f"| {v} | {'baseline' if v == 'v0' else 'system_prompt.md'} | {'Đo starter' if v == 'v0' else HYPOTHESIS} | {'—' if v == 'v0' else '65%'} | {run['summary']['case_accuracy']:.2%} | `{path.relative_to(ROOT).as_posix()}` |\n"
    section += "| v2 | Chưa thực hiện | | | | |\n| v3 | Chưa thực hiện | | | | |\n\n"
    section += "| Version | Passed / total | Measured cases | Provider errors | Routing | Arguments | Multiturn |\n|---|---|---:|---:|---:|---:|---:|\n"
    for _, run in runs:
        s = run['summary']
        section += f"| {run['version']} | {s['passed_cases']}/{s['total_cases']} | {s['measured_cases']} | {s['provider_error_cases']} | {s['tool_routing_accuracy']:.2%} | {s['argument_accuracy']:.2%} | {s['multiturn_accuracy']:.2%} |\n"
    section += "\ncase_accuracy loại provider_error khỏi mẫu số. Không kết luận tăng chất lượng chỉ từ điểm này khi số measured_cases khác nhau.\n\n"
    report = re.sub(r"## B1\. Version Evidence.*?(?=## B2\.)", lambda _: section, report, flags=re.S)
    section = "## B2. Failure Analysis\n\nPhân tích baseline v0. Nhãn case khác lỗi quan sát ở R03/R13: tool đúng, query không khớp bộ chấm.\n\n"
    section += "| Case ID | Observed mismatch | Actual Tool Calls | What Failed | Fix hypothesis |\n|---|---|---|---|---|\n"
    details = [
        ("R03", "wrong_arg_value", "lookup", "query chứa cả câu/ngày; bộ chấm mong AI", "Mô tả query là từ khóa, thời gian ở timeframe"),
        ("R10", "missing_tool_call", "timeline(screenname=Sam Altman)", "Tự đoán tài khoản thay vì hỏi", "v1: clarify khi thiếu tài khoản"),
        ("R11", "missing_tool_call", "fetch(url=https://vnexpress.net)", "Tự đoán URL", "v1: clarify khi thiếu URL"),
        ("R12", "missing_tool_call", "Tên tool không hợp lệ; args lồng send", "Không gọi clarify yes_no; giả lập đồng ý khi hết giờ", "Vòng sau: xác nhận rõ ràng, không coi im lặng là đồng ý"),
        ("R13", "wrong_arg_value", "lookup + social_search", "Gọi đủ tool nhưng query của lookup không khớp AI", "Quy ước query"),
        ("M02", "wrong_arg_value", "lookup", "timeframe đúng; query không khớp robotics", "Quy ước query"),
        ("M03", "wrong_arg_value", "timeline(screenname=Andrej Karpathy, limit=3)", "Dùng tên người thay vì handle karpathy", "Mô tả handle và quy tắc ánh xạ/hỏi lại"),
    ]
    for detail in details:
        section += "| " + " | ".join(detail) + " |\n"
    section += "\nprovider_error_cases=0 không chứng minh mọi API tool thành công: v0 có tool timeline trả JSONDecodeError. Cần kiểm tra tool_results riêng.\n\n"
    if len(runs) == 2:
        before = {r["id"]: r["result"]["passed"] for r in runs[0][1]["results"]}
        after = runs[1][1]
        improved = [r["id"] for r in after["results"] if r["result"]["passed"] and not before[r["id"]]]
        regressed = [r["id"] for r in after["results"] if not r["result"]["passed"] and before[r["id"]]]
        section += f"v1 so với v0: cải thiện {', '.join(improved) or 'không có'}; hồi quy {', '.join(regressed) or 'không có'}.\n\n"
        section += "Mỗi phiên bản mới chạy một lần; biến động ngoài R10/R11 chưa đủ để kết luận do thay đổi prompt.\n\n"
        section += "Kết luận v1: giả thuyết hỏi lại chưa được chứng minh. R10 không trả tool call; R11 lỗi API 409 duplicate request; R12 lỗi TypeError ở đường gọi provider. Vẫn 13/20 case đúng, multiturn giảm từ 66,67% xuống 50%. Cần xử lý/kiểm tra lại lỗi provider và cải tiến hướng dẫn clarify trong vòng tiếp theo.\n\n"
    report = re.sub(r"## B2\. Failure Analysis.*?(?=## B3\.)", lambda _: section, report, flags=re.S)
    report_path.write_text(report, encoding="utf-8")
    print(f"Recorded {len(runs)} real baseline/optimization runs.")


if __name__ == "__main__":
    main()
