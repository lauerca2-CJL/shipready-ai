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

Sprint 10 note: presentation-only polish of _render_report_markdown() and
its two helpers — the JSON contract requested from the model (decision/
overall_risk/executive_summary/business_impact/final_recommendation), the
SDK call, and the isolation rules above are all unchanged. The decision is
now a large emoji heading (the primary visual element) instead of a small
inline badge; the executive summary/business impact are word-capped
(_truncate_words()) at render time so the display stays terse even if the
model ignores the prompt's word limits — the full, untruncated text is
still kept on ReleaseDecision.executive_summary/.business_impact as the
structured source of truth, same "ask AND enforce" pattern already used
for CAB's diff-isolation. final_recommendation is split into at most 3
bullets (_split_recommendation_bullets()) without changing its underlying
type (still a single string field/JSON value — only how it's rendered
changed). The reviewer summary lines are now a compact one-liner per
reviewer (icon + name + colored decision, "(Placeholder)" for the three
reviewers with no `decision` field populated yet) instead of a bullet with
that reviewer's full assessment paragraph.
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
_CAB_DECISION_EMOJI = {"APPROVE": "\U0001f7e2", "NEEDS_CHANGES": "\U0001f7e0", "BLOCK": "\U0001f534"}
_RISK_COLORS = {"LOW": "green", "MEDIUM": "blue", "HIGH": "orange", "CRITICAL": "red"}
_REVIEWER_DECISION_COLORS = {"PASS": "green", "NEEDS_CHANGES": "orange", "BLOCK": "red"}
_CAB_DECISION_TO_LEGACY = {"APPROVE": "ship", "NEEDS_CHANGES": "ship_with_conditions", "BLOCK": "hold"}
# For reviewers still on a hardcoded verdict (no `decision` field populated
# yet) — security.py/qa.py/operations.py as of this sprint.
_VERDICT_TO_DECISION_LABEL = {"approve": "PASS", "approve_with_comments": "NEEDS_CHANGES", "block": "BLOCK"}
# Same icons as ui/components.py's STATUS_CARDS — duplicated rather than
# imported (reviewers never depend on ui/, ARCHITECTURE.md's layering rule).
_REVIEWER_EMOJI = {"Architecture": "\U0001f3d7\ufe0f", "Security": "\U0001f512", "QA": "\U0001f9ea", "Operations": "\u2699\ufe0f"}

# Sprint 10: hard word/bullet caps applied at render time, regardless of
# whether the model honored the (also updated) prompt's own limits — see
# module docstring's "ask AND enforce" note.
_EXECUTIVE_SUMMARY_MAX_WORDS = 50
_BUSINESS_IMPACT_MAX_WORDS = 40
_FINAL_RECOMMENDATION_MAX_BULLETS = 3


def _load_persona_prompt() -> str:
    with open(_PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        raw = f.read()
    return _LEADING_HTML_COMMENT.sub("", raw, count=1).strip()


def _reviewer_decision_label(result: ReviewResult) -> str:
    return result.decision or _VERDICT_TO_DECISION_LABEL.get(result.verdict, result.verdict.upper())


def _reviewer_assessment(result: ReviewResult) -> str:
    return result.overall_assessment or result.summary


def _is_placeholder_reviewer(result: ReviewResult) -> bool:
    """True for reviewers with no real SDK integration yet (security.py/qa.py/operations.py, as of this sprint)."""
    return result.decision is None


def _truncate_words(text: str, max_words: int) -> str:
    """Hard word cap for the report's display copy — see module docstring."""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip(".,;:") + "\u2026"


def _split_recommendation_bullets(text: str, max_bullets: int = _FINAL_RECOMMENDATION_MAX_BULLETS) -> List[str]:
    """
    Split final_recommendation into at most `max_bullets` short bullets.

    Prefers newline-separated points (what the updated prompts/cab.md asks
    the model for). Falls back to a sentence-ish split of a single
    paragraph so older/plain responses — the model ignored the prompt, or
    this is a pre-Sprint-10 ReleaseDecision — still render as a sensible
    (if shorter) bulleted list instead of one long line.
    """
    parts = [p.strip(" -\u2022") for p in text.split("\n") if p.strip()]
    if len(parts) <= 1:
        parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text.strip()) if p.strip()]
    return parts[:max_bullets] if parts else [text.strip()]


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
    """
    The deterministic "Reviewer Summary" section — see module docstring.

    Sprint 10: one compact line per reviewer (icon + name + colored
    decision, "(Placeholder)" tag when applicable) — no more full
    assessment paragraphs; those are still available to a human via that
    reviewer's own status card, so repeating them here just added noise.
    """
    lines = []
    for result in review_results:
        label = _reviewer_decision_label(result)
        color = _REVIEWER_DECISION_COLORS.get(label, "gray")
        icon = _REVIEWER_EMOJI.get(result.reviewer_name, "\u2022")
        placeholder_tag = " _(Placeholder)_" if _is_placeholder_reviewer(result) else ""
        lines.append(f"{icon} **{result.reviewer_name}** — :{color}[{label.replace('_', ' ')}]{placeholder_tag}")
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
    Render the CAB's structured output as one markdown report.

    Sprint 10: the decision is now the primary visual element — a large
    emoji heading, with Overall Risk directly below it — rather than a
    small inline badge line; the other sections keep the same ### headed
    style used elsewhere (reviewers/architecture.py, Sprint 8) but each is
    tightened for an executive-report read: word-capped summaries, a
    compact reviewer list, and a short bulleted final recommendation. See
    module docstring for what's enforced here vs. asked of the model.
    """
    decision_emoji = _CAB_DECISION_EMOJI.get(cab_decision, "\u26aa")
    risk_color = _RISK_COLORS.get(overall_risk, "gray")

    lines = [
        f"## {decision_emoji} {cab_decision.replace('_', ' ')}",
        f"**Overall Risk:** :{risk_color}[{overall_risk or 'n/a'}]",
        "",
        "### Executive Summary",
        _truncate_words(executive_summary, _EXECUTIVE_SUMMARY_MAX_WORDS),
        "",
        "### Reviewer Summary",
    ]
    lines += reviewer_lines if reviewer_lines else ["- No reviewer input available."]

    lines += ["", "### Business Impact", _truncate_words(business_impact, _BUSINESS_IMPACT_MAX_WORDS)]

    lines += ["", "### Final Recommendation"]
    lines += [f"- {bullet}" for bullet in _split_recommendation_bullets(final_recommendation)]

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
