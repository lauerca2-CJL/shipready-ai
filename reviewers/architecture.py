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

Sprint 6 note: review() now makes a REAL Cursor SDK call — the first real
reviewer in this project. cursor-sdk requires Python 3.10+, but this app
targets Python 3.9.6 (see DEVELOPMENT_CONTEXT.md, Sprint 5), so the SDK
call happens OUT-OF-PROCESS: this module builds the prompt (persona from
prompts/architecture.md + the real diff/PR text), then shells out to
sdk_bridge.py (repo root) using a separate Python 3.10+ interpreter
(config.CURSOR_SDK_PYTHON), and parses that subprocess's JSON stdout back
into a ReviewResult. This module never imports cursor_sdk itself — only
sdk_bridge.py does. Every other reviewer (security.py, qa.py, operations.py,
cab.py) is untouched and still returns a hardcoded placeholder.

If the bridge subprocess can't be launched, times out, reports a startup
failure, a run failure, or returns text that isn't the expected JSON shape,
review() still always returns a valid ReviewResult (never raises) — the
orchestrator has no try/except around reviewer calls, so this module is
the last line of defense against a broken SDK call crashing the dashboard.
Failures surface as verdict="block" with the error in the summary, since
there is no partial-failure policy for the pipeline yet (see
DEVELOPMENT_CONTEXT.md, outstanding TODOs).
"""

import json
import os
import re
import subprocess

from pydantic import ValidationError

from config import CURSOR_SDK_BRIDGE_TIMEOUT_SECONDS, CURSOR_SDK_MODEL, CURSOR_SDK_PYTHON
from models.review_models import Finding, ReviewResult, SubmissionInput

_REVIEWER_NAME = "Architecture"
_PROMPT_TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prompts", "architecture.md")
_BRIDGE_SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sdk_bridge.py")

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


def _call_sdk_bridge(prompt: str) -> dict:
    """
    Run sdk_bridge.py under the separate Python 3.10+ SDK interpreter and
    return its parsed JSON response. Raises on subprocess-level failures
    (missing interpreter, timeout, malformed JSON) — review() converts
    those into a _blocked_result rather than letting them propagate.
    """
    payload = json.dumps({"prompt": prompt, "model": CURSOR_SDK_MODEL})
    completed = subprocess.run(
        [CURSOR_SDK_PYTHON, _BRIDGE_SCRIPT_PATH],
        input=payload,
        capture_output=True,
        text=True,
        timeout=CURSOR_SDK_BRIDGE_TIMEOUT_SECONDS,
    )
    return json.loads(completed.stdout.strip())


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
    """Real Cursor SDK review, via the out-of-process bridge (see module docstring)."""
    prompt = _build_prompt(submission)

    try:
        bridge_response = _call_sdk_bridge(prompt)
    except FileNotFoundError:
        return _blocked_result(
            f"Cursor SDK interpreter not found at {CURSOR_SDK_PYTHON!r}. "
            "See DEVELOPMENT_CONTEXT.md (Sprint 5/6) to set up .venv-sdk."
        )
    except subprocess.TimeoutExpired:
        return _blocked_result(f"Cursor SDK bridge timed out after {CURSOR_SDK_BRIDGE_TIMEOUT_SECONDS}s.")
    except json.JSONDecodeError as exc:
        return _blocked_result(f"Cursor SDK bridge returned malformed JSON: {exc}")

    status = bridge_response.get("status")
    if status != "success":
        return _blocked_result(bridge_response.get("error") or f"bridge status={status}")

    try:
        return _parse_agent_response(bridge_response.get("text") or "")
    except (json.JSONDecodeError, KeyError, TypeError, ValidationError) as exc:
        return _blocked_result(f"Cursor SDK responded, but its output didn't match the expected schema: {exc}")
