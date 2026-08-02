# ShipReady AI

AI-powered Engineering Change Advisory Board built with the Cursor SDK.

ShipReady AI helps engineering teams determine whether a software change is ready for production by orchestrating specialized AI reviewers that evaluate architecture, security, testing, operations, and release readiness.

> **Status: scaffold only.** No orchestration or review logic is implemented
> yet. This increment establishes folder structure, module responsibilities,
> and documentation. See [`PRODUCT_VISION.md`](./PRODUCT_VISION.md) for the
> roadmap and [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the technical design.

## What this demonstrates

This project exists to demonstrate **AI orchestration**, not code generation:

- Five single-responsibility reviewer agents, each with its own prompt and
  structured output contract.
- A fan-out / fan-in pipeline: four reviewers run independently against the
  same submission, then a fifth (the CAB reviewer) synthesizes their
  **structured outputs only** — it never sees the raw diff.
- Typed data contracts (Pydantic models, once implemented) between every
  stage, so hand-offs between agents are auditable instead of ad hoc string
  passing.

## Inputs

A user submits:

- **Git diff** (required)
- **Pull Request description** (required)
- **API specification** (optional)

## Reviewers

| # | Reviewer              | File                       | Responsibility                                              |
|---|-----------------------|----------------------------|--------------------------------------------------------------|
| 1 | Architecture Reviewer | `reviewers/architecture.py`| Structural/design soundness, maintainability                 |
| 2 | Security Reviewer     | `reviewers/security.py`    | Vulnerabilities, authN/authZ, secrets, unsafe dependencies    |
| 3 | QA Reviewer           | `reviewers/qa.py`          | Test coverage, testability, edge cases                        |
| 4 | Operations Reviewer   | `reviewers/operations.py`  | Deployability, rollback safety, observability                 |
| 5 | CAB Reviewer          | `reviewers/cab.py`         | Synthesizes the four reviewers' structured outputs into a final release decision |

The CAB (Change Advisory Board) reviewer does **not** read the git diff. It
only consumes the `ReviewResult` objects produced by reviewers 1–4.

## Tech stack

- **Python** — application logic
- **Streamlit** — UI
- **Cursor SDK** (`cursor-sdk`) — runs each reviewer as an orchestrated agent

## Project structure

```
shipready-ai/
├── README.md
├── PROJECT_CHARTER.md
├── PRODUCT_VISION.md
├── ARCHITECTURE.md
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .gitignore
├── app.py                     # Streamlit entrypoint
├── .streamlit/
│   └── config.toml
├── reviewers/                 # one file per persona
│   ├── architecture.py
│   ├── security.py
│   ├── qa.py
│   ├── operations.py
│   └── cab.py                 # Change Advisory Board — final decision
├── models/
│   └── review_models.py       # SubmissionInput, ReviewResult, ReleaseDecision
├── orchestrator/
│   └── pipeline.py            # fan-out / fan-in coordination
├── prompts/                   # persona prompt templates (markdown)
│   ├── architecture.md
│   ├── security.md
│   ├── qa.md
│   ├── operations.md
│   └── cab.md
├── ui/
│   └── dashboard.py           # Streamlit presentation layer
├── sample_data/                # example diffs / PR descriptions for manual testing
├── generated/                  # pipeline output artifacts (gitignored contents)
└── tests/
    ├── __init__.py
    ├── test_pipeline.py
    └── fixtures/
        ├── sample.diff
        ├── sample_pr_description.md
        └── sample_api_spec.yaml
```

## Getting started

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt      # runtime
pip install -r requirements-dev.txt  # + testing/linting, for development

# 3. Configure your Cursor API key
cp .env.example .env
# then edit .env and set CURSOR_API_KEY

# 4. Run the app (not yet functional — scaffold only)
streamlit run app.py
```

## Roadmap

See [`PRODUCT_VISION.md`](./PRODUCT_VISION.md#roadmap-incremental-build-plan)
for the full incremental build plan. This increment covers **Phase 0 —
Project scaffold** only.
