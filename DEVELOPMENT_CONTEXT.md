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
- `prompts/` — persona prompt templates as markdown data (not yet loaded by any code — see TODOs).

**The single most important invariant:** the CAB reviewer's function
signature (`review(review_results: List[ReviewResult])`) makes it
*impossible* to pass it the raw diff — this is a type-level guarantee, not
just a convention. Do not weaken this when adding real SDK calls.

---

## 3. Folder structure (current, actual)

```
shipready-ai/
├── README.md                  # stale in places — see staleness note
├── PROJECT_CHARTER.md         # source of truth for V1 scope
├── PRODUCT_VISION.md          # stale roadmap — see staleness note
├── ARCHITECTURE.md            # design rationale, mostly still accurate
├── DEVELOPMENT_CONTEXT.md     # this file
├── requirements.txt           # streamlit, pydantic, python-dotenv, PyYAML
├── requirements-dev.txt       # + pytest, pytest-asyncio, ruff
├── .env.example                # CURSOR_API_KEY, REVIEWBOARD_MODEL, REVIEW_STEP_DELAY_SECONDS
├── .gitignore
├── config.py                  # centralized settings (env-var driven, has defaults)
├── app.py                     # Streamlit entrypoint — set_page_config + render_dashboard()
├── .streamlit/
│   └── config.toml
├── reviewers/                 # one file per persona, flat (no package __init__.py)
│   ├── architecture.py        # review(submission) -> ReviewResult   [placeholder logic]
│   ├── security.py            # review(submission) -> ReviewResult   [placeholder logic]
│   ├── qa.py                  # review(submission) -> ReviewResult   [placeholder logic]
│   ├── operations.py          # review(submission) -> ReviewResult   [placeholder logic]
│   └── cab.py                 # review(review_results) -> ReleaseDecision [placeholder logic]
├── models/
│   └── review_models.py       # SubmissionInput, Finding, ReviewResult, ReleaseDecision (Pydantic, real)
├── orchestrator/
│   └── pipeline.py            # run_review_pipeline() — real sequencing logic, placeholder reviewer bodies
├── prompts/                   # persona prompt templates — currently EMPTY placeholders, not loaded by code yet
│   ├── architecture.md
│   ├── security.md
│   ├── qa.md
│   ├── operations.md
│   └── cab.md
├── ui/
│   ├── dashboard.py           # render_dashboard() — assembles components, drives the pipeline generator
│   └── components.py          # reusable, presentation-only building blocks + STATUS_CARDS data
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

Git history: `Initial project scaffold` → `Build initial Streamlit
dashboard` → `Implement review orchestration pipeline`.

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
8. **Python 3.9.6 compatibility is a hard constraint.** No `X | Y` union
   syntax — use `typing.Optional[X]` / `typing.Union[X, Y]`. Built-in
   generics like `list[str]`/`tuple[...]` ARE fine on 3.9 (PEP 585) and
   don't need to be changed.
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
- Full Streamlit dashboard UI (header, uploaders, run button, animated status grid).
- `models/review_models.py` — real Pydantic models.
- `orchestrator/pipeline.py` — real sequencing, generator, delay-from-config logic.
- `config.py` — real, env-var driven settings loader.
- End-to-end click flow: **Run Review → pipeline executes in order → cards flip live → success message shows CAB's (placeholder) decision.**

**Explicitly placeholder / not real yet:**
- All 5 reviewers' `review()` bodies return **hardcoded** results — no analysis of any kind happens.
- No Cursor SDK import or call anywhere in the codebase.
- `prompts/*.md` are empty template placeholders — nothing loads or reads them yet.
- Uploaded files (`ui/components.py::render_input_section()`) are captured but **discarded** — never turned into a real `SubmissionInput`. The pipeline always runs against `SubmissionInput()` (empty defaults).
- The four diff-reviewers run **sequentially**, not concurrently (`ARCHITECTURE.md` describes a planned concurrent fan-out via the SDK's async client — not implemented).
- No partial-failure handling (what happens if a reviewer call fails) — not applicable yet since nothing can fail, but will matter once real SDK calls exist.
- `Finding` objects are never populated (`ReviewResult.findings` is always `[]`).
- `tests/test_pipeline.py` has no real test cases.
- `sample_data/` has no actual sample diffs/PRs, just a README.

---

## 7. Outstanding TODOs (grep-able as `# TODO:` in the repo)

- `reviewers/*.py` — load the matching `prompts/*.md` template, invoke the Cursor SDK, parse structured response into `ReviewResult`/`ReleaseDecision`.
- Wire `ui/components.py::render_input_section()`'s uploaded files into a real `SubmissionInput` (read file contents, pass through to `run_review_pipeline(submission)` instead of the default empty one).
- Author real prompt content in `prompts/*.md` (currently empty HTML-comment placeholders).
- Convert the diff-reviewer fan-out from sequential to concurrent (Cursor SDK async client), per `ARCHITECTURE.md` §2 and §5.
- Define and implement partial-failure policy (can CAB proceed with 3/4 reviews? how are `CursorAgentError` vs. `result.status == "error"` vs. parse failures surfaced?).
- Write real tests in `tests/test_pipeline.py` (there's a `streamlit.testing.v1.AppTest`-based pattern already proven ad hoc in-conversation for click-simulation — see §9 below — worth formalizing into `pytest` tests).
- Populate `ReviewResult.findings` with structured `Finding` objects once reviewers do real analysis.
- Refresh `README.md` and `PRODUCT_VISION.md` — see staleness note below.

---

## 8. Planned next sprint (proposed, not yet started)

Two reasonable candidates, in order of what unblocks the other:

1. **Wire real input end-to-end (no AI yet):** parse the uploaded diff/PR files in `ui/dashboard.py` into a real `SubmissionInput`, pass it into `run_review_pipeline(submission)` instead of the default. Still placeholder reviewer logic, but the pipeline would now be reacting to actual user input shape (e.g. could reflect file names/sizes in the placeholder summaries) — sets up the plumbing for real reviewers to have something to look at.
2. **First real reviewer, end-to-end Cursor SDK integration** (`PRODUCT_VISION.md` Phase 3): pick one reviewer (Architecture is the natural first candidate) and wire it to make a real one-shot `Agent.prompt(...)` call using the prompt template in `prompts/architecture.md`, parsing the structured response into a real `ReviewResult`. This is the highest-value next step for proving the orchestration concept end-to-end, but depends on (1) to have something real to send.

**Do not start Cursor SDK / LLM work without explicit user confirmation** — every prior sprint in this project has been explicitly scoped by the user one step at a time, and "no AI logic yet" has been a repeated, deliberate constraint.

---

## 9. Testing / verification approach used so far

No formal test suite exists yet, but this workflow was used repeatedly and
worked well — worth continuing:

1. `python3 -c "compile(...)"` over every `.py` file for a fast syntax sanity check (the actual system Python here is **3.9.6** — the real compatibility target, not just an assumption).
2. Create a throwaway venv (`python3 -m venv .venv_smoketest`), `pip install -r requirements.txt`, then actually `streamlit run app.py --server.headless true --server.port <free port>` in the background and curl `/_stcore/health` (expects `ok`) to catch real runtime/import errors that static analysis misses.
3. For behavior (not just "does it boot"), use Streamlit's built-in `streamlit.testing.v1.AppTest`:
   ```python
   from streamlit.testing.v1 import AppTest
   at = AppTest.from_file('app.py')
   at.run(timeout=15)
   at.button[0].click().run(timeout=15)
   # inspect at.session_state, at.success, at.exception, etc.
   ```
   This simulates real button clicks headlessly without a browser and was used to verify the full Run Review → pipeline → status update flow.
4. Always `rm -rf .venv_smoketest` afterward — it must never be committed (already covered by `.gitignore`'s `.venv/`-style patterns, but the smoketest venv uses a different name, so double-check it's deleted).

---

## 10. Important constraints — what NOT to change without being asked

- **Do not add any Cursor SDK, LLM, or other AI logic** unless the user explicitly requests it in a given sprint. This has been an explicit, repeated constraint across every sprint so far.
- **Do not weaken the CAB reviewer's isolation** from the raw diff/`SubmissionInput` — its function signature must stay `review(review_results: List[ReviewResult])` only.
- **Do not re-nest the flat folder structure** back into a `shipready_ai`-style package, and don't add `__init__.py` files to `reviewers/`, `models/`, `orchestrator/`, `ui/` without a reason — the flat, no-`__init__.py` layout was a deliberate, explicit choice.
- **Do not reintroduce Python 3.10+ syntax** (`X | Y` unions). The target runtime is Python **3.9.6**. `list[...]`/`tuple[...]`/`dict[...]` generics are fine (PEP 585, valid since 3.9); only the `|` union operator (PEP 604, 3.10+) and any other 3.10+-only syntax must be avoided.
- **Preserve the fixed reviewer order**: Architecture → Security → QA → Operations → CAB. This is specified in `PROJECT_CHARTER.md` and hardcoded in `orchestrator/pipeline.py`'s `_DIFF_REVIEWERS` tuple and `ui/components.py`'s `STATUS_CARDS` list — both must stay in sync if this ever changes.
- **Don't hardcode tunable values inline** — follow the `config.py` pattern established for `REVIEW_STEP_DELAY_SECONDS` (env var with a sensible default) for any new configurable behavior.
- **Keep reviewer/orchestrator/model modules Streamlit-free**, and keep `ui/` free of reviewer/orchestration/SDK logic — the layering boundaries in `ARCHITECTURE.md` §4/§7 are intentional and were enforced sprint-over-sprint.
- **Don't commit a smoke-test virtualenv** or other throwaway artifacts.
- **This project is built sprint-by-sprint on explicit user instruction** — avoid scope creep (e.g. don't jump ahead to real SDK calls, extra reviewers, or unrequested refactors) even if it seems like a logical next step. Confirm with the user first, as reflected in §8.

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
