from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import streamlit as st

from chat import run_model_tool_loop, trim_history, write_transcript
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version
from version_store import create_version, get_version, list_versions, matching_runs, version_rows
from feedback_store import read_feedback, save_feedback

ROOT = Path(__file__).resolve().parent
load_lab_env(ROOT)
st.set_page_config(page_title="Research Lab · Versions", page_icon="🔎", layout="wide")

st.markdown("""<style>
.stApp {background: #f6f8fc;}
.block-container {max-width: 1180px; padding-top: 2.5rem;}
[data-testid="stSidebar"] {background: #eaf0f8;}
h1, h2, h3 {color: #152b49;}
[data-testid="stMetric"] {background: white; border: 1px solid #dfe6f1;
 border-radius: 14px; padding: 18px;}
.eyebrow {color:#2563eb; letter-spacing:.15em; font-size:.75rem; font-weight:700;}
</style>""", unsafe_allow_html=True)


def reset_chat() -> None:
    st.session_state.history = []
    st.session_state.turns = []
    st.session_state.transcript_id = f"ui_{uuid4().hex}"
    st.session_state.created_at = datetime.now().isoformat(timespec="seconds")


if "history" not in st.session_state:
    reset_chat()

with st.sidebar:
    st.markdown("### 🔎 Research Lab")
    st.caption("Nghiên cứu có nguồn · Quan sát từng tool")
    versions = list_versions()
    if not versions:
        st.error("Chưa có snapshot phiên bản trong artifacts/versions/.")
        st.stop()
    default_version = next((name for name in ["v3", "v2", "v1"] if name in versions), versions[0])
    version_name = st.selectbox("Phiên bản", versions, index=versions.index(default_version), key="selected_version")
    active = get_version(version_name)
    provider_name = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini", "ollama"])
    provider = make_provider(provider_name)
    default_model = getattr(provider, "default_model", "")
    model = st.text_input("Model tùy chọn", placeholder=default_model, key=f"model_{provider_name}").strip() or None
    max_rounds = st.slider("Số vòng tool tối đa", 1, 8, 4)
    if st.button("＋ Cuộc trò chuyện mới", use_container_width=True, key="reset_chat"):
        reset_chat()
        st.rerun()
    st.divider()
    st.markdown("**Cấu hình API**")
    for key in ["OPENROUTER_API_KEY", "TAVILY_API_KEY", "FIRECRAWL_API_KEY", "RAPIDAPI_KEY"]:
        st.caption(f"{'🟢' if os.getenv(key) else '⚪'} {key.removesuffix('_API_KEY')}")
    st.caption("Đọc từ .env trên máy. Không hiển thị khóa API.")
    st.info(f"Đang dùng {version_name}. v3 làm rõ routing, tham số, xác nhận và tránh gọi trùng. Chat luôn tắt gửi Telegram; quy tắc được đo bằng eval.")

context_key = (version_name, active["prompt_hash"], active["tools_hash"], provider_name, model)
if st.session_state.get("chat_context") != context_key:
    reset_chat()
    st.session_state.chat_context = context_key

st.markdown('<div class="eyebrow">RESEARCH AGENT / VERSION LAB</div>', unsafe_allow_html=True)
st.title("Từ câu hỏi đến bằng chứng")
st.caption("Tra cứu web, theo dõi bài đăng và đọc tài liệu — cùng lịch sử tool rõ ràng.")
st.caption(f"Phiên bản đang chọn: {version_name} · Prompt {active['prompt_hash'][:12]} · Tools {active['tools_hash'][:12]}")
chat_tab, eval_tab, versions_tab, tools_tab, demo_tab = st.tabs(["💬 Trò chuyện", "📊 Đánh giá & lỗi", "🗂 Phiên bản", "🧰 Công cụ", "🎤 Demo & gom lỗi"])

declarations = load_tool_declarations(active["tools_path"])
chat_tools = to_openai_tools([d for d in declarations if d["name"] != "send"])

