# LinkedIn Post Generator

A 7-phase AI pipeline that turns a topic into a publish-ready LinkedIn post.
Stack: **FastAPI · CrewAI · React 19 · Vite**.

---

## What this replaces

Writing one LinkedIn post the right way — research, draft, edit, format, rhythm check — takes a senior engineer 30–45 minutes.

This pipeline produces a publish-ready post in under 60 seconds.

Nine deterministic Python checks run before the post is approved: word count, character limit, hashtag count, line length, banned openers, banned words, CTA count, wall-of-text detection, and packed-sentence detection.

No LLM is trusted to count or measure. Python does it. The LLM only writes.

---

## ⚠ Security — Rotate These Keys Now

The following API keys were committed in plaintext to `.env` before git-ignore was set up.
Even though `.env` is now git-ignored, the keys are in repository history and must be rotated:

| Key | Provider dashboard |
|---|---|
| `NVIDIA_API_KEY` | build.nvidia.com → API Keys |
| `GROQ_API_KEY` | console.groq.com → API Keys |
| `GEMINI_API_KEY` | aistudio.google.com → API keys |
| `OLLAMA_CLOUD_API_KEY` | your Ollama Cloud account |

Revoke each key, generate a replacement, and paste the new values into your local `.env`.

---

## How it works — 7-phase pipeline

```
Browser (React 19 + Vite)
        │
        │  WebSocket  ws://localhost:8000/api/ws/generate   (streaming)
        │  HTTP POST  /api/generate                         (sync)
        ▼
FastAPI  ·  app/main.py
        │
        ▼
LinkedInPipelineOrchestrator  ·  app/pipeline/orchestrator.py
        │
        ├─ 1 ─▶  HookFinderAgent          temp=0.8   max_tokens=1024
        │         Analyzes topic → 3 hook candidates → picks strongest
        │         Output: AnglePack  (topic, angle_type, hook_options[3],
        │                             selected_hook, cta_type)
        │         ↓  selected_hook is LOCKED here — never rewritten downstream
        │
        ├─ 2 ─▶  BodyWriterAgent           temp=0.7   max_tokens=2048
        │         Writes body only (status quo → teardown → framework → ROI)
        │         Hook passed as read-only context. No CTA, no hashtags.
        │         Output: BodyDraft  (body: str)
        │
        ├─ 3 ─▶  CTAWriterAgent            temp=0.7   max_tokens=512
        │         Writes closing CTA + 3–5 hashtags only
        │         Hook + body passed as read-only context.
        │         Output: CTADraft  (cta: str, hashtags: list[str])
        │
        ├─ 4 ─▶  assemble_post()           pure Python — NO LLM
        │         Concatenates hook + body + cta + #hashtags with \n\n
        │         Output: full_post string
        │
        ├─ 5 ─▶  Edit loop  (max 2 cycles, skipped when QA passes)
        │         ├─ LinkedInQAChecker.check()  ← deterministic Python only
        │         │    9 checks: word count (200–280), char count (≤3,000),
        │         │              hashtag count (3–5), line length (≤12 words),
        │         │              banned opener, banned words, CTA count,
        │         │              wall-of-text, packed-sentence
        │         └─ LinkedInEditorAgent    temp=0.3   max_tokens=4096
        │              Rewrites to fix each failed QA rule.
        │              LINKEDIN_STYLE_SPEC + failed-rule list both injected.
        │
        ├─ 6 ─▶  LinkedInQAChecker.check()    final measurement pass
        │
        └─ 7 ─▶  LinkedInApproverAgent         pure Python — NO LLM
                  Maps QA pass/fail keys → ApprovalResult
                  Output: ApprovalResult  (approved, reasons, checklist)
```

LLM `.call()` runs inside `asyncio.to_thread` — the event loop never blocks.
No task queue; everything runs synchronously inside the FastAPI worker.

---

## Project layout

