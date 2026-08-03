"""
Architecture reviewer.

Responsibility:
    Evaluate the structural and design soundness of a proposed change —
    module boundaries, coupling, abstraction choices, adherence to existing
    architectural patterns, and long-term maintainability.

Explicitly OUT of scope for this reviewer (owned by other personas):
    - Security vulnerabilities            -> reviewers/security.py
    - Test coverage / QA process          -> reviewers/qa.py
    - Deployment/runtime operational risk -> reviewers/operations.py

Inputs:  SubmissionInput (git diff + PR description) — see
         models/review_models.py.
Output:  ReviewResult — see models/review_models.py.

Sprint 6/7 note: review() makes a REAL Cursor SDK call — the first (and so
far only) real reviewer in this project. Sprint 6 had to run this
out-of-process via a subprocess bridge because cursor-sdk required Python
3.10+ while the app targeted 3.9.6. Sprint 7 migrated the whole project to
Python 3.12, so this module now imports cursor_sdk directly and calls
Agent.prompt(...) in-process — no subprocess, no bridge script. Every other
reviewer (security.py, qa.py, operations.py, cab.py) is untouched and still
returns a hardcoded placeholder.

review() still always returns a valid ReviewResult (never raises) — the
orchestrator has no try/except around reviewer calls, so this module is the
last line of defense against a broken SDK call crashing the dashboard.
Failures (auth/network, a failed run, or a model response that isn't the
expected JSON shape) surface as verdict="block" with the error in the
summary, since there is no partial-failure policy for the pipeline yet (see
DEVELOPMENT_CONTEXT.md, outstanding TODOs).
"""

import json
import os
import re

from cursor_sdk import Agent, AgentOptions, CursorAgentError, LocalAgentOptions
from pydantic import ValidationError

from config import CURSOR_API_KEY, CURSOR_SDK_MODEL
from models.review_models import Finding, ReviewResult, SubmissionInput

_REVIEWER_NAME = "Architecture"
_PROMPT_TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prompts", "architecture.md")

# Strips the leading `<!-- ... -->` authoring-notes comment from a prompt
# markdown file — that comment documents this file's own role for humans
# reading the repo, not instructions meant for the model.
_LEADING_HTML_COMMENT = re.compile(r"^\s*<!--.*?-->\s*", re.DOTALL)


def _load_persona_prompt() -> str:
    with open(_PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        raw = f.read()
    return _LEADING_HTML_COMMENT.sub("", raw, count=1).strip()


def _build_prompt(submission: SubmissionInput) -> str:
    persona = _load_persona_prompt()
    pr_description = submission.pr_description or "(no PR description provided)"
    diff_text = submission.diff_text or "(no diff provided)"
    return (
        f"{persona}\n\n"
        f"---\n\nPull Request Description:\n{pr_description}\n\n"
        f"Git Diff:\n{diff_text}"
    )


def _blocked_result(reason: str) -> ReviewResult:
    """A safe, valid ReviewResult for any failure mode — see module docstring."""
    return ReviewResult(
        reviewer_name=_REVIEWER_NAME,
        verdict="block",
        summary=f"Architecture review could not be completed: {reason}",
    )


def _parse_agent_response(text: str) -> ReviewResult:
    """
    Parse the agent's (expected-JSON) response text into a real
    ReviewResult. Raises ValueError/JSONDecodeError/ValidationError on
    malformed output — review() converts those into a _blocked_result
    rather than letting them propagate (see ARCHITECTURE.md section 5:
    malformed structured output is its own distinct failure mode).
    """
    # Models sometimes wrap JSON in markdown fences despite instructions.
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    data = json.loads(cleaned)
    findings = [Finding(**f) for f in data.get("findings", [])]
    return ReviewResult(
        reviewer_name=_REVIEWER_NAME,
        verdict=data.get("verdict", "approve_with_comments"),
        summary=data["summary"],
        findings=findings,
    )


def review(submission: SubmissionInput) -> ReviewResult:
    """Real Cursor SDK review, called directly, in-process (see module docstring)."""
    if not CURSOR_API_KEY:
        return _blocked_result("CURSOR_API_KEY is not set. Copy .env.example to .env and fill it in.")

    prompt = _build_prompt(submission)

    try:
        result = Agent.prompt(
            prompt,
            AgentOptions(
                api_key=CURSOR_API_KEY,
                model=CURSOR_SDK_MODEL,
                local=LocalAgentOptions(cwd=os.getcwd()),
            ),
        )
    except CursorAgentError as err:
        # The run never executed: auth, config, or network problem.
        return _blocked_result(f"Cursor SDK startup failed: {err}")

    if result.status == "error":
        # The run executed but failed mid-flight.
        return _blocked_result(f"Cursor SDK run failed: run id={getattr(result, 'id', 'unknown')}")

    try:
        return _parse_agent_response(result.result or "")
    except (json.JSONDecodeError, KeyError, TypeError, ValidationError) as exc:
        return _blocked_result(f"Cursor SDK responded, but its output didn't match the expected schema: {exc}")
