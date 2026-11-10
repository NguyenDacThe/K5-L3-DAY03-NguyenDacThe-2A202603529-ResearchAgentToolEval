from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import streamlit as st

from chat import now_iso, run_model_tool_loop, trim_history, write_transcript
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version
from ui_errors import describe_error

ROOT = Path(__file__).resolve().parent


class ResearchOnlyProvider:
    """Restrict the demo to declared research tools, including hallucinated calls."""

    def __init__(self, provider, allowed):
        self.provider = provider
        self.allowed = allowed

    def complete(self, *args, **kwargs):
        response = self.provider.complete(*args, **kwargs)
        if any(call.name not in self.allowed for call in response.tool_calls):
            raise RuntimeError("Model requested a tool unavailable in this research demo.")
        return response


def main():
    st.set_page_config(page_title="Research Lab | Trợ lý nghiên cứu", page_icon="🔎", layout="centered")
    load_lab_env(ROOT)
    st.markdown("**RESEARCH LAB** · Tìm hiểu với nguồn dẫn")
    st.title("Từ câu hỏi đến thông tin.")
    st.caption("Tìm tin trên web, khám phá bài đăng và đọc tài liệu trong một cuộc trò chuyện.")

    with st.sidebar:
        st.header("Không gian nghiên cứu")
        version = st.selectbox("Phiên bản thử nghiệm", ["v3", "v2", "v1", "v0"])
        st.caption("xkiro · Model lấy từ cấu hình .env")
        reset = st.button("Cuộc trò chuyện mới", use_container_width=True)
        st.divider()
        st.markdown("**Bạn có thể thử**")
        st.markdown("- Tin AI hôm nay có gì?\n- Tóm tắt 3 tweet của @sama.\n- Tóm tắt bài viết này giúp mình.")
        st.caption("Gửi thêm URL hoặc tài khoản khi trợ lý hỏi lại. Telegram không bật trong giao diện này.")

    artifacts = ROOT / "artifacts" / "versions" / version
    prompt_path, tools_path = artifacts / "system_prompt.md", artifacts / "tools.yaml"
    artifact = artifact_version_dict(build_artifact_version(version, prompt_path, tools_path))
    if reset or st.session_state.get("artifact_id") != artifact["artifact_version"]:
        st.session_state.artifact_id = artifact["artifact_version"]
        st.session_state.history = []
        st.session_state.transcript = {
            "transcript_id": f"ui_{version}_{uuid4().hex}",
            **artifact, "provider": "xkiro", "interface": "streamlit",
            "disabled_tools": ["send"], "created_at": now_iso(), "turns": [],
        }

    transcript = st.session_state.transcript
    for turn in transcript["turns"]:
        with st.chat_message("user"):
            st.markdown(turn["user"])
        with st.chat_message("assistant"):
            st.markdown(turn["assistant_text"])
            if turn.get("error_type"):
                code = turn["error_type"]
                if turn.get("http_status"):
                    code += f" · HTTP {turn['http_status']}"
                st.caption(f"Mã lỗi: {code}")
            if turn.get("tool_events"):
                with st.expander("Nguồn và công cụ đã dùng"):
                    st.json(turn["tool_events"])

    query = st.chat_input("Bạn muốn tìm hiểu điều gì?")
    if query:
        turn = {"turn_index": len(transcript["turns"]) + 1, "user": query, "started_at": now_iso()}
        with st.chat_message("user"):
            st.markdown(query)
        with st.chat_message("assistant"):
            with st.spinner("Đang tìm hiểu yêu cầu…"):
                try:
                    provider = make_provider("xkiro")
                    transcript["model"] = provider.default_model
                    declarations = [t for t in load_tool_declarations(tools_path) if t["name"] != "send"]
                    guarded = ResearchOnlyProvider(provider, {t["name"] for t in declarations})
                    messages = [
                        {"role": "system", "content": prompt_path.read_text(encoding="utf-8")},
                        *trim_history(st.session_state.history, 5),
                        {"role": "user", "content": query},
                    ]
                    result = run_model_tool_loop(provider=guarded, messages=messages,
                        tools=to_openai_tools(declarations), model=None, max_tool_rounds=4)
                    turn.update(result)
                    st.session_state.history.extend([
                        {"role": "user", "content": query},
                        {"role": "assistant", "content": result["assistant_text"]},
                    ])
                except Exception as exc:
                    # Do not surface raw provider messages that might contain credentials.
                    turn.update(status="provider_error", **describe_error(exc),
                        rounds=[], tool_events=[])
        turn["ended_at"] = now_iso()
        transcript["turns"].append(turn)
        write_transcript(ROOT / "transcripts" / f"{transcript['transcript_id']}.transcript.json", transcript)
        st.rerun()

    if transcript["turns"]:
        st.download_button("Tải lịch sử nghiên cứu (JSON)",
            data=json.dumps(transcript, ensure_ascii=False, indent=2),
            file_name=f"{transcript['transcript_id']}.transcript.json", mime="application/json")
    else:
        st.info("Bắt đầu bằng một chủ đề, tài khoản hoặc đường dẫn bài viết.")


if __name__ == "__main__":
    main()
