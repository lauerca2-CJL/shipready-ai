"""
CAB (Change Advisory Board) reviewer.

Responsibility:
    Synthesize the four ReviewResults (Architecture, Security, QA,
    Operations) into one final release decision.

Architectural rule (enforced by review()'s signature, not just prompt
wording):
    The CAB reviewer NEVER receives the raw git diff or PR description. It
    only ever consumes the four ReviewResult objects produced by the other
    reviewers. If it ever seems to need "just a bit more context," that is
    a signal a ReviewResult schema is missing a field — not a reason to
    give the CAB reviewer diff access.

Inputs:  list[ReviewResult] — exactly four, one per reviewer above.
Output:  ReleaseDecision — see models/review_models.py.

Sprint 9 note: review() makes a REAL Cursor SDK call, same in-process
pattern as reviewers/architecture.py (Sprint 6/7) — no subprocess/bridge.
The isolation rule above is enforced at TWO levels, not just one:
    1. review()'s signature — it is structurally impossible to pass this
       function a diff/PR description; there's no parameter for it.
    2. The SDK call itself runs with `local=LocalAgentOptions(cwd=...)`
       pointed at an EMPTY, throwaway temp directory — never this repo.
       LocalAgentOptions grants the underlying agent real file/shell tool
       access to whatever `cwd` it's given (see the `sdk` skill); pointing
       it at this repo would let the model just run `git diff` itself and
       defeat rule #1 regardless of what the prompt says. An empty temp
       dir means there's structurally nothing for it to find even if it
       tried.

The "Reviewer Summary" section of the final report is built deterministically
in Python from the four ReviewResult objects (name + decision/verdict +
overall_assessment/summary) — NOT requested from the model. That data
already exists in typed form; asking the model to reproduce it would just
add a chance of it paraphrasing/misstating a reviewer's own verdict. The
model is only asked for the five fields that are genuinely a judgment call:
decision, overall_risk, executive_summary, business_impact,
final_recommendation. See prompts/cab.md.

review() still always returns a valid ReleaseDecision (never raises) — same
last-line-of-defense reasoning as reviewers/architecture.py, since
orchestrator/pipeline.py has no try/except around this call either.
"""

import json
import os
import re
import tempfile
from typing import List, Optional

from cursor_sdk import Agent, AgentOptions, CursorAgentError, LocalAgentOptions
from pydantic import ValidationError

from config import CURSOR_API_KEY, CURSOR_SDK_MODEL
from models.review_models import ReleaseDecision, ReviewResult

_PROMPT_TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prompts", "cab.md")

# Duplicated (rather than imported) from reviewers/architecture.py — small,
# and reviewers deliberately never depend on each other (ARCHITECTURE.md).
_LEADING_HTML_COMMENT = re.compile(r"^\s*<!--.*?-->\s*", re.DOTALL)

_CAB_DECISION_COLORS = {"APPROVE": "green", "NEEDS_CHANGES": "orange", "BLOCK": "red"}
_RISK_COLORS = {"LOW": "green", "MEDIUM": "blue", "HIGH": "orange", "CRITICAL": "red"}
_REVIEWER_DECISION_COLORS = {"PASS": "green", "NEEDS_CHANGES": "orange", "BLOCK": "red"}
_CAB_DECISION_TO_LEGACY = {"APPROVE": "ship", "NEEDS_CHANGES": "ship_with_conditions", "BLOCK": "hold"}
# For reviewers still on a hardcoded verdict (no `decision` field populated
# yet) — security.py/qa.py/operations.py as of this sprint.
_VERDICT_TO_DECISION_LABEL = {"approve": "PASS", "approve_with_comments": "NEEDS_CHANGES", "block": "BLOCK"}