with chat_tab:
    st.caption("Gợi ý: Tìm tin AI hôm nay trên web · Lấy 5 tweet mới nhất của @sama · Tóm tắt một URL")
    for turn in st.session_state.turns:
        with st.chat_message("user"):
            st.write(turn["user"])
        with st.chat_message("assistant"):
            st.markdown(turn.get("assistant_text") or "Chưa có câu trả lời.")
            if turn.get("tool_events"):
                with st.expander(f"Xem {len(turn['tool_events'])} lượt gọi tool"):
                    st.json(turn["tool_events"])
    user_text = st.chat_input("Bạn muốn nghiên cứu điều gì?") or st.session_state.pop("demo_request", None)
    if user_text:
        with st.chat_message("user"):
            st.write(user_text)
        turn = {"user": user_text, "version": version_name, "provider": provider_name, "model": model or default_model,
                "started_at": datetime.now().isoformat(timespec="seconds")}
        with st.chat_message("assistant"):
            try:
                required_key = getattr(provider, "api_key_env", None)
                if required_key and provider_name != "ollama" and not os.getenv(required_key):
                    raise RuntimeError(f"Thiếu {required_key} trong .env.")
                prompt = active["prompt"]
                # The UI has no publishing capability, even if the model invents a send call.
                prompt += "\nIn this UI Telegram publishing is unavailable. Never call send. Explain this if asked to publish. Reply in the user's language."
                def ui_complete(*args, **kwargs):
                    response = provider.complete(*args, **kwargs)
                    if any(call.name == "send" for call in response.tool_calls):
                        raise RuntimeError("UI không hỗ trợ gửi Telegram. Không có nội dung nào được gửi.")
                    return response

                with st.spinner("Agent đang tra cứu và tổng hợp…"):
                    result = run_model_tool_loop(
                        provider=SimpleNamespace(complete=ui_complete),
                        messages=[{"role": "system", "content": prompt},
                                  *trim_history(st.session_state.history, 5),
                                  {"role": "user", "content": user_text}],
                        tools=chat_tools, model=model, max_tool_rounds=max_rounds,
                    )
                turn.update(result)
                st.markdown(result["assistant_text"] or "Agent chưa trả về nội dung; xem chi tiết tool.")
                st.session_state.history.extend([
                    {"role": "user", "content": user_text},
                    {"role": "assistant", "content": result["assistant_text"]},
                ])
                if result["tool_events"]:
                    with st.expander("Chi tiết gọi tool"):
                        st.json(result["tool_events"])
                if result["status"] == "max_tool_rounds":
                    st.warning("Đã đạt giới hạn vòng tool. Bạn có thể hỏi tiếp hoặc tăng giới hạn.")
            except Exception as exc:
                # Avoid exposing API keys in provider/tool exception messages.
                message = str(exc)
                for key, value in os.environ.items():
                    if value and any(part in key for part in ["API_KEY", "TOKEN", "SECRET"]):
                        message = message.replace(value, "[hidden]")
                turn.update(status="provider_error", assistant_text=f"Không hoàn tất yêu cầu: {message}")
                st.error(turn["assistant_text"])
        turn["ended_at"] = datetime.now().isoformat(timespec="seconds")
        st.session_state.turns.append(turn)
        transcript = {
            "transcript_id": st.session_state.transcript_id,
            "created_at": st.session_state.created_at,
            "provider": provider_name, "model": model or default_model,
            **artifact_version_dict(build_artifact_version(version_name, active["prompt_path"], active["tools_path"])),
            "ui_excluded_tools": ["send"],
            "turns": st.session_state.turns,
        }
        write_transcript(ROOT / "transcripts" / f"{st.session_state.transcript_id}.transcript.json", transcript)
    if st.session_state.turns:
        st.download_button("↓ Tải lịch sử JSON", json.dumps(st.session_state.turns, ensure_ascii=False, indent=2, default=str),
                           file_name="research_chat.json", mime="application/json")
        st.caption("Transcript tự lưu trong starter_v0/transcripts/.")