```
linkedin-post-generator/
│
├── app/
│   ├── main.py              FastAPI app, CORS, lifespan
│   ├── config.py            Pydantic Settings — reads .env, singleton via get_settings()
│   ├── llm.py               build_llm() — maps provider string → crewai.LLM with fallback
│   ├── linkedin_client.py   LinkedIn OAuth + Posts API — get_auth_url, exchange_code, get_userinfo, post_content
│   ├── routers/
│   │   ├── generate.py      GET /health · POST /generate · WS /ws/generate
│   │   └── linkedin.py      GET /api/linkedin/auth · GET /callback · POST /api/linkedin/post
│   └── pipeline/
│       ├── orchestrator.py  LinkedInPipelineOrchestrator — drives all 7 phases
│       ├── hook_finder.py   Phase 1 · HookFinderAgent → AnglePack
│       ├── body_writer.py   Phase 2 · BodyWriterAgent → BodyDraft
│       ├── cta_writer.py    Phase 3 · CTAWriterAgent → CTADraft
│       ├── post_writer.py   Phase 4 · assemble_post() — no LLM
│       ├── editor.py        Phase 5 · LinkedInEditorAgent → EditedPost
│       ├── qa_checker.py    Phases 5+6 · LinkedInQAChecker — 9 Python checks
│       ├── approver.py      Phase 7 · LinkedInApproverAgent — pure Python
│       ├── schemas.py       Pydantic contracts for every inter-agent payload
│       ├── style_spec.py    LINKEDIN_STYLE_SPEC constant (injected into agents 2, 3, 4)
│       └── utils.py         make_llm() · call_llm_with_retry() · extract_json()
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 WebSocket client + state machine (idle/connecting/running/done/error)
│   │   ├── components/
│   │   │   ├── GenerateForm.jsx    Topic, niche, provider inputs
│   │   │   ├── PipelineProgress.jsx  5-step live progress bar + step log
│   │   │   └── PostResult.jsx      Final post + metadata badges + copy button · Post to LinkedIn button
│   │   └── main.jsx                React 19 entry point
│   ├── index.html
│   └── package.json                React 19.2 · Vite 8
│
├── .env.example             Env template — placeholder values only, no real keys
├── .env                     Local secrets — git-ignored, never commit
├── .gitignore
└── requirements.txt
```

---

## Writing-style system

### Where style lives

`app/pipeline/style_spec.py` holds four module-level constants:

| Constant | Used at runtime? | Description |
|---|---|---|
| `LINKEDIN_STYLE_SPEC` | **Yes** | Blended ruleset focusing on rhythm, hook structure, density, and banned words |
| `LINKEDIN_STYLE_CHECKLIST` | No — docs only | 11 human-readable rule labels |
| `LINKEDIN_REGEX_CHECKLIST` | No — docs only | 8 regex-oriented rule labels |
| `LINKEDIN_SEMANTIC_CHECKLIST` | No — docs only | 5 semantic rule labels |

One fixed style applies to all requests. There is no per-request style selection.

### Style injection per agent

Prompt ordering in every agent: **role → input → rules → `LINKEDIN_STYLE_SPEC` → schema hint**.
Schema hint is always last (recency bias — closest to generation).

| Agent | `LINKEDIN_STYLE_SPEC` injected? | Notes |
|---|---|---|
| HookFinder | No | Hook/angle rules are hard-coded in `HOOK_FINDER_PROMPT`; consistent with the spec |
| BodyWriter | **Yes** (`body_writer.py:BODY_WRITER_PROMPT`) | Enforces engaging rhythm, anti-wall-of-text |
| CTAWriter | **Yes** (`cta_writer.py:CTA_WRITER_PROMPT`) | Enforces single-CTA and hashtag rules |
| Editor | **Yes** (`editor.py:EDITOR_PROMPT`) | Preserves voice while fixing QA violations |
| Approver | n/a — no LLM | Pure Python |

### Per-agent temperatures

| Agent | Temp | Constant | Location |
|---|---|---|---|
| HookFinder | **0.8** | `HOOK_FINDER_TEMPERATURE` | `hook_finder.py:16` |
| BodyWriter | **0.7** | `BODY_WRITER_TEMPERATURE` | `body_writer.py:19` |
| CTAWriter | **0.7** | `CTA_WRITER_TEMPERATURE` | `cta_writer.py:19` |
| Editor | **0.3** | `EDITOR_TEMPERATURE` | `editor.py:18` |
| Approver | — | no LLM | — |