def _load_persona_prompt() -> str:
    with open(_PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        raw = f.read()
    return _LEADING_HTML_COMMENT.sub("", raw, count=1).strip()


def _reviewer_decision_label(result: ReviewResult) -> str:
    return result.decision or _VERDICT_TO_DECISION_LABEL.get(result.verdict, result.verdict.upper())


def _reviewer_assessment(result: ReviewResult) -> str:
    return result.overall_assessment or result.summary


def _build_prompt(review_results: List[ReviewResult]) -> str:
    persona = _load_persona_prompt()
    blocks = []
    for result in review_results:
        recommendations = "; ".join(result.recommendations) if result.recommendations else "(none)"
        blocks.append(
            f"### {result.reviewer_name}\n"
            f"Decision: {_reviewer_decision_label(result)}\n"
            f"Assessment: {_reviewer_assessment(result)}\n"
            f"Recommendations: {recommendations}"
        )
    return f"{persona}\n\n---\n\nReviewer Outputs:\n\n" + "\n\n".join(blocks)


def _build_reviewer_summary_lines(review_results: List[ReviewResult]) -> List[str]:
    """The deterministic "Reviewer Summary" section — see module docstring."""
    lines = []
    for result in review_results:
        label = _reviewer_decision_label(result)
        color = _REVIEWER_DECISION_COLORS.get(label, "gray")
        lines.append(f"- **{result.reviewer_name}** — :{color}[{label.replace('_', ' ')}] — {_reviewer_assessment(result)}")
    return lines


def _render_report_markdown(
    cab_decision: str,
    overall_risk: Optional[str],
    executive_summary: str,
    reviewer_lines: List[str],
    business_impact: str,
    final_recommendation: str,
) -> str:
    """
    Render the CAB's structured output as one markdown report, in the same
    style as reviewers/architecture.py's _render_report_markdown() (Sprint
    8) — decision/risk badge line, then ### headed sections with bullets.
    """
    decision_color = _CAB_DECISION_COLORS.get(cab_decision, "gray")
    risk_color = _RISK_COLORS.get(overall_risk, "gray")

    lines = [
        f"**Decision:** :{decision_color}[{cab_decision.replace('_', ' ')}]"
        f"  \u00b7  **Overall Risk:** :{risk_color}[{overall_risk or 'n/a'}]",
        "",
        "### Executive Summary",
        executive_summary,
        "",
        "### Reviewer Summary",
    ]
    lines += reviewer_lines if reviewer_lines else ["- No reviewer input available."]
    lines += ["", "### Business Impact", business_impact, "", "### Final Recommendation", final_recommendation]
    return "\n".join(lines)


def _blocked_result(review_results: List[ReviewResult], reason: str) -> ReleaseDecision:
    """A safe, valid ReleaseDecision for any failure mode — see module docstring."""
    executive_summary = f"CAB synthesis could not be completed: {reason}"
    business_impact = "Unknown — the CAB synthesis step failed before an assessment could be produced."
    final_recommendation = "Resolve the error above, then re-run the review."
    reviewer_lines = _build_reviewer_summary_lines(review_results)

    return ReleaseDecision(
        decision="hold",
        rationale=_render_report_markdown(
            "BLOCK", None, executive_summary, reviewer_lines, business_impact, final_recommendation
        ),
        contributing_reviews=review_results,
        cab_decision="BLOCK",
        overall_risk=None,
        executive_summary=executive_summary,
        reviewer_summary=reviewer_lines,
        business_impact=business_impact,
        final_recommendation=final_recommendation,
    )


def _parse_agent_response(text: str, review_results: List[ReviewResult]) -> ReleaseDecision:
    """
    Parse the agent's (expected-JSON) response text into a real
    ReleaseDecision. Raises ValueError/JSONDecodeError/ValidationError on
    malformed output — review() converts those into a _blocked_result
    rather than letting them propagate, same convention as
    reviewers/architecture.py.
    """
    # Models sometimes wrap JSON in markdown fences despite instructions.
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    data = json.loads(cleaned)

    cab_decision = data.get("decision", "NEEDS_CHANGES")
    overall_risk = data.get("overall_risk")
    executive_summary = data["executive_summary"]
    business_impact = data.get("business_impact") or executive_summary
    final_recommendation = data["final_recommendation"]
    reviewer_lines = _build_reviewer_summary_lines(review_results)

    return ReleaseDecision(
        decision=_CAB_DECISION_TO_LEGACY.get(cab_decision, "ship_with_conditions"),
        rationale=_render_report_markdown(
            cab_decision, overall_risk, executive_summary, reviewer_lines, business_impact, final_recommendation
        ),
        contributing_reviews=review_results,
        cab_decision=cab_decision,
        overall_risk=overall_risk,
        executive_summary=executive_summary,
        reviewer_summary=reviewer_lines,
        business_impact=business_impact,
        final_recommendation=final_recommendation,
    )


def review(review_results: List[ReviewResult]) -> ReleaseDecision:
    """Real Cursor SDK synthesis, called directly, in-process (see module docstring)."""
    if not CURSOR_API_KEY:
        return _blocked_result(review_results, "CURSOR_API_KEY is not set. Copy .env.example to .env and fill it in.")

    prompt = _build_prompt(review_results)

    # Empty, throwaway directory — never this repo — so the underlying
    # agent has nothing to inspect via file/shell tools even if it tried.
    # See module docstring, isolation rule #2.
    with tempfile.TemporaryDirectory(prefix="shipready-cab-") as isolated_cwd:
        try:
            result = Agent.prompt(
                prompt,
                AgentOptions(
                    api_key=CURSOR_API_KEY,
                    model=CURSOR_SDK_MODEL,
                    local=LocalAgentOptions(cwd=isolated_cwd),
                ),
            )
        except CursorAgentError as err:
            # The run never executed: auth, config, or network problem.
            return _blocked_result(review_results, f"Cursor SDK startup failed: {err}")

        if result.status == "error":
            # The run executed but failed mid-flight.
            return _blocked_result(review_results, f"Cursor SDK run failed: run id={getattr(result, 'id', 'unknown')}")

    try:
        return _parse_agent_response(result.result or "", review_results)
    except (json.JSONDecodeError, KeyError, TypeError, ValidationError) as exc:
        return _blocked_result(
            review_results, f"Cursor SDK responded, but its output didn't match the expected schema: {exc}"
        )