with eval_tab:
    run_files = [path for path, _ in matching_runs(active)]
    if not run_files:
        st.info(f"{version_name} chưa có log khớp prompt/tools của snapshot. Xem lệnh chạy trong tab Phiên bản.")
    else:
        selected = st.selectbox("Lần đánh giá", run_files, format_func=lambda p: p.name.replace("v1-tool_", "v1_"))
        if version_name == "v1":
            st.caption("v1 có hai phép đo: base đo prompt tối ưu với bộ tool gốc; group kiểm tra tool mới. Đây là các lần kiểm tra của cùng phiên bản v1.")
        try:
            run = json.loads(selected.read_text(encoding="utf-8"))
            summary = run["summary"]
            cols = st.columns(4)
            for col, label, key in zip(cols, ["Đạt toàn bộ", "Chọn tool", "Đúng tham số", "Nhiều lượt"],
                                       ["case_accuracy", "tool_routing_accuracy", "argument_accuracy", "multiturn_accuracy"]):
                value = summary.get(key)
                col.metric(label, f"{value:.0%}" if isinstance(value, (int, float)) else "—")
            st.caption(f"{summary.get('passed_cases', 0)}/{summary.get('total_cases', 0)} ca đạt · {summary.get('provider_error_cases', 0)} lỗi provider · {run.get('model', '')}")
            failed_only = st.toggle("Chỉ hiện ca lỗi", value=True)
            rows = []
            for case in run["results"]:
                result = case["result"]
                if failed_only and result["passed"]:
                    continue
                rows.append({"Ca": case["id"], "Kết quả": "PASS" if result["passed"] else "FAIL",
                             "Chọn tool": result.get("routing_correct"), "Đúng tham số": result.get("args_correct"),
                             "Lỗi quan sát": result.get("observed_mismatch", ""),
                             "Chi tiết": "; ".join(result.get("failures", []))})
            st.dataframe(rows, use_container_width=True, hide_index=True)
            st.markdown("#### So sánh kỳ vọng và hành vi thực tế")
            for case in run["results"]:
                if failed_only and case["result"]["passed"]:
                    continue
                with st.expander(case["id"]):
                    st.write(case.get("input"))
                    left, right = st.columns(2)
                    with left:
                        st.caption("Kỳ vọng")
                        st.json(case["expect"])
                    with right:
                        st.caption("Thực tế")
                        st.json(case["result"])
                    st.caption("Kết quả thực thi tool")
                    st.json(case.get("tool_results", []))
            report = ROOT / "analysis" / f"{version_name}_findings.md"
            if report.exists():
                with st.expander(f"Phân tích {version_name}"):
                    st.markdown(report.read_text(encoding="utf-8"))
            st.download_button("↓ Tải run JSON", selected.read_bytes(), file_name=selected.name, mime="application/json")
        except (ValueError, KeyError, TypeError) as exc:
            st.error(f"Log không đúng định dạng: {type(exc).__name__}")

with versions_tab:
    st.markdown("### Bảng phiên bản")
    st.caption("v0: baseline · v1: hỏi lại + tool mới · v2: xác nhận Telegram · v3: routing và tham số rõ ràng, tránh gọi trùng. Điểm lấy từ log đã lưu; không gộp điểm các dataset khác nhau.")
    st.dataframe(version_rows(), use_container_width=True, hide_index=True)
    st.markdown(f"#### Cấu hình {version_name}")
    with st.expander("Xem prompt và khai báo công cụ"):
        st.code(active["prompt"], language="markdown")
        st.code(active["tools_yaml"], language="yaml")
    suite = st.selectbox("Bộ đánh giá", ["base", "group", "cross"], key="eval_suite")
    cases_file = f"data/eval_{suite}.json"
    snapshot_dir = f"artifacts/versions/{version_name}" + (f"/{active['tools_path'].parent.name}" if active["tools_path"].parent.name in {"full", "final", "release"} else "")
    st.caption("Lệnh đánh giá snapshot từ Terminal trong thư mục starter_v0:")
    st.code(f'python run_eval.py --provider {provider_name} --version {version_name} --suite {suite} '
            f'--eval-cases {cases_file} --system-prompt {snapshot_dir}/system_prompt.md '
            f'--tools {snapshot_dir}/tools.yaml', language="powershell")
    st.markdown("#### Tạo version mới")
    base_name = st.selectbox("Tạo từ phiên bản", versions, index=versions.index(version_name), key="version_parent")
    base = get_version(base_name)
    if st.session_state.get("editor_parent") != base_name:
        st.session_state.editor_parent = base_name
        st.session_state.draft_prompt = base["prompt"]
        st.session_state.draft_tools = base["tools_yaml"]
    if st.session_state.get("version_notice"):
        st.success(st.session_state.pop("version_notice"))
    with st.form("create_version"):
        new_name = st.text_input("Tên version mới", placeholder="Ví dụ: v2", key="new_version_name")
        hypothesis = st.text_area("Giả thuyết / lý do thay đổi", placeholder="Một thay đổi bạn muốn kiểm chứng", key="new_version_hypothesis")
        draft_prompt = st.text_area("System prompt", height=250, key="draft_prompt")
        draft_tools = st.text_area("Khai báo công cụ (YAML)", height=220, key="draft_tools")
        submitted = st.form_submit_button("Tạo version", type="primary")
    if submitted:
        try:
            created = create_version(new_name.strip(), base_name, draft_prompt, draft_tools, hypothesis)
            st.session_state.version_notice = f"Đã tạo {created['version']} từ {base_name}. Chọn phiên bản mới ở thanh bên để dùng; phiên bản này chưa được đánh giá."
            st.rerun()
        except (ValueError, OSError) as exc:
            st.error(str(exc))
    st.caption("Lưu snapshot riêng, không ghi đè bản cũ. Tạo version không gọi API và không tự chạy eval.")