`make_llm()` (`utils.py`) builds the LLM with the global `LLM_TEMPERATURE` and then immediately overwrites `llm.temperature` with the per-agent constant. The env var is loaded but has no effect at runtime.

### QA checks — all deterministic Python (`qa_checker.py`)

| Check | Threshold | Pass key |
|---|---|---|
| Word count | 200–280 words (hashtag lines excluded) | `passes_word_count` |
| Char count | ≤ 3,000 characters (LinkedIn hard cap) | `passes_char_count` |
| Hashtag count | 3–5 | `passes_hashtag_count` |
| Line length | ≤ 12 words per non-hashtag line | `passes_line_length` |
| Banned opener | Not one of 8 hard-coded openers | `passes_hook` |
| Banned words | None of 16 banned words/phrases | `passes_banned_words` |
| CTA count | Exactly 1 (`?` marks + soft-ask phrases) | `passes_cta` |
| Wall of text | No paragraph with > 3 non-blank lines | `passes_white_space` |
| Packed sentences | No line contains 3+ independent sentences without a line break | `passes_packed_sentences` |

`overall_pass` is `True` only when all 9 keys are `True`.

---

## Supported LLM providers

| `provider` value | Model | Requires |
|---|---|---|
| `ollama` *(default)* | `gemma4:31b-cloud` via `OLLAMA_API_BASE` | Local Ollama |
| `ollama/<model>` | Any model name served by Ollama | Local Ollama |
| `groq` | `groq/llama-3.3-70b-versatile` | `GROQ_API_KEY` |
| `openai` | `gpt-4o` | `OPENAI_API_KEY` |
| `anthropic` | `anthropic/claude-3-5-sonnet-latest` | `ANTHROPIC_API_KEY` |
| `google` | `gemini/gemini-3.5-flash` | `GEMINI_API_KEY` |
| `nvidia` | `openai/z-ai/glm-5.1` | `NVIDIA_API_KEY` |

Any provider that fails to initialise (missing key, network error) silently falls back to Ollama.

Per-provider output-token ceilings enforced in `make_llm()`: Groq 32,000 · NVIDIA 16,384 · Ollama 16,384.

---

## Setup

### Backend

```bash
# 1. Create virtualenv and install deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env: set DEFAULT_PROVIDER and whichever API keys you need

# 3. (Ollama only) pull the default model
ollama pull gemma4:31b-cloud

# 4. Start API server
uvicorn app.main:app --reload --port 8000
```

- API root: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
# or
npm run build      # production build → frontend/dist/
```

> The WebSocket URL is hardcoded to `ws://localhost:8000/api/ws/generate` in `App.jsx:7`.
> Any non-localhost deployment needs a reverse proxy or a build-time env replacement.

---

## Environment variables

| Variable | Default | Notes |
|---|---|---|
| `DEFAULT_PROVIDER` | `ollama` | Used when `provider` is absent from the request |
| `OLLAMA_API_BASE` | `http://127.0.0.1:11434` | Ollama server address |
| `LLM_TEMPERATURE` | `0.6` | Loaded into config but **overridden by per-agent constants** — has no runtime effect |
| `LLM_MAX_TOKENS` | `4096` | Global fallback; per-agent values and provider caps take precedence |
| `LLM_TIMEOUT` | `300` | Seconds before LLM call times out |
| `GROQ_API_KEY` | — | |
| `OPENAI_API_KEY` | — | |
| `ANTHROPIC_API_KEY` | — | |
| `GEMINI_API_KEY` | — | |
| `NVIDIA_API_KEY` | — | |
| `LINKEDIN_CLIENT_ID` | — | OAuth app client ID from developer.linkedin.com |
| `LINKEDIN_CLIENT_SECRET` | — | OAuth app client secret — never sent to frontend |
| `LINKEDIN_REDIRECT_URI` | `http://localhost:8000/callback` | Must match a URI registered in your LinkedIn app |

