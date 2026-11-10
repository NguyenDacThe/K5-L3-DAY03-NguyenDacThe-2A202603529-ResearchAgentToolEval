"""Streamlit UI for the Research Agent.

Run with:
    streamlit run app.py

It reuses the same tool loop as chat.py, so the chat behaves exactly like the CLI
(including the send-confirmation guardrail and the clarify-when-missing behaviour).
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from chat import run_model_tool_loop
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
VERSIONS_DIR = ARTIFACTS_DIR / "versions"
load_lab_env(ROOT)

st.set_page_config(page_title="Research Agent", page_icon="🔎")
st.title("🔎 Research Agent")
st.caption("Tìm tin / mạng xã hội / Hacker News, đọc URL, tra policy, tổng hợp digest.")

# Danh sách model LLM gợi ý cho mỗi provider.
PROVIDER_MODELS = {
    "openrouter": ["openai/gpt-4o-mini", "openai/gpt-4o", "anthropic/claude-3-5-sonnet", "google/gemini-2.0-flash-exp"],
    "openai": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
    "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
    "gemini": ["gemini-2.0-flash", "gemini-2.5-pro-exp"],
    "ollama": ["qwen2.5:7b", "llama3.1:8b", "gemma2:9b"],
}


def _list_versions() -> list[str]:
    """Liệt kê các phiên bản agent theo thứ tự v0, v1, ... (snapshot trong artifacts/versions)."""
    versions: list[str] = []
    if VERSIONS_DIR.exists():
        for child in sorted(VERSIONS_DIR.iterdir()):
            if child.is_dir() and (child / "system_prompt.md").exists():
                versions.append(child.name)
    return versions


@st.cache_resource(show_spinner=False)
def load_agent_config(provider_name: str, version: str):
    version_dir = VERSIONS_DIR / version if version else None
    prompt_path = version_dir / "system_prompt.md" if version_dir and (version_dir / "system_prompt.md").exists() else (ARTIFACTS_DIR / "system_prompt.md")
    tools_path = version_dir / "tools.yaml" if version_dir and (version_dir / "tools.yaml").exists() else (ARTIFACTS_DIR / "tools.yaml")
    system_prompt = prompt_path.read_text(encoding="utf-8")
    tools = to_openai_tools(load_tool_declarations(tools_path))
    provider = make_provider(provider_name)
    return system_prompt, tools, provider


with st.sidebar:
    provider_name = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini", "ollama"])
    available_versions = _list_versions()
    version = st.selectbox(
        "Version",
        options=available_versions,
        index=max(0, len(available_versions) - 1),
        help="Phiên bản agent (v0 baseline → v4 tốt nhất). Mỗi version dùng cặp system_prompt.md + tools.yaml riêng trong artifacts/versions/vN/.",
    )
    st.caption(f"Đang dùng artifacts: `artifacts/versions/{version}/`")

try:
    system_prompt, tools, provider = load_agent_config(provider_name, version)
except Exception as exc:  # provider/key not configured yet
    st.error(f"Không khởi tạo được provider '{provider_name}': {type(exc).__name__}: {exc}")
    st.stop()

with st.sidebar:
    default_model = getattr(provider, "default_model", None) or ""
    model_options = PROVIDER_MODELS.get(provider_name, [])
    if default_model and default_model not in model_options:
        model_options = [default_model, *model_options]
    model = st.selectbox(
        "LLM Model",
        options=model_options or [default_model or ""],
        index=model_options.index(default_model) if default_model in model_options else 0,
        help="Tên model LLM thực thi (gọi API). Khác với Version ở trên.",
    )
    history_window = st.slider("History window", min_value=1, max_value=10, value=5)
    max_tool_rounds = st.slider("Max tool rounds", min_value=1, max_value=8, value=4)
    st.caption("Đọc key từ `.env` (TAVILY / FIRECRAWL / RAPIDAPI / provider key).")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Hỏi gì đó, ví dụ: 'Trên Hacker News mọi người bàn gì về Rust?'")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    history = st.session_state.messages[:-1]
    messages = [
        {"role": "system", "content": system_prompt},
        *history[-history_window * 2:],
        {"role": "user", "content": prompt},
    ]

    with st.chat_message("assistant"):
        with st.spinner("Đang xử lý..."):
            try:
                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=tools,
                    model=model or None,
                    max_tool_rounds=max_tool_rounds,
                )
            except Exception as exc:
                st.error(f"Lỗi provider: {type(exc).__name__}: {exc}")
                st.stop()

        for event in result["tool_events"]:
            st.caption(f"🔧 {event['tool']}({event['args']})")
        if result["status"] == "waiting_for_user":
            st.info(result["assistant_text"])
        else:
            st.markdown(result["assistant_text"] or "")

    st.session_state.messages.append({"role": "assistant", "content": result["assistant_text"] or ""})