with tools_tab:
    st.markdown("### Các công cụ của agent")
    st.caption(f"Công cụ được đọc từ snapshot {version_name}.")
    for declaration in declarations:
        with st.expander(f"{declaration['name']}{' · Chỉ có trong eval, tắt ở UI' if declaration['name'] == 'send' else ''}"):
            st.write(declaration.get("description", ""))
            st.json(declaration["parameters"])

with demo_tab:
    st.markdown("### Demo → thử chéo → gom lỗi")
    st.caption(f"Mọi yêu cầu demo dùng phiên bản đang chọn: {version_name}. Chọn một mẫu rồi xem kết quả ở tab Trò chuyện; API thật sẽ được gọi.")
    samples = ["Tìm 2 tin tức về năng lượng tái tạo hôm nay trên web.",
               "Lấy 3 tweet mới nhất, tôi chưa cung cấp tài khoản.",
               "Chuẩn bị đăng bản tin lên Telegram, nhưng hỏi tôi trước khi thực hiện.",
               "Viết hàm Python giải bài tập Fibonacci cho tôi."]
    example = st.selectbox("Yêu cầu demo", samples, key="demo_example")
    if st.button("Chạy mẫu trong chat", key="run_demo"):
        st.session_state.demo_request = example
        st.rerun()
    st.markdown("#### Kịch bản thử chéo")
    st.write("Nhờ người khác dùng chủ đề, URL hoặc tài khoản chưa có trong bộ eval; thử sửa yêu cầu ở lượt sau, thiếu dữ liệu và hủy đăng. Ghi lại cách tái hiện, kỳ vọng và kết quả thay vì chỉ nhận xét đúng/sai.")
    st.caption("Suite cross là tự kiểm tra bằng API, không phải phản hồi của nhóm khác. UI chưa có link công khai; người thử có thể dùng UI trên máy này.")
    failures = []
    seen_suites = set()
    for path, run in matching_runs(active):
        run_suite = run.get("suite", "")
        if run_suite in seen_suites:
            continue
        seen_suites.add(run_suite)
        for case in run.get("results", []):
            if not case["result"]["passed"]:
                failures.append({"Suite": run_suite, "Ca": case["id"], "Lỗi": "; ".join(case["result"].get("failures", []))})
    st.markdown("#### Lỗi từ lần eval mới nhất của mỗi bộ")
    if failures:
        st.dataframe(failures, hide_index=True, use_container_width=True)
    else:
        st.info("Không có lỗi trong log hiện có; điều này không bảo đảm không còn lỗi thực tế.")
    st.markdown("#### Ghi nhận lỗi khi dùng thử")
    with st.form("manual_feedback"):
        steps = st.text_area("Cách tái hiện / câu hỏi", key="feedback_steps")
        expected = st.text_area("Kết quả mong đợi", key="feedback_expected")
        actual_result = st.text_area("Kết quả thực tế", key="feedback_actual")
        report_issue = st.form_submit_button("Lưu phản hồi")
    if report_issue:
        try:
            save_feedback(active, steps, expected, actual_result)
            st.success("Đã lưu phản hồi cùng phiên bản và hash để kiểm tra lại.")
        except (ValueError, OSError) as exc:
            st.error(str(exc))
    feedback = read_feedback(version_name)
    if feedback:
        st.dataframe([{k: r[k] for k in ["version", "status", "steps", "expected", "actual"]} for r in feedback], hide_index=True, use_container_width=True)
        st.download_button("Tải phản hồi JSON", json.dumps(feedback, ensure_ascii=False, indent=2), file_name=f"{version_name}_feedback.json", mime="application/json")
