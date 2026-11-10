"""Local immutable prompt/tool snapshots and evidence for the version UI."""
from __future__ import annotations

import inspect
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

from tools import TOOL_FUNCTIONS
from versioning import artifact_version_dict, build_artifact_version

ROOT = Path(__file__).resolve().parent
VERSIONS_DIR = ROOT / "artifacts/versions"
RUNS_DIR = ROOT / "runs"


def version_path(name: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,47}", name):
        raise ValueError("Tên version chỉ gồm chữ, số, dấu - hoặc _, tối đa 48 ký tự.")
    return VERSIONS_DIR / name


def list_versions() -> list[str]:
    if not VERSIONS_DIR.exists():
        return []
    return sorted(p.name for p in VERSIONS_DIR.iterdir()
                  if p.is_dir() and p.name != "v1-tool" and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,47}", p.name)
                  and (p / "system_prompt.md").is_file() and (p / "tools.yaml").is_file())


def get_version(name: str) -> dict:
    folder = version_path(name)
    if name == "v1" and (folder / "full/tools.yaml").is_file():
        folder = folder / "full"
    if name == "v3":
        if (folder / "release/tools.yaml").is_file():
            folder = folder / "release"
        elif (folder / "final/tools.yaml").is_file():
            folder = folder / "final"
    prompt_path, tools_path = folder / "system_prompt.md", folder / "tools.yaml"
    metadata_path = folder / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
    return {**metadata, **artifact_version_dict(build_artifact_version(name, prompt_path, tools_path)),
            "prompt_path": prompt_path, "tools_path": tools_path,
            "prompt": prompt_path.read_text(encoding="utf-8"),
            "tools_yaml": tools_path.read_text(encoding="utf-8")}


def validate_tools(text: str) -> None:
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError("YAML công cụ không hợp lệ.") from exc
    declarations = data.get("tools") if isinstance(data, dict) else None
    if not isinstance(declarations, list) or not declarations:
        raise ValueError("YAML phải chứa danh sách tools không rỗng.")
    names = set()
    for declaration in declarations:
        if not isinstance(declaration, dict):
            raise ValueError("Mỗi tool phải là một object.")
        name = declaration.get("name")
        if not isinstance(name, str) or name not in TOOL_FUNCTIONS or name in names:
            raise ValueError("Tool phải có implementation đã đăng ký và không trùng tên.")
        names.add(name)
        if not isinstance(declaration.get("description"), str) or not declaration["description"].strip():
            raise ValueError(f"Tool {name} cần description.")
        params = declaration.get("parameters", {})
        if not isinstance(params, dict) or params.get("type") != "object":
            raise ValueError(f"Tool {name}: parameters phải có type=object.")
        properties, required = params.get("properties", {}), params.get("required", [])
        if not isinstance(properties, dict) or not isinstance(required, list) or not all(isinstance(k, str) for k in required):
            raise ValueError(f"Tool {name}: properties/required không hợp lệ.")
        accepted = set(inspect.signature(TOOL_FUNCTIONS[name]).parameters)
        if not set(properties) <= accepted or not set(required) <= set(properties):
            raise ValueError(f"Tool {name}: tham số không khớp implementation.")


def create_version(name: str, base_name: str, prompt: str, tools_yaml: str, hypothesis: str) -> dict:
    folder = version_path(name)
    get_version(base_name)  # Ensure the selected parent exists before creating anything.
    if not prompt.strip() or not hypothesis.strip():
        raise ValueError("Cần điền prompt và giả thuyết thay đổi.")
    validate_tools(tools_yaml)
    try:
        folder.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise ValueError("Version đã tồn tại. Hãy chọn tên khác để giữ nguyên lịch sử.") from exc
    (folder / "system_prompt.md").write_text(prompt, encoding="utf-8")
    (folder / "tools.yaml").write_text(tools_yaml, encoding="utf-8")
    (folder / "metadata.json").write_text(json.dumps({
        "parent": base_name, "hypothesis": hypothesis.strip(),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return get_version(name)


def matching_runs(version: dict, suite: str | None = None) -> list[tuple[Path, dict]]:
    matches = []
    configurations = {(version["version"], version["prompt_hash"], version["tools_hash"])}
    if version["version"] == "v1":
        # v1's prompt experiment and new-tool check are evidence for one version.
        original = version_path("v1")
        measured = build_artifact_version("v1", original / "system_prompt.md", original / "tools.yaml")
        configurations.add(("v1", measured.prompt_hash, measured.tools_hash))
        configurations.add(("v1-tool", version["prompt_hash"], version["tools_hash"]))
    for path in RUNS_DIR.glob("*.json"):
        try:
            run = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if ((run.get("version"), run.get("prompt_hash"), run.get("tools_hash")) in configurations
                and (suite is None or run.get("suite") == suite)):
            matches.append((path, run))
    return sorted(matches, key=lambda item: item[0].stat().st_mtime, reverse=True)


def version_rows() -> list[dict]:
    rows = []
    for name in list_versions():
        version = get_version(name)
        runs = matching_runs(version)
        base_runs = [item for item in runs if item[1].get("suite") == "base"]
        evidence = (base_runs or runs)
        run = evidence[0][1] if evidence else None
        summary = run.get("summary", {}) if run else {}
        accuracy = summary.get("case_accuracy")
        group_runs = [item for item in runs if item[1].get("suite") == "group"]
        group_summary = group_runs[0][1].get("summary", {}) if group_runs else None
        cross_runs = [item for item in runs if item[1].get("suite") == "cross"]
        cross_summary = cross_runs[0][1].get("summary", {}) if cross_runs else None
        rows.append({"Version": name, "Tạo từ": version.get("parent", "—"),
                     "Giả thuyết": version.get("hypothesis", {
                         "v0": "Baseline đã chạy", "v1": "Hỏi lại khi thiếu handle/URL",
                     }.get(name, "—")),
                     "Trạng thái": "Đã đánh giá" if run else "Chưa đánh giá",
                     "Suite": run.get("suite", "—") if run else "—",
                     "Độ chính xác": f"{accuracy:.0%}" if isinstance(accuracy, (float, int)) else "—",
                     "Đạt/tổng": f"{summary.get('passed_cases', 0)}/{summary.get('total_cases', 0)}" if run else "—",
                     "Group đạt/tổng": f"{group_summary.get('passed_cases', 0)}/{group_summary.get('total_cases', 0)}" if group_summary else "—",
                     "Cross đạt/tổng": f"{cross_summary.get('passed_cases', 0)}/{cross_summary.get('total_cases', 0)}" if cross_summary else "—",
                     "Prompt hash": version["prompt_hash"][:12], "Tools hash": version["tools_hash"][:12]})
    return rows
