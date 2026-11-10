# UI validation — 2026-11-10

Command: `.\.venv\Scripts\python.exe -m pytest -q`

Observed result: **65 passed, 17 skipped in 3.03s**.
The 17 skips are the existing student TODO tests; they remain unfinished.

Three new offline Streamlit AppTest checks passed:

1. Clarify pauses, the next user message retains conversation history, transcript
   contains both turns, and changing version/reset starts a new conversation.
2. A model attempting to call the disabled Telegram tool is blocked before execution.
3. Raw provider exception contents are not displayed or saved in UI transcripts.

Server smoke check:

```text
python -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8501
GET http://127.0.0.1:8501/_stcore/health -> ok
GET http://127.0.0.1:8501 -> HTTP 200
```

UI behavior was validated with AppTest and a local server health check.
No visual browser inspection or live UI model conversation was performed.
These tests use a fake provider and do not count as the required 3 live chat turns.
The temporary smoke-test server is stopped after validation; start it using UI-README.md.

Real model evaluation is recorded separately in `runs/v0_*.json` and `runs/v1_*.json`.
The v1 run has two provider errors and does not establish an improvement over v0.

## Follow-up: user-reported live failure

The user's original transcript `ui_v1_2ce820f86883485c9c9a8dfe0a80e518.transcript.json`
records `APIConnectionError`, not an authentication failure. A subsequent authenticated
xkiro request succeeded. The exact transient connection cause was not established.

During live AppTest reproduction, Windows console logging raised UnicodeEncodeError
before tool execution. Fixed chat.py logging to emit ASCII-safe JSON. UI now displays
safe error categories and HTTP status without exposing raw response payloads.

Validation after fix: **68 passed, 17 skipped in 3.14s**.

Live AppTest with the same Vietnamese request succeeded:
`transcripts/ui_v1_bd265e80d1234a798d0d942d6ec45508.transcript.json`.
Status `answered`, no UI exceptions. Model called timeline with @sama first (tool
JSONDecodeError), corrected to sama, then called format and returned an answer.
This is one automated live UI turn, not the required three manual chat turns.
No prompt snapshot or base eval was changed by this UI/logging fix.
