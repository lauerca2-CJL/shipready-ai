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
far only) real reviewer in this project. Sprint 7 migrated the whole
project to Python 3.12 so this module imports cursor_sdk directly and
calls Agent.prompt(...) in-process (no subprocess/bridge). Every other
reviewer (security.py, qa.py, operations.py, cab.py) is untouched and still
returns a hardcoded placeholder.

Sprint 8 note: expanded the model's requested JSON shape (see
prompts/architecture.md) to a fuller enterprise-code-review style report —
decision, confidence, summary, findings grouped by severity,
recommendations, overall assessment — and added matching fields to
ReviewResult. orchestrator/pipeline.py is explicitly out of scope for this
sprint and still only forwards `ReviewResult.summary` (a plain string) to
the dashboard, so `_render_report_markdown()` below renders the full report
as ONE markdown string and puts it in `summary` — that's what lets
ui/components.py display real headings/bullets without needing the
orchestrator's yield contract to change. The granular fields (`decision`,
`confidence`, `recommendations`, `overall_assessment`) are still populated
on the ReviewResult itself too, as the structured source of truth, in case
a future sprint enriches the orchestrator to forward the full object
instead of just its summary text.

review() still always returns a valid ReviewResult (never raises) — the
orchestrator has no try/except around reviewer calls, so this module is the
last line of defense against a broken SDK call crashing the dashboard.
Failures (auth/network, a failed run, or a model response that isn't the
expected JSON shape) surface as decision="BLOCK"/verdict="block" with the
error in the summary, since there is no partial-failure policy for the
pipeline yet (see DEVELOPMENT_CONTEXT.md, outstanding TODOs).
"""

import json
import os
import re
from typing import Dict, List, Optional

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

# Most-severe-first, used to group findings into report sections.
_SEVERITY_ORDER = ("critical", "high", "medium", "low", "info")
_SEVERITY_COLORS = {"critical": "red", "high": "orange", "medium": "blue", "low": "violet", "info": "gray"}
_DECISION_COLORS = {"PASS": "green", "NEEDS_CHANGES": "orange", "BLOCK": "red"}
_DECISION_TO_VERDICT = {"PASS": "approve", "NEEDS_CHANGES": "approve_with_comments", "BLOCK": "block"}


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


def _group_findings_by_severity(findings: List[Finding]) -> Dict[str, List[Finding]]:
    """Bucket findings by severity, most-severe-first, dropping empty buckets."""
    grouped: Dict[str, List[Finding]] = {}
    for severity in _SEVERITY_ORDER:
        bucket = [f for f in findings if f.severity == severity]
        if bucket:
            grouped[severity] = bucket
    return grouped


def _render_report_markdown(
    decision: str,
    confidence: Optional[int],
    summary: str,
    findings: List[Finding],
    recommendations: List[str],
    overall_assessment: str,
) -> str:
    """
    Render the reviewer's structured output as one markdown report — see
    the Sprint 8 module docstring note for why this (rather than
    ui/components.py) is where the sections get assembled.

    This only produces markdown *text*; it makes no Streamlit/UI calls, so
    reviewers/ stays framework-agnostic (ARCHITECTURE.md's layering rule).
    ui/components.py is what actually renders this into headings and
    bullets on screen (st.markdown).
    """
    decision_label = decision.replace("_", " ")
    decision_color = _DECISION_COLORS.get(decision, "gray")
    confidence_text = f"{confidence}%" if confidence is not None else "n/a"

    lines = [
        f"**Decision:** :{decision_color}[{decision_label}]  \u00b7  **Confidence:** {confidence_text}",
        "",
        "### Summary",
        summary,
        "",
        "### Findings",
    ]

    grouped = _group_findings_by_severity(findings)
    if not grouped:
        lines.append("- No findings.")
    else:
        for severity, bucket in grouped.items():
            color = _SEVERITY_COLORS[severity]
            lines.append(f"**:{color}[{severity.upper()}]**")
            for finding in bucket:
                reference = f" (`{finding.reference}`)" if finding.reference else ""
                lines.append(f"- **{finding.title}** — {finding.detail}{reference}")

    lines += ["", "### Recommendations"]
    lines += [f"- {rec}" for rec in recommendations] if recommendations else ["- None."]

    lines += ["", "### Overall Assessment", overall_assessment or summary]

    return "\n".join(lines)


def _blocked_result(reason: str) -> ReviewResult:
    """A safe, valid ReviewResult for any failure mode — see module docstring."""
    summary = f"Architecture review could not be completed: {reason}"
    recommendations = ["Resolve the error above, then re-run the review."]
    return ReviewResult(
        reviewer_name=_REVIEWER_NAME,
        verdict="block",
        decision="BLOCK",
        confidence=None,
        summary=_render_report_markdown(
            decision="BLOCK",
            confidence=None,
            summary=summary,
            findings=[],
            recommendations=recommendations,
            overall_assessment=summary,
        ),
        findings=[],
        recommendations=recommendations,
        overall_assessment=summary,
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
    recommendations = [str(r) for r in data.get("recommendations", [])]
    decision = data.get("decision", "NEEDS_CHANGES")
    confidence = data.get("confidence")
    summary = data["summary"]
    overall_assessment = data.get("overall_assessment") or summary

    return ReviewResult(
        reviewer_name=_REVIEWER_NAME,
        verdict=_DECISION_TO_VERDICT.get(decision, "approve_with_comments"),
        decision=decision,
        confidence=confidence,
        summary=_render_report_markdown(decision, confidence, summary, findings, recommendations, overall_assessment),
        findings=findings,
        recommendations=recommendations,
        overall_assessment=overall_assessment,
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
