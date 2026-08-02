# ReviewBoard AI

An AI **orchestration** prototype that simulates an enterprise Engineering
Review Board. Multiple specialized reviewer agents evaluate a proposed
software change from different angles, and a Release Manager agent
synthesizes their findings into a single deployment recommendation.

> **Status: scaffold only.** No orchestration or review logic is implemented
> yet. This increment establishes folder structure, module responsibilities,
> and documentation. See [`PRODUCT_VISION.md`](./PRODUCT_VISION.md) for the
> roadmap and [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the technical design.

## What this demonstrates

This project exists to demonstrate **AI orchestration**, not code generation:

- Five single-responsibility reviewer agents, each with its own prompt and
  structured output contract.
- A fan-out / fan-in pipeline: four reviewers run independently against the
  same submission, then a fifth (the Release Manager) synthesizes their
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

| # | Reviewer             | Responsibility                                              |
|---|-----------------------|--------------------------------------------------------------|
| 1 | Architecture Reviewer | Structural/design soundness, maintainability                 |
| 2 | Security Reviewer     | Vulnerabilities, authN/authZ, secrets, unsafe dependencies    |
| 3 | QA Reviewer           | Test coverage, testability, edge cases                        |
| 4 | Operations Reviewer   | Deployability, rollback safety, observability                 |
| 5 | Release Manager       | Synthesizes the four reviewers' structured outputs into a final go/no-go |

The Release Manager does **not** read the git diff. It only consumes the
`ReviewResult` objects produced by reviewers 1–4.

## Tech stack

- **Python** — application logic
- **Streamlit** — UI
- **Cursor SDK** (`cursor-sdk`) — runs each reviewer as an orchestrated agent

## Project structure

```
releaseiq/
├── README.md
├── PRODUCT_VISION.md
├── ARCHITECTURE.md
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .gitignore
├── app.py                          # Streamlit entrypoint
├── .streamlit/
│   └── config.toml
├── reviewboard/
│   ├── __init__.py
│   ├── config.py                   # centralized settings (API key, model)
│   ├── models/                     # typed data contracts
│   │   ├── __init__.py
│   │   ├── inputs.py                # SubmissionInput
│   │   ├── review.py                # ReviewResult / Finding
│   │   └── recommendation.py        # ReleaseRecommendation
│   ├── reviewers/                  # one file per persona
│   │   ├── __init__.py
│   │   ├── base.py                  # shared reviewer contract
│   │   ├── architecture_reviewer.py
│   │   ├── security_reviewer.py
│   │   ├── qa_reviewer.py
│   │   ├── operations_reviewer.py
│   │   └── release_manager.py
│   ├── orchestration/
│   │   ├── __init__.py
│   │   ├── pipeline.py              # fan-out / fan-in coordination
│   │   └── prompts/                 # persona prompt templates (markdown)
│   │       ├── architecture.md
│   │       ├── security.md
│   │       ├── qa.md
│   │       ├── operations.md
│   │       └── release_manager.md
│   └── ui/                         # Streamlit presentation layer
│       ├── __init__.py
│       ├── sidebar.py
│       ├── results.py
│       └── state.py
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