---

## API reference

### `GET /api/health`
```json
{ "status": "ok" }
```

### `POST /api/generate`
Request body:
```json
{ "topic": "string (required)", "niche": "string (default: ai)", "provider": "string | null" }
```
Runs the full pipeline synchronously. Returns the response shape below.

### `WebSocket /api/ws/generate`
1. Connect, then send one JSON message: `{ "topic", "niche", "provider" }`.
2. Receive a stream:
   - `{ "type": "step", "agent": "LinkedIn Body Writer", "task": "Write Post Body", "output": "..." }`
   - `{ "type": "done", "result": { … } }`
   - `{ "type": "error", "message": "…" }`

**Response shape** (both transports):
```json
{
  "post_text":        "full assembled post text",
  "hook":             "first non-empty line of final post",
  "angle_type":       "story | contrarian | how-to | lesson-learned",
  "word_count":       214,
  "char_count":       1287,
  "hashtag_count":    4,
  "approved":         true,
  "approval_reasons": [],
  "qa_results": {
    "passes_word_count": true,
    "passes_char_count": true,
    "passes_hashtag_count": true,
    "passes_line_length": true,
    "passes_hook": true,
    "passes_banned_words": true,
    "passes_cta": true,
    "passes_white_space": true,
    "passes_packed_sentences": true,
    "overall_pass": true
  },
  "cycles_taken": 1
}
```

Step emissions visible in the WebSocket stream:

| Agent name in stream | Task name |
|---|---|
| `LinkedIn Hook Finder` | `Find Angle & Hooks` |
| `LinkedIn Body Writer` | `Write Post Body` |
| `LinkedIn CTA Writer` | `Write CTA & Hashtags` |
| `LinkedIn Assembler` | `Assemble Full Post` |
| `LinkedIn QA Checker` | `Python QA cycle N` / `Final Python QA` |
| `LinkedIn Editor` | `Edit cycle N` |
| `LinkedIn Approver` | `Final Approval` |

### LinkedIn OAuth & Posting

#### `GET /api/linkedin/auth`
Redirects to LinkedIn consent screen. Requires `LINKEDIN_CLIENT_ID` and `LINKEDIN_REDIRECT_URI` in `.env`.

#### `GET /callback`
Handles the OAuth redirect. Exchanges the auth code for an access token, fetches the user ID via `/v2/userinfo`, then redirects the browser to `http://localhost:5173/?li_token=...&li_uid=...`.

The frontend picks up those params on mount, restores any pending post from `sessionStorage`, and shows the **Post to LinkedIn** button.

#### `POST /api/linkedin/post`
Request body:
```json
{ "post_text": "...", "access_token": "...", "author_urn": "urn:li:person:..." }
```
Posts directly to LinkedIn via the REST Posts API (`/rest/posts`, version `202501`). Returns `{ "success": true, "post_id": "..." }`.

The access token is never stored on the server — it lives in the browser and is passed back with each post request.

---

## Known gaps

| Gap | Impact | Notes |
|---|---|---|
| **No research engine** | `trending_context` is always `""` (`orchestrator.py:53`) | The `HookFinderAgent.run()` signature accepts it; wiring a real source would improve hook relevance immediately |
| **Frontend WS URL hardcoded** | Breaks in any non-localhost deploy | `App.jsx:7` — needs a reverse proxy or `VITE_WS_URL` env substitution at build time |
| **`LLM_TEMPERATURE` env var silently ignored** | Potential confusion during debugging | Per-agent constants (0.8 / 0.7 / 0.3) always win inside `make_llm()` |
| **No persistence** | Posts not saved; each request is stateless | No DB, no cache layer |
| **Dead-code checklists** | `LINKEDIN_REGEX_CHECKLIST`, `LINKEDIN_SEMANTIC_CHECKLIST`, `LINKEDIN_STYLE_CHECKLIST` defined but never called | Kept as documentation of style intent |
| **`LinkedInApproverAgent` accepts `llm_provider` but ignores it** | Harmless | Kept for constructor-signature consistency with other agents |
