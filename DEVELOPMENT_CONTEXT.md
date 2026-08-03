# Development Context — ShipReady AI

> **Purpose of this file:** a self-contained handoff so a new chat/agent
> session can continue this project without re-reading the entire prior
> conversation history. Treat this as the current source of truth on
> project status — `README.md`, `ARCHITECTURE.md`, and `PRODUCT_VISION.md`
> contain some now-stale language (e.g. "scaffold only") left over from
> earlier sprints; see [Documentation staleness](#documentation-staleness-known-issue)
> below.

---

## 1. Project overview

**ShipReady AI** is an AI-powered **Change Advisory Board (CAB)** that
helps engineering teams decide whether a software change is ready for
production. Instead of one large AI prompt, it orchestrates multiple
single-responsibility reviewer agents (Architecture, Security, QA,
Operations), then a CAB agent synthesizes their findings into one release
decision.

The project's real purpose (per `PROJECT_CHARTER.md` / `PRODUCT_VISION.md`)
is to **demonstrate AI orchestration engineering using the Cursor SDK** —
decomposing a judgment task into independent specialist agents, defining
strict typed contracts between them, and coordinating their execution. It
is explicitly *not* a code-generation demo, not a CI/CD gate, and not a
general static analysis tool.

**V1 scope** (from `PROJECT_CHARTER.md`):
- **Inputs:** Git diff, Pull Request description.
- **Review specialists:** Architecture, Security, QA, Operations.
- **Final decision:** Change Advisory Board (CAB).
- **Outputs:** Executive summary, findings, recommendations, release decision.
- **Non-goals for V1:** GitHub/Jira/Slack integration, cloud deployment, CI/CD integration.

---

## 2. Current architecture

Full technical rationale lives in `ARCHITECTURE.md` (still largely
accurate in its *design intent*, even where it describes things as
"planned" that are now partially implemented — see staleness note).

**Data flow (fan-out / fan-in):**

```
User → ui/dashboard.py → SubmissionInput
                              │
        ┌──────────┬──────────┼──────────┐
        ▼          ▼          ▼          ▼
   Architecture  Security    QA      Operations   (run in this fixed order,
        │          │          │          │          NOT concurrently yet)
        ▼          ▼          ▼          ▼
   ReviewResult ReviewResult ReviewResult ReviewResult
        └──────────┴──────────┴──────────┘
                       ▼
                 CAB reviewer  (receives ONLY the 4 ReviewResults —
                       │        never the diff/SubmissionInput)
                       ▼
                ReleaseDecision → back to dashboard
```

**Layers:**
- `models/` — typed Pydantic contracts shared by every stage.
- `reviewers/` — one module per persona, each exposing a `review(...)` function. Four take `SubmissionInput`; `cab.py` takes `List[ReviewResult]` only.
- `orchestrator/` — the *only* module that knows the pipeline shape/order. Reviewers never call each other.
- `ui/` — Streamlit presentation only; never constructs prompts or calls an SDK.
- `config.py` — single source of truth for tunable settings, loaded from environment variables (`.env`) with defaults.
- `prompts/` — persona prompt templates as markdown data. `architecture.md` is real content as of Sprint 6 (loaded by `reviewers/architecture.py`); the other four are still empty placeholders.

**The single most important invariant:** the CAB reviewer's function
signature (`review(review_results: List[ReviewResult])`) makes it
*impossible* to pass it the raw diff — this is a type-level guarantee, not
just a convention. Do not weaken this when adding real SDK calls.

**Cursor SDK integration — call flow (Sprint 7, current):**

`reviewers/architecture.py` is the only reviewer that talks to a real
Cursor SDK agent. As of Sprint 7 this is a direct, in-process call — the
whole project targets Python 3.12 (see §9), so there is no interpreter
mismatch to work around and no subprocess involved:

```
reviewers/architecture.py::review(submission)
    │
    ├─ loads prompts/architecture.md, appends
    │  submission.diff_text / pr_description
    │
    ├─ from cursor_sdk import Agent, AgentOptions, CursorAgentError, LocalAgentOptions
    ├─ Agent.prompt(prompt, AgentOptions(api_key=config.CURSOR_API_KEY,
    │                                    model=config.CURSOR_SDK_MODEL,
    │                                    local=LocalAgentOptions(cwd=os.getcwd())))
    │
    ├─ on CursorAgentError, or result.status == "error":
    │      return a safe ReviewResult(verdict="block", summary=<error>)
    ├─ else: json.loads(result.result) → expects
    │  {"verdict", "summary", "findings": [...]}
    │  and builds a real ReviewResult/Finding (pydantic-validated);
    │  malformed/non-JSON output also collapses to a safe "block" result
    │
    └─ returns ReviewResult   (same shape orchestrator/pipeline.py and
                                cab.py always expected — they don't know
                                or care that this one is real)
```

Every failure mode (auth/network `CursorAgentError`, `result.status ==
"error"`, or a model response that isn't the expected JSON shape) is
caught inside `review()` and converted into a valid, safe
`ReviewResult(verdict="block", ...)` — it never raises, because
`orchestrator/pipeline.py` (unmodified since Sprint 3) has no try/except
around reviewer calls.

**History:** Sprint 5 proved `cursor-sdk` requires Python 3.10+ while the
app targeted 3.9.6. Sprint 6 worked around that with an out-of-process
subprocess bridge (`sdk_bridge.py`, a separate `.venv-sdk` interpreter,
stdin/stdout JSON). Sprint 7 migrated the whole project to Python 3.12 and
removed that bridge entirely in favor of the direct call shown above — see
the Sprint 7 row in §4 for the full list of what was removed.

---

## 3. Folder structure (current, actual)

```
shipready-ai/
├── README.md                  # stale in places — see staleness note
├── PROJECT_CHARTER.md         # source of truth for V1 scope
├── PRODUCT_VISION.md          # stale roadmap — see staleness note
├── ARCHITECTURE.md            # design rationale, mostly still accurate
├── DEVELOPMENT_CONTEXT.md     # this file
├── .python-version             # "3.12" — Sprint 7; pyenv/uv-style pin
├── requirements.txt           # streamlit, cursor-sdk, pydantic, python-dotenv, PyYAML — all one Python 3.12+ venv as of Sprint 7
├── requirements-dev.txt       # + pytest, pytest-asyncio, ruff
├── verify_cursor_sdk.py       # standalone Cursor SDK connectivity check (Sprint 5) — runs in the same venv as everything else as of Sprint 7
├── .env.example                # CURSOR_API_KEY, REVIEWBOARD_MODEL, REVIEW_STEP_DELAY_SECONDS
├── .gitignore
├── config.py                  # centralized settings (env-var driven, has defaults; + CURSOR_API_KEY / CURSOR_SDK_MODEL as of Sprint 6/7)
├── app.py                     # Streamlit entrypoint — set_page_config + render_dashboard()
├── .streamlit/
│   └── config.toml
├── reviewers/                 # one file per persona, flat (no package __init__.py)
│   ├── architecture.py        # review(submission) -> ReviewResult   [REAL Cursor SDK call, in-process as of Sprint 7]
│   ├── security.py            # review(submission) -> ReviewResult   [placeholder logic]
│   ├── qa.py                  # review(submission) -> ReviewResult   [placeholder logic]
│   ├── operations.py          # review(submission) -> ReviewResult   [placeholder logic]
│   └── cab.py                 # review(review_results) -> ReleaseDecision [REAL Cursor SDK call, in-process, isolated cwd, as of Sprint 9]
├── models/
│   └── review_models.py       # SubmissionInput, Finding, ReviewResult, ReleaseDecision (Pydantic, real)
├── orchestrator/
│   └── pipeline.py            # run_review_pipeline() — real sequencing logic, placeholder reviewer bodies
├── prompts/                   # persona prompt templates
│   ├── architecture.md        # REAL content as of Sprint 6 — loaded by reviewers/architecture.py
│   ├── security.md            # still an empty placeholder
│   ├── qa.md                  # still an empty placeholder
│   ├── operations.md          # still an empty placeholder
│   └── cab.md                 # REAL content as of Sprint 9 — loaded by reviewers/cab.py
├── ui/
│   ├── dashboard.py           # render_dashboard() — assembles components, drives the pipeline generator
│   └── components.py          # reusable, presentation-only building blocks + STATUS_CARDS data; reviewer sections are st.expanders as of Sprint 11
├── sample_data/
│   └── README.md              # placeholder — no actual sample diffs/PRs added yet
├── generated/
│   └── .gitkeep                # gitignored output dir for future pipeline artifacts
└── tests/
    ├── __init__.py
    ├── test_pipeline.py        # placeholder only — no real tests written yet
    └── fixtures/
        ├── sample.diff
        ├── sample_pr_description.md
        └── sample_api_spec.yaml
```

**Note:** there are no `__init__.py` files in `reviewers/`, `models/`,
`orchestrator/`, or `ui/`. They work as Python 3 implicit namespace
packages because `streamlit run app.py` puts the repo root on `sys.path`.
This was a deliberate choice to match an exact folder spec given early in
the project — don't "fix" it by adding `__init__.py` files without reason.

---

## 4. Completed sprints

| Sprint | Goal | Key outcome |
|---|---|---|
| **Sprint 0** | Initial scaffold | Nested `shipready_ai/` package with placeholder-only modules (docstrings + TODOs, no logic). |
| **Sprint 1** | Re-scaffold to an exact flat structure | Replaced the nested package with the current flat layout (`reviewers/`, `models/`, `orchestrator/`, `prompts/`, `ui/`, `sample_data/`, `generated/`). Renamed "Release Manager" → "CAB" throughout. Still placeholder-only. |
| **Sprint 2** | Build the initial Streamlit dashboard (UI only) | `ui/components.py` (reusable widgets) + `ui/dashboard.py` assembled: header, two file uploaders, "Run Review" button, 5 status cards in a responsive grid (2+2+1 layout), all hardcoded to "Pending". No business logic. Later polished for compactness (smaller header, shorter cards, tightened CSS spacing) and fixed for Python 3.9 compatibility (`typing.Optional`/`Tuple` instead of `X \| Y` / lowercase generics where relevant). |
| **Sprint 3** | Build the orchestration workflow (still no AI) | Implemented real Pydantic models in `models/review_models.py`. Each reviewer got a real `review()` function returning a **hardcoded placeholder** `ReviewResult`/`ReleaseDecision`. `orchestrator/pipeline.py` now really runs Architecture → Security → QA → Operations → CAB in order via a generator that `yield`s after each step; the dashboard consumes this generator to flip each status card from "Pending" to "Complete" live, with a short delay between steps. That delay was then extracted into `config.py` as `REVIEW_STEP_DELAY_SECONDS` (env-var overridable, defaults to 0.8s) instead of being hardcoded in the orchestrator. |
| **Sprint 4** | Wire real input end-to-end (still no AI) | `ui/dashboard.py` now builds a real `SubmissionInput` from the uploaded diff/PR files — new private helpers `_read_uploaded_text()` (decodes an `UploadedFile`'s bytes as UTF-8, `errors="replace"`, returns `""` for no file) and `_build_submission()` — and passes it into `run_review_pipeline(submission)` instead of relying on the empty default. `ui/components.py::render_input_section()` is unchanged (still returns raw `UploadedFile`/`None` objects; presentation-only boundary preserved). Reviewer `review()` bodies are still hardcoded placeholders — they now just receive real `diff_text`/`pr_description` instead of `""`/`""`. No `api_spec` uploader exists yet, so `SubmissionInput.api_spec` stays `None`. |
| **Sprint 5** | Stand up the Cursor SDK, prove basic connectivity (no reviewer integration) | Added a standalone `verify_cursor_sdk.py` at repo root that calls `Agent.prompt("Say hello in exactly one short sentence.", ...)` (local runtime) via the official `cursor-sdk` PyPI package, printing the result and exiting 0/1/2 per the SDK's startup-failure vs. run-failure vs. success distinction. **Key finding:** `cursor-sdk` requires Python 3.10+; this project targets 3.9.6, so this script must run under a *separate* 3.10+ virtualenv (`.venv-sdk/`, gitignored) — it is not installed into `requirements.txt` and cannot run under the app's normal interpreter. See §9 below for full setup steps. Nothing in `reviewers/`, `orchestrator/`, `ui/`, `models/`, or `config.py` was touched. |
| **Sprint 6** | Bridge the 3.9 app to a real Cursor SDK-backed Architecture reviewer | Added `sdk_bridge.py` (repo root) — the only file in the repo that imports `cursor_sdk` — a tiny stdin/stdout JSON process run under the Python 3.10+ `.venv-sdk` from Sprint 5: reads `{"prompt", "model"}`, calls `Agent.prompt(...)`, writes `{"status", "text", "error"}`, exits 0/1/2. Rewrote `reviewers/architecture.py::review()` to build a real prompt from `prompts/architecture.md` (authored for real this sprint) + the submission's `diff_text`/`pr_description`, invoke `sdk_bridge.py` via `subprocess.run([config.CURSOR_SDK_PYTHON, ...])`, and parse the bridge's JSON response into a real `ReviewResult`/`Finding`. Added 3 small settings to `config.py` (`CURSOR_SDK_PYTHON`, `CURSOR_SDK_MODEL`, `CURSOR_SDK_BRIDGE_TIMEOUT_SECONDS`). Every failure mode (missing interpreter, timeout, bridge startup/run error, malformed model JSON) is caught inside `review()` and converted to a safe `ReviewResult(verdict="block", ...)` — it never raises, since `orchestrator/pipeline.py` was left untouched and has no try/except around reviewer calls. `security.py`, `qa.py`, `operations.py`, `cab.py`, the orchestrator, and the dashboard are all byte-for-byte unchanged. **Superseded by Sprint 7 — the bridge described here no longer exists.** |
| **Sprint 7** | Migrate the whole project to Python 3.12; remove the subprocess bridge | Per explicit user decision, stopped maintaining a Python 3.9 compatibility layer. **Removed:** `sdk_bridge.py`, `requirements-sdk.txt`, `config.CURSOR_SDK_PYTHON`, `config.CURSOR_SDK_BRIDGE_TIMEOUT_SECONDS`, the `.venv-sdk` convention. **Added:** `.python-version` (`3.12`), `config.CURSOR_API_KEY`. **Changed:** `reviewers/architecture.py::review()` now imports `cursor_sdk` directly and calls `Agent.prompt(...)` in-process (see §2's call-flow diagram) — the prompt-building and JSON-response-parsing logic is unchanged from Sprint 6, only the transport changed. `cursor-sdk>=1.0.24` merged directly into `requirements.txt` (single venv now, no more split). `verify_cursor_sdk.py` simplified (no longer documents a separate-interpreter requirement) but otherwise unchanged. `README.md`'s "Getting started" venv instructions updated to require Python 3.12+. `security.py`, `qa.py`, `operations.py`, `cab.py`, the orchestrator, `models/`, and the dashboard are all byte-for-byte unchanged — same reviewer interfaces, same `ReviewResult` model, same fixed order. |
| **Sprint 8** | Polish the Architecture review's presentation into an enterprise-code-review-style report | Expanded `prompts/architecture.md`'s requested JSON shape to `{decision, confidence, summary, findings, recommendations, overall_assessment}` (was just `{verdict, summary, findings}`). Added matching optional fields to `models/review_models.py::ReviewResult` (`decision: Literal["PASS","NEEDS_CHANGES","BLOCK"]`, `confidence: int 0-100`, `recommendations: list[str]`, `overall_assessment`) — all default `None`/`[]` so `security.py`/`qa.py`/`operations.py`/`cab.py` are unaffected. `reviewers/architecture.py::_parse_agent_response()` parses the new fields and derives the legacy `verdict` from `decision` for backward compatibility; added `_render_report_markdown()`, which groups findings by severity (critical→info) and renders the whole report — decision/confidence line, then `### Summary` / `### Findings` / `### Recommendations` / `### Overall Assessment` headed sections with bullets — as ONE markdown string, since `orchestrator/pipeline.py` (explicitly out of scope this sprint) only forwards `ReviewResult.summary` to the dashboard; `_blocked_result()` renders through the same helper so failure output looks consistent. `ui/components.py::render_status_card()` now renders a "Complete" card's description with `st.markdown()` instead of `st.caption()` so those headings/bullets actually display (harmless for the other reviewers' one-line placeholder text). Verified with a real, live `Agent.prompt` call against `demo/auth-service.diff` (see the user's own demo fixture) — produced a genuine 5-finding, 4-recommendation report — plus mocked tests for the success path, malformed-JSON fallback, and an invalid `decision` literal (pydantic `ValidationError` → safe `block`, same as any other malformed-output case). `orchestrator/pipeline.py`, `security.py`, `qa.py`, `operations.py`, and `cab.py` are byte-for-byte unchanged. |
| **Sprint 9** | Replace the placeholder CAB reviewer with a real Cursor SDK reviewer | Authored `prompts/cab.md` for real (was an empty placeholder). Added matching optional fields to `models/review_models.py::ReleaseDecision` (`cab_decision: Literal["APPROVE","NEEDS_CHANGES","BLOCK"]`, `overall_risk: Literal["LOW","MEDIUM","HIGH","CRITICAL"]`, `executive_summary`, `reviewer_summary: list[str]`, `business_impact`, `final_recommendation`) — legacy `decision`/`rationale`/`conditions`/`contributing_reviews` untouched, `cab_decision` maps onto legacy `decision` for backward compatibility, same pattern as Sprint 8. Rewrote `reviewers/cab.py::review()` to call `cursor_sdk.Agent.prompt(...)` directly, in-process — same shape as `architecture.py` — but with **isolation enforced at two levels**, not one: (1) the function signature still only accepts `list[ReviewResult]`, no diff parameter, same as always; (2) the SDK call's `LocalAgentOptions(cwd=...)` points at a fresh `tempfile.TemporaryDirectory()`, **never this repo** — `LocalAgentOptions` grants the underlying agent real file/shell tool access to whatever `cwd` it's given (confirmed via the `sdk` skill), so pointing it at the real repo would let the model just run `git diff` itself regardless of prompt wording; an empty temp dir makes that structurally impossible. The prompt (`_build_prompt()`) is built only from the four `ReviewResult` objects' `reviewer_name`/decision/`overall_assessment`/`recommendations` — verified by a mocked test asserting `"shipready-ai"` never appears in the `cwd` passed to `Agent.prompt`. The "Reviewer Summary" section is **not** requested from the model — `_build_reviewer_summary_lines()` builds it deterministically from the same four `ReviewResult` objects, since that data is already typed and there's no reason to risk the model paraphrasing it. `_render_report_markdown()` mirrors Sprint 8's style exactly (colored decision/risk badges, `###` headed sections, bullets) and is what `rationale` now holds — so no changes were needed to `orchestrator/pipeline.py` (still just yields `decision.rationale`) or `ui/components.py` (already renders any "Complete" card as markdown since Sprint 8). Verified with a real, live full-pipeline run against `demo/auth-service.diff`: CAB correctly weighed one real `NEEDS_CHANGES` (Architecture) against three placeholder `PASS`es into an overall `NEEDS_CHANGES`/`MEDIUM`-risk decision with a coherent executive summary and hold recommendation — plus mocked tests for the success path and all four failure modes (no credentials, malformed JSON, run error, startup error). `orchestrator/pipeline.py`, `ui/`, `security.py`, `qa.py`, `operations.py`, and `reviewers/architecture.py` are byte-for-byte unchanged. |
| **Sprint 10** | Polish the CAB report's presentation (readability only, no logic change) | Touched only `prompts/cab.md` (wording) and `reviewers/cab.py`'s rendering helpers — the JSON contract, the SDK call, and the diff-isolation rules from Sprint 9 are all untouched. `_render_report_markdown()`: decision is now a `##` emoji heading (🟢/🟠/🔴 for APPROVE/NEEDS_CHANGES/BLOCK) — the primary visual element — with Overall Risk directly below it, instead of a small inline badge line. Added `_truncate_words()`, applied at render time to cap the *displayed* Executive Summary at 50 words and Business Impact at 40 — the prompt now also asks the model for these limits directly, but the cap is enforced in code regardless, so a verbose response still renders tight; the full untruncated text stays on `ReleaseDecision.executive_summary`/`.business_impact` as the structured source of truth. Added `_split_recommendation_bullets()`, which renders `final_recommendation` (still a single string field/JSON value — type unchanged) as at most 3 bullets, preferring newline-separated points (what the updated prompt asks for) and falling back to a sentence split of a plain paragraph for backward compatibility with older/plain responses. `_build_reviewer_summary_lines()` replaced each reviewer's full assessment paragraph with one compact line (icon + name + colored decision, `_(Placeholder)_` tag for the three reviewers with no `decision` field populated yet — detected via `result.decision is None`, an existing signal, no new field added). Verified with mocked tests (a deliberately verbose/non-newline response correctly truncated to 50/40 words and 3 bullets while the raw fields stayed untruncated; a newline-separated response; the blocked/failure path) and a real, live full-pipeline run against `demo/auth-service.diff`. `models/review_models.py`, `orchestrator/pipeline.py`, `ui/`, and `reviewers/architecture.py` are byte-for-byte unchanged. |
| **Sprint 11** | Final UI polish for the interview demo (presentation only) | User explicitly confirmed one small, mechanical, non-logic change to `orchestrator/pipeline.py` was in scope (asked first, since prior sprints had treated it as fully off-limits): `run_review_pipeline()` now yields `(step_name, result)` — the real `ReviewResult`/`ReleaseDecision` object — instead of `(step_name, result.summary)`/`(step_name, decision.rationale)`. Same sequencing, order, delay, reviewer calls, and CAB isolation; purely a data-plumbing change so `ui/` can read `.decision`/`.verdict`/`.cab_decision` for a status badge instead of just a pre-rendered string. `ui/components.py`: new `render_header()` (🚢 title, subtitle, tagline, one-line explanation, divider); `render_input_section()` now wraps the two uploaders in a bordered container with a lead-in caption; `render_status_card`/`render_status_board` (bordered-card 2-per-row grid) replaced with `render_reviewer_section`/`render_review_board` (`st.expander` per reviewer, stacked vertically) — default-expanded state per reviewer via `_DEFAULT_EXPANDED` (Architecture/CAB open, Security/QA/Operations collapsed); new `decision_badge()` reads a completed step's real object via `getattr()` duck-typing (`cab_decision` → `decision` → `verdict`, in that order) to build an "✅/🟠/🔴 LABEL" badge shown directly in the expander title, so even the three still-hardcoded placeholder reviewers get a real `✅ PASS` badge (derived from their existing `verdict` field, no reviewer change needed). `ui/dashboard.py`: session state now keys reviewer name → the real result object (was → a `"Pending"/"Complete"` string); the final `st.success(...)` banner now shows the CAB's decision badge instead of dumping its entire multi-section rationale into one line. `inject_compact_styles()` trimmed to the one CSS rule Streamlit has no native equivalent for (expander-to-expander spacing) — everything else (headers, dividers, bordered containers) is native. Verified with a headless `AppTest` run of `app.py` (no exceptions, 5 expanders present) plus a session-state-injected "Complete" render matching the sprint's exact expected titles (`🏗️ Architecture — 🟠 NEEDS CHANGES`, `🔒 Security — ✅ PASS`, etc.) against a real, live full-pipeline run on `demo/auth-service.diff`. One deliberate, disclosed deviation from the literal spec: kept each reviewer's already-established icon (🏗️ Architecture, 🏛️ CAB — same as `STATUS_CARDS` since Sprint 2 and the icons `reviewers/cab.py`'s own Sprint-10 reviewer-summary lines use) rather than reusing 🏛 for both Architecture and CAB as literally written in the request, since two identical icons stacked on the same screen seemed like an actual readability regression rather than the intended effect. `models/review_models.py`, `reviewers/architecture.py`, `reviewers/cab.py`, and `prompts/` are byte-for-byte unchanged. |

Git history (as of Sprint 3): `Initial project scaffold` → `Build initial
Streamlit dashboard` → `Implement review orchestration pipeline` → (Sprint
4-8, committed together as) `Enhance architecture reviewer with structured
AI output`. Sprint 9's changes are not yet committed — see the user before
committing.

---

## 5. Key design decisions

1. **Flat structure over a nested package.** The project deliberately uses
   top-level `reviewers/`, `models/`, `orchestrator/`, `ui/` directories
   rather than a single importable `shipready_ai` package. This was an
   explicit user decision (Sprint 1) — don't re-nest without being asked.
2. **CAB never receives the raw diff — enforced by type signature.**
   `cab.review(review_results: List[ReviewResult])` has no parameter
   through which a diff could be passed. This is the project's central
   architectural point and must be preserved through every future change
   (including real Cursor SDK integration).
3. **Pydantic models, not dicts, for every hand-off.** `SubmissionInput`,
   `Finding`, `ReviewResult`, `ReleaseDecision` in `models/review_models.py`
   are the only data shapes reviewers/orchestrator/UI pass around.
4. **Reviewers are plain functions, not classes.** `review(submission) ->
   ReviewResult` (or `review(review_results) -> ReleaseDecision` for CAB).
   No `BaseReviewer` abstract class — kept intentionally simple.
5. **Orchestrator is a generator, not a batch function.** `run_review_pipeline()`
   `yield`s `(step_name, summary)` after each step so the UI can animate
   progress incrementally within a single Streamlit script run (using
   `st.empty()` placeholders redrawn in place) rather than blocking until
   everything finishes.
6. **Pacing delay lives in config, not hardcoded.** `REVIEW_STEP_DELAY_SECONDS`
   in `config.py` (env-var overridable via `.env` / `REVIEW_STEP_DELAY_SECONDS`,
   default `0.8`). It exists purely so the sequential workflow is visibly
   watchable — it is explicitly a stand-in for future real agent latency,
   not a permanent feature.
7. **Status persisted in `st.session_state`,** not just local variables, so
   completed card state survives unrelated Streamlit reruns.
8. **Python 3.12 is the target (as of Sprint 7).** The project ran on
   Python 3.9.6 through Sprint 6 (hence `typing.Optional[X]`/`Tuple[...]`
   instead of `X | Y` in `ui/components.py` and elsewhere) — that
   constraint was dropped when the whole project migrated to 3.12 so it
   could import `cursor-sdk` directly without a subprocess bridge (see
   Sprint 7, §2). The existing `typing.Optional`/`Tuple` style was left
   as-is rather than modernized to `X | None`/lowercase generics — that
   would be a cosmetic, unrelated refactor; do it only if asked.
9. **Minimal, safe custom CSS only.** `ui/components.py::inject_compact_styles()`
   targets only the stable `.block-container` class and plain `h3` tags —
   deliberately avoids Streamlit's internal `data-testid` attributes, which
   can change between versions.
10. **Docstring convention:** every module has a docstring stating its
    responsibility, what's explicitly out of scope, and a note on what's
    still a placeholder vs. real. Preserve this pattern in new files.

---

## 6. Current implementation status

**Real / functional:**
- Full Streamlit dashboard UI — polished header, bordered upload section, primary run button, and a vertically-stacked `st.expander` per reviewer (Sprint 11; was a bordered-card grid through Sprint 10).
- `models/review_models.py` — real Pydantic models.
- `orchestrator/pipeline.py` — real sequencing, generator, delay-from-config logic; yields the real `ReviewResult`/`ReleaseDecision` object per step as of Sprint 11 (was just its `.summary`/`.rationale` string).
- `config.py` — real, env-var driven settings loader.
- `ui/dashboard.py::_build_submission()` / `_read_uploaded_text()` — real: uploaded diff/PR files are read and turned into a real `SubmissionInput` before the pipeline runs.
- `ui/components.py::decision_badge()` — real (Sprint 11): reads a completed step's actual `.cab_decision`/`.decision`/`.verdict` and renders an "✅/🟠/🔴 LABEL" badge in its expander title — works for all five reviewers, including the three still-hardcoded placeholders (via their always-populated `.verdict`).
- End-to-end click flow: **Run Review → uploaded files parsed into a real SubmissionInput → pipeline executes in order → each reviewer's expander flips to Complete with a real decision badge live → success message shows CAB's decision badge.**
- `verify_cursor_sdk.py` — real, standalone: proves the project can complete a one-shot `Agent.prompt(...)` round trip. Runs in the same venv as the rest of the app as of Sprint 7. Not wired into the app in any way.
- `reviewers/architecture.py` — **real as of Sprint 6, in-process as of Sprint 7, richer structured output as of Sprint 8.** Builds a real prompt, calls `cursor_sdk.Agent.prompt(...)` directly, and parses a real structured response (`decision`/`confidence`/`summary`/`findings`/`recommendations`/`overall_assessment`) into `ReviewResult`. Verified with a real, live round trip against `demo/auth-service.diff` (5 findings, 4 recommendations, all sections populated) plus mocked `Agent.prompt` responses covering the success path, run-error path, malformed-JSON fallback, and an invalid `decision` literal.
- `ReviewResult.findings` **is** populated for real now — for the Architecture reviewer only (see §7's old TODO about this, now done for one of four reviewers).
- `reviewers/cab.py` — **real as of Sprint 9.** Calls `cursor_sdk.Agent.prompt(...)` directly, in-process, same as `architecture.py`, but with `LocalAgentOptions(cwd=...)` pointed at a fresh `tempfile.TemporaryDirectory()` rather than the real repo — so the underlying agent has no file/shell-accessible diff to find even if it tried (see §11's isolation note). Parses a real structured response (`decision`/`overall_risk`/`executive_summary`/`business_impact`/`final_recommendation`) into `ReleaseDecision`; the "Reviewer Summary" section is built deterministically in Python from the four incoming `ReviewResult`s, not requested from the model. Verified with a real, live full-pipeline round trip against `demo/auth-service.diff` plus mocked tests for the success path and all four failure modes.

**Explicitly placeholder / not real yet:**
- `security.py`, `qa.py`, `operations.py` — `review()` bodies still return **hardcoded** results; untouched by Sprints 6–9.
- No Cursor SDK import anywhere in `orchestrator/`, `ui/`, `models/`, `config.py`'s logic, or `reviewers/security.py` / `qa.py` / `operations.py` — `reviewers/architecture.py` and `reviewers/cab.py` are the only two that import `cursor_sdk`.
- `prompts/security.md`, `qa.md`, `operations.md` are still empty template placeholders (`architecture.md` real as of Sprint 6/expanded Sprint 8; `cab.md` real as of Sprint 9).
- ~~`orchestrator/pipeline.py` still only forwards `ReviewResult.summary`/`ReleaseDecision.rationale`~~ — **changed in Sprint 11**: it now yields the full object (`.summary`/`.rationale` still holds the same pre-rendered report markdown from Sprint 8/9/10; `ui/` just also reads `.decision`/`.verdict`/`.cab_decision` off the same object now for the expander title badge, instead of receiving only the rendered string).
- No `api_spec` uploader exists in the UI yet — `SubmissionInput.api_spec` stays `None` from every real run (there's a `sample_api_spec.yaml` fixture for future use).
- The four diff-reviewers run **sequentially**, not concurrently (`ARCHITECTURE.md` describes a planned concurrent fan-out via the SDK's async client — not implemented).
- No *pipeline-level* partial-failure policy yet: `reviewers/architecture.py` and `reviewers/cab.py` now handle their own failures internally (collapsing to `verdict="block"`/`decision="BLOCK"`/`cab_decision="BLOCK"`), but there's no orchestrator-level policy for e.g. "should CAB be told a reviewer's result came from a real failure vs. a real 'block' verdict vs. a placeholder?" (CAB does still receive whatever `ReviewResult` it's given either way — it just weighs it — but there's no explicit policy document for this distinction). See the §7 TODO.
- `Finding` objects are populated for the Architecture reviewer as of Sprint 8; still always `[]` for `security.py`/`qa.py`/`operations.py`. CAB has no `Finding`-shaped output of its own (out of scope for its schema).
- `tests/test_pipeline.py` has no real test cases.
- `sample_data/` has no actual sample diffs/PRs, just a README.

---

## 7. Outstanding TODOs (grep-able as `# TODO:` in the repo)

- `reviewers/security.py`, `qa.py`, `operations.py` — same treatment as `architecture.py`/`cab.py`: load the matching `prompts/*.md` template, call `cursor_sdk.Agent.prompt(...)` directly (no bridge needed anymore), parse structured response into `ReviewResult`.
- Author real prompt content in `prompts/security.md`, `qa.md`, `operations.md` (currently empty HTML-comment placeholders; `architecture.md` and `cab.md` are done).
- Convert the diff-reviewer fan-out from sequential to concurrent (Cursor SDK async client — `AsyncAgent`/`AsyncClient`), per `ARCHITECTURE.md` §2 and §5. This is simpler post-Sprint-7 than it would have been with the old subprocess bridge — it's now "four concurrent in-process `Agent.prompt` calls" rather than "four concurrent subprocesses."
- Define and implement partial-failure policy (can CAB proceed with 3/4 reviews being real vs. hardcoded, or one being a `block`-on-error placeholder like Architecture can now produce? how are `CursorAgentError` vs. `result.status == "error"` vs. parse failures surfaced beyond each reviewer's current "collapse to `block`" approach?).
- ~~Run `verify_cursor_sdk.py` and the Architecture reviewer once with a real `CURSOR_API_KEY`~~ — **done in Sprint 8**, against `demo/auth-service.diff` (the user's own fixture, not `tests/fixtures/`) — see the Sprint 8 row in §4.
- ~~Replace the placeholder CAB reviewer with a real Cursor SDK reviewer~~ — **done in Sprint 9**, verified live against the same fixture — see the Sprint 9 row in §4.
- Write real tests in `tests/test_pipeline.py` (there's a `streamlit.testing.v1.AppTest`-based pattern already proven ad hoc in-conversation for click-simulation — see §10 below — worth formalizing into `pytest` tests).
- Give `security.py`/`qa.py`/`operations.py` the same `decision`/`confidence`/`recommendations`/`overall_assessment` treatment once they get real SDK calls, so all four diff-reviewer cards render consistently (and so CAB's per-reviewer summary line for them reads as more than a one-line placeholder).
- Refresh `README.md` and `PRODUCT_VISION.md` — see staleness note below.
- `ruff check .` now reports pre-existing `UP006`/`UP035`/`UP045` findings (`typing.Optional`/`List`/`Dict`/`Tuple` → `X | None`/`list`/`dict`) across most files, including some Sprint 8/9 touched — ruff started flagging these once `.python-version` (Sprint 7) gave it a Python 3.12 target to infer. This is pre-existing style debt, not a Sprint 8/9 regression (see §5 item 8) — a future sprint could modernize it repo-wide in one pass if asked, rather than doing it piecemeal per-file.

---

## 8. Planned next sprint (proposed, not yet started)

Sprint 4 wired real input end-to-end. Sprint 5 proved basic Cursor SDK
connectivity standalone. Sprint 6 wired exactly one real reviewer
(Architecture) through a subprocess bridge. Sprint 7 migrated the whole
project to Python 3.12 and removed that bridge in favor of a direct,
in-process SDK call. Sprint 8 polished that one reviewer's presentation
into a structured, enterprise-report-style output. Sprint 9 wired up the
second real reviewer (CAB), synthesizing the other four's `ReviewResult`s
in the same report style. Sprint 10 polished CAB's presentation into a
tighter, decision-first executive report. Remaining candidates:

1. ~~Wire real input end-to-end (no AI yet)~~ — **done in Sprint 4.**
2. ~~Prove Cursor SDK connectivity, standalone~~ — **done in Sprint 5.**
3. ~~First real reviewer, end-to-end Cursor SDK integration~~ — **done in Sprint 6** (Architecture only, via a subprocess bridge).
4. ~~Migrate to Python 3.12, remove the subprocess bridge~~ — **done in Sprint 7** (see §2's call-flow diagram).
5. ~~Polish the Architecture reviewer's presentation~~ — **done in Sprint 8** (decision/confidence/findings-by-severity/recommendations/overall assessment; see §4's Sprint 8 row).
6. ~~Replace the placeholder CAB reviewer with a real Cursor SDK reviewer~~ — **done in Sprint 9** (decision/overall_risk/executive_summary/reviewer_summary/business_impact/final_recommendation, isolated `cwd`; see §4's Sprint 9 row).
7. ~~Polish the CAB reviewer's presentation~~ — **done in Sprint 10** (decision-first emoji heading, word-capped summaries, compact reviewer list, bulleted recommendation; see §4's Sprint 10 row).
8. **Repeat the pattern for Security, QA, Operations** (each is now a near-copy of `reviewers/architecture.py`'s direct-call shape *and* its Sprint 8 structured-output/rendering shape, with its own `prompts/*.md`) — this would also make CAB's per-reviewer "Reviewer Summary" lines richer for those three, since it already reads `overall_assessment`/`decision` when present and only falls back to the one-line placeholder `summary` otherwise.
9. **Consider the Cursor SDK's async client** for the four diff-reviewers once more than one is real, so they can run concurrently instead of sequentially (see the §7 TODO) — this is now a much simpler change than it would have been under the Sprint 6 bridge design, since there's no subprocess-per-call question anymore.
10. ~~Consider enriching `orchestrator/pipeline.py`'s yield~~ — **done in Sprint 11**, after explicitly confirming with the user first (see §4's Sprint 11 row): it now yields the full `ReviewResult`/`ReleaseDecision` object. `ui/` still just displays `.summary`/`.rationale` as one markdown blob rather than building each report's layout itself from the granular fields (`findings`/`recommendations`/etc.) — that finer-grained UI layout remains a real, separate future candidate if ever wanted.

**Do not start Cursor SDK / LLM work *inside a reviewer* without explicit user confirmation** — every prior sprint in this project has been explicitly scoped by the user one step at a time. Sprint 6/7 explicitly authorized real SDK logic in the Architecture reviewer, Sprint 9 in the CAB reviewer; `security.py`, `qa.py`, and `operations.py` remain off-limits until a future sprint says otherwise.

---

## 9. Cursor SDK setup (Sprint 5, simplified in Sprint 7)

As of Sprint 7 the whole project — app and SDK alike — runs in **one**
Python 3.12+ venv. There is no separate interpreter or bridge to set up
(that was the Sprint 5/6 story before the Python 3.9→3.12 migration; see
§4's Sprint 7 row for what was removed).

1. **Python version.** `cursor-sdk` (PyPI) requires Python 3.10+; this
   project targets **3.12** (`.python-version`, `requirements.txt`). If
   your system `python3` is older, install 3.12 via
   [pyenv](https://github.com/pyenv/pyenv),
   [uv](https://github.com/astral-sh/uv) (`uv python install 3.12` fetches
   a standalone build with no Homebrew/pyenv needed), or your platform's
   package manager.
2. **One-time setup:**
   ```bash
   python3.12 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```
3. **Configure credentials.** Copy `.env.example` to `.env` and fill in
   `CURSOR_API_KEY` (`python-dotenv` loads it automatically, both via
   `config.py` for the app and directly in `verify_cursor_sdk.py`), or
   export it directly in the shell.
4. **Run the standalone connectivity check:**
   ```bash
   .venv/bin/python verify_cursor_sdk.py
   ```
   Expected on success: prints `Run finished: status=...` and the agent's
   text response, exits 0. See the script's docstring for the exit-code
   meanings (0 success / 1 startup failure / 2 run failure), which mirror
   the SDK's own `CursorAgentError` vs. `result.status == "error"`
   distinction (see the `sdk` skill / `cursor.com/docs/sdk/python`).
5. **What was actually verified in Sprint 7:** built a Python 3.12 venv
   from scratch (via `uv python install 3.12`, kept locally as `.python312/`
   since these standalone builds aren't fully relocatable — `.venv`'s own
   interpreter binary still points back at it, so both must stay on disk
   together; see §11), installed the merged `requirements.txt` into it
   (`cursor-sdk`, `streamlit`, `pydantic`, `python-dotenv`, `PyYAML` all
   import cleanly together in one venv), then re-ran every check from
   Sprint 6 against the new direct in-process call: `reviewers.architecture.review()`
   with no `CURSOR_API_KEY` set still degrades gracefully to
   `ReviewResult(verdict="block", ...)` instead of raising; the full
   `run_review_pipeline()` generator and a headless `AppTest` render of
   `app.py` both complete without exceptions; and `Agent.prompt` was
   mocked to verify the success-path JSON parsing, the run-error path, and
   the malformed/non-JSON-output fallback all still behave identically to
   Sprint 6's bridge-based versions. `verify_cursor_sdk.py` was run
   directly (unmocked) and correctly reports its "CURSOR_API_KEY is not
   set" failure path. The live `Agent.prompt(...)` round trip itself was
   **not** exercised end-to-end with a real `CURSOR_API_KEY` in this
   environment — a future session with real credentials should run
   `verify_cursor_sdk.py` and then the Architecture reviewer once to
   confirm the full live round trip.
6. **`.venv/` and `.python312/` are both gitignored** and both left in
   place on disk (not deleted after verification) — the app now genuinely
   depends on them to run at all, the same reasoning Sprint 6 applied to
   `.venv-sdk` (which no longer exists as of this sprint).

---

## 10. Testing / verification approach used so far

No formal test suite exists yet, but this workflow was used repeatedly and
worked well — worth continuing:

1. `python3 -c "compile(...)"` over every `.py` file for a fast syntax sanity check. Note: the machine's system `python3` is still 3.9.6 as of this writing — fine for a syntax-only check, but running the app or its tests for real requires the project's actual Python 3.12 venv (`.venv/`, §9), since `reviewers/architecture.py` now imports `cursor_sdk` at module load time.
2. Create/use the project's Python 3.12 venv (`.venv/`, `pip install -r requirements.txt`), then actually `streamlit run app.py --server.headless true --server.port <free port>` in the background and curl `/_stcore/health` (expects `ok`) to catch real runtime/import errors that static analysis misses.
3. For behavior (not just "does it boot"), use Streamlit's built-in `streamlit.testing.v1.AppTest`:
   ```python
   from streamlit.testing.v1 import AppTest
   at = AppTest.from_file('app.py')
   at.run(timeout=15)
   at.button[0].click().run(timeout=15)
   # inspect at.session_state, at.success, at.exception, etc.
   ```
   This simulates real button clicks headlessly without a browser and was used to verify the full Run Review → pipeline → status update flow.
4. Any *additional* throwaway venv created for a one-off check (e.g. `.venv_smoketest`, `.venv_uv_bootstrap`) must be `rm -rf`'d afterward — it must never be committed. This does NOT apply to `.venv/` or `.python312/` themselves (§9 item 6): those are load-bearing and gitignored, not throwaway.

---

## 11. Important constraints — what NOT to change without being asked

- **Do not add Cursor SDK, LLM, or other AI logic to `security.py`, `qa.py`, `operations.py`, `orchestrator/`, `ui/`, `models/`, or `config.py`'s existing settings** unless the user explicitly requests it in a given sprint. This has been an explicit, repeated constraint across every sprint so far. (`verify_cursor_sdk.py` (Sprint 5), `reviewers/architecture.py` + the `CURSOR_API_KEY`/`CURSOR_SDK_MODEL` settings in `config.py` (Sprint 6/7), and `reviewers/cab.py` (Sprint 9) are the explicit, scoped exceptions so far — `architecture.py` and `cab.py` are the only two reviewers with real SDK logic.)
- **`reviewers/architecture.py::review()` and `reviewers/cab.py::review()` must never raise.** Every SDK-call/parsing failure mode must be caught and converted to a valid `ReviewResult`/`ReleaseDecision` (currently `verdict="block"`/`decision="BLOCK"` and `cab_decision="BLOCK"` respectively) — `orchestrator/pipeline.py` has no try/except around reviewer calls, so an uncaught exception here would crash the whole dashboard run. Preserve this if you touch either function again — including their `_blocked_result()` helpers, which must keep rendering through `_render_report_markdown()` so failure output stays visually consistent with success output.
- **`orchestrator/pipeline.py` yields the full `ReviewResult`/`ReleaseDecision` object as of Sprint 11** (was just `.summary`/`.rationale`, a plain string) — `ui/` reads `.decision`/`.verdict`/`.cab_decision` off it for the expander badge and `.summary`/`.rationale` for the body markdown. `.summary`/`.rationale` themselves are still the ONE pre-rendered report string Sprint 8/9/10 build (findings/recommendations/etc. aren't separately laid out by `ui/` — it just displays that one string, same as before). If you touch the orchestrator again, preserve this shape (yield the object, not a re-extracted string) rather than reverting to string-only.
- **Do not weaken the CAB reviewer's isolation** from the raw diff/`SubmissionInput` — its function signature must stay `review(review_results: List[ReviewResult])` only, AND (as of Sprint 9) its `Agent.prompt(...)` call's `local=LocalAgentOptions(cwd=...)` must keep pointing at an empty throwaway directory (currently a `tempfile.TemporaryDirectory()`), never this repo. `LocalAgentOptions` grants real file/shell tool access to whatever `cwd` it's given — pointing it at the real repo would let the underlying agent inspect the diff itself regardless of prompt wording, silently defeating the signature-level guarantee. If `cab.py` is touched again, preserve both halves of this, not just the function signature.
- **Do not re-nest the flat folder structure** back into a `shipready_ai`-style package, and don't add `__init__.py` files to `reviewers/`, `models/`, `orchestrator/`, `ui/` without a reason — the flat, no-`__init__.py` layout was a deliberate, explicit choice.
- **Preserve the fixed reviewer order**: Architecture → Security → QA → Operations → CAB. This is specified in `PROJECT_CHARTER.md` and hardcoded in `orchestrator/pipeline.py`'s `_DIFF_REVIEWERS` tuple and `ui/components.py`'s `STATUS_CARDS` list — both must stay in sync if this ever changes.
- **Don't hardcode tunable values inline** — follow the `config.py` pattern established for `REVIEW_STEP_DELAY_SECONDS` (env var with a sensible default) for any new configurable behavior.
- **Keep reviewer/orchestrator/model modules Streamlit-free**, and keep `ui/` free of reviewer/orchestration/SDK logic — the layering boundaries in `ARCHITECTURE.md` §4/§7 are intentional and were enforced sprint-over-sprint.
- **Don't commit a smoke-test virtualenv** or other throwaway artifacts. `.venv/` and `.python312/` are the exception to "delete it when done": both are gitignored (never committed either way), but as of Sprint 7 they're load-bearing — the whole app requires Python 3.12 to run at all, and `.venv`'s interpreter binary itself depends on `.python312/` still existing on disk (these `uv`-fetched standalone builds aren't fully relocatable) — so leave both in place rather than deleting them after verification.
- **This project is built sprint-by-sprint on explicit user instruction** — avoid scope creep (e.g. don't jump ahead to real SDK calls, extra reviewers, or unrequested refactors) even if it seems like a logical next step. Confirm with the user first, as reflected in §8.

**Retired as of Sprint 7 (kept here so a future session doesn't reintroduce them by habit):**
- ~~Never import `cursor_sdk` from anywhere except `sdk_bridge.py`~~ — `sdk_bridge.py` no longer exists; `reviewers/architecture.py` now imports `cursor_sdk` directly, in-process, and that's correct.
- ~~Do not reintroduce Python 3.10+ syntax (`X | Y` unions); target is 3.9.6~~ — the target is now **Python 3.12**; `X | Y` unions (PEP 604) are fine to use in new code, though existing `typing.Optional`/`Tuple` usage was left as-is (see §5 item 8).
- ~~Don't add `cursor-sdk` to `requirements.txt`~~ — it's in `requirements.txt` now; there is no separate `requirements-sdk.txt` anymore.

---

## Documentation staleness (known issue)

`README.md` still says "Status: scaffold only" / "not yet functional", and
`PRODUCT_VISION.md`'s roadmap checklist doesn't reflect the sprints
actually completed (it predates the current flat folder structure and CAB
naming, and still says "Release Manager" / `ReleaseRecommendation` in a few
places rather than "CAB" / `ReleaseDecision`). `ARCHITECTURE.md` is closer
to accurate but still describes some implemented pieces (e.g. the data
models) as "once implemented" future work.

These were **not** updated during Sprints 2–3 because each sprint's scope
was narrowly defined by the user and didn't include a docs pass. A
reasonable, low-risk task for a future sprint (if the user asks for it) is
a documentation refresh pass to reconcile `README.md` / `PRODUCT_VISION.md`
with actual current status — but don't do this unprompted, since it's
outside any sprint scoped so far.
