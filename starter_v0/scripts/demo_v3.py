"""Run a reproducible five-turn live API demo; publication execution is blocked."""
from pathlib import Path
import sys
from types import SimpleNamespace
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chat import now_iso, run_model_tool_loop, write_transcript
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from version_store import get_version


def main():
    version = get_version("v3")
    provider = make_provider("openrouter")
    def readonly_complete(*args, **kwargs):
        response = provider.complete(*args, **kwargs)
        if any(call.name == "send" for call in response.tool_calls):
            raise RuntimeError("Publication execution is blocked in the demo")
        return response
    tools = to_openai_tools(load_tool_declarations(version["tools_path"]))
    queries = [
        'Tóm tắt ngắn từ dữ liệu đã có, không tìm web: [{"title":"Nguồn A","url":"https://example.com/a","summary":"Dự án nghiên cứu đã công bố dữ liệu thử nghiệm."},{"title":"Nguồn B","url":"https://example.org/b","summary":"Báo cáo mô tả các giới hạn của bộ dữ liệu."}]. Dùng format với template brief.',
        "Lấy 2 tweet mới nhất, tôi chưa cung cấp tài khoản.",
        "Tài khoản sama, lấy 2 tweet mới nhất.",
        "Tôi muốn đăng bản tin lên Telegram nhưng chưa cung cấp nội dung hoặc kênh. Hãy hỏi trước.",
        "Không. Hủy việc đăng và chỉ xác nhận đã hủy, không thực hiện hành động nào nữa.",
    ]
    transcript = {k: version[k] for k in ["version", "artifact_version", "prompt_hash", "tools_hash"]}
    transcript.update(transcript_id=f"v3_live_demo_{uuid4().hex}", provider="openrouter",
                      model=provider.default_model, created_at=now_iso(), turns=[],
                      source="automated_live_demo_not_human_peer_review", publication_execution="blocked",
                      supplied_demo_sources="Synthetic source snippets; not real research findings")
    path = ROOT / "transcripts" / f"{transcript['transcript_id']}.transcript.json"
    history = []
    for index, query in enumerate(queries, 1):
        turn = {"turn_index": index, "user": query, "started_at": now_iso()}
        try:
            result = run_model_tool_loop(provider=SimpleNamespace(complete=readonly_complete),
                messages=[{"role": "system", "content": version["prompt"]}, *history,
                          {"role": "user", "content": query}], tools=tools, model=None, max_tool_rounds=4)
            turn.update(result)
            history.extend([{"role":"user","content":query},
                            {"role":"assistant","content":result["assistant_text"]}])
        except Exception as exc:
            turn.update(status="error", error=type(exc).__name__)
        turn["ended_at"] = now_iso()
        transcript["turns"].append(turn)
        write_transcript(path, transcript)
        print(f"Demo turn {index}: {turn['status']}", flush=True)
    print(f"Saved: {path}")


if __name__ == "__main__":
    main()
