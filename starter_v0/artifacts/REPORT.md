# Research Agent ? Nguyen Dac The

## Part A ? Quick introduction

This agent researches public web and X sources, reads supplied URLs, searches local company policies and arXiv, and formats retrieved material into a digest. It asks for missing information and requires explicit confirmation before sending to Telegram.

| Tool | Purpose |
|---|---|
| clarify | Ask for missing or ambiguous information |
| timeline | Retrieve recent posts from a named X account |
| social_search | Search X posts by keywords, sorted Latest or Top |
| lookup | Search general web or news, optionally time filtered |
| fetch | Read a supplied URL |
| format | Format already retrieved evidence as a digest |
| send | Send a confirmed message to configured Telegram |
| policy | Search local company policy files |
| papers | Search arXiv |
| paper_text | Extract text from a known arXiv paper |
| summarize_sources | Count supplied items by source/domain locally |

Try: ?Find this week?s news about AI research in Vietnam and make a three item digest?; ?Show recent posts from @OpenAI?; ?What does our data privacy policy say about personal data??

**Local demo:** http://127.0.0.1:8502 (Streamlit, bound to localhost). No public deployment was created.

## Part B ? Evidence

### B1. Version evidence

Provider: xKiro. Selected model: `mistralai/mistral-large-2512`. Base URL: `https://api.xkiro.com/v1`; change the model with `XKIRO_MODEL` in the local `.env`.

| Version | Base suite result | Notes |
|---|---:|---|
| v0 | 17/20 (85%) | Baseline |
| v1 | 16/18 measured | 2 provider conflicts; v1 recheck passed 17/19 measured with 1 provider conflict |
| v2 | 16/20 (80%) | Lower than baseline |
| v3 | 16/20 (80%) | No gain from declaration-only change |
| v4 | 18/19 measured | 1 provider conflict |
| v5 | 18/20 (90%) | |
| v6 | 19/20 (95%) | |
| v7 | 20/20 (100%) | Latest complete base run |

The v7 improvement includes a narrow provider adapter repair: when the model emits a prose function name with `action=stop`, a question mark, and no valid function name, the adapter maps it to the non-side-effecting `clarify` tool. Unknown actions remain unknown. The regression tests cover these rules. Exact hashes and run paths are in `artifacts/version_log.csv` and `runs/`.

### B2. Remaining eval status

The v8 group rerun measured 7 cases and passed all 7; three cases errored. One error exposed an eval comparator bug for lists of dictionaries, now fixed and covered by a test. The other two hit xKiro's daily free-token quota. The prior v7 group run passed 8/10 with no provider errors. The g05 eval input now includes actual source items, and the prompt now says to use a user's answer to an earlier clarification instead of asking again. Rerun `python run_eval.py --provider xkiro --version v8 --suite group --eval-cases data/eval_group.json` after the free quota resets. No paid model was substituted.

The first v1 recheck also had one provider conflict (17/19 measured). Rerun it after quota reset if a complete comparison is needed. The latest complete base result is v7, 20/20. The current prompt includes an additional multi-turn follow-up rule from v8; its base suite has not been rerun yet.

### B3. Failure analysis

The early base failures were: R03 expanded the search query beyond the user's term; R10/R11 did not consistently call `clarify`; R12 used `response_type=text` instead of `yes_no`. Few-shot examples improved R03 and R10/R12. The malformed clarification normalization cleared R11 in v7. The base v7 run had no failures.

### B4. Team eval

`data/eval_group.json` has ten cases, five single-turn and five multi-turn. The latest group run is quota-limited as described above. See `runs/v7_B_group_xkiro_20261110T120453266866.json` and `runs/v8_B_group_xkiro_20261110T120851110864.json`.

### B5. Live chat and source review

Four live turns are recorded in `transcripts/v3_xkiro_20261110T110620735791.transcript.json`: web lookup plus digest formatting, local policy search, clarification for a missing X account, and timeline retrieval after the user supplied `OpenAI`.

I spot-checked the digest's five source links. Nippon.com and VietnamPlus support the Vietnam?Japan AI/semiconductor cooperation summary. The Viet Nam News item is about AI in communications and brand visibility; its national-policy connection is narrower than the digest wording suggests. The FPT/Quantum Zeitgeist article is discoverable at [this URL](https://quantumzeitgeist.com/fpt-proposes-quantum-leap-ways-tech/); the transcript URL omitted the trailing slash. The transcript's VIR link was the wrong article (Korean firms' investment plans); the summit information is at [the correct VIR article](https://vir.com.vn/first-vietnam-south-korea-ai-and-semiconductor-conference-set-to-open-164629.html). The OpenAI Control Room and GPT-6 Cyber claims in the X digest have corresponding [official Control Room](https://openai.com/index/introducing-control-room/) and [official GPT-6 Cyber](https://openai.com/index/introducing-gpt-6-cyber/) posts. Other X claims were not independently verified.

### B6. UI, tools, and tests

The Streamlit UI is available locally at `http://127.0.0.1:8502`; it is bound to localhost. `AppTest` reports 0 exceptions and the health endpoint returns HTTP 200. I fixed the environment-loader argument error and a Windows console Unicode crash in chat output. A public deployment was not created; exposing the unauthenticated UI would expose provider-backed tool access.

Added `summarize_sources`, a local-only source/domain counter. Completed the starter TODO tool tests and added regression coverage for malformed provider tool calls and dictionary-list eval comparison. Final offline suite: **91 passed, 0 failed, 0 skipped**.

### B7. Local model challenge

Not run. Ollama model comparison remains optional.
