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

Sprint 3 note: review() returns a hardcoded placeholder ReleaseDecision. No
Cursor SDK or LLM call happens here yet — that's deferred to a future
sprint, at which point only this function's body changes; its signature
(still no diff access) stays the same.
"""

from typing import List

from models.review_models import ReleaseDecision, ReviewResult

# TODO: load the cab.md prompt template from prompts/.
# TODO: invoke the Cursor SDK with only the four ReviewResults (no diff).
# TODO: parse the agent's structured response into a ReleaseDecision.


def review(review_results: List[ReviewResult]) -> ReleaseDecision:
    """Placeholder synthesis — returns a simulated decision, no AI involved."""
    return ReleaseDecision(
        decision="ship",
        rationale=(
            "Placeholder decision: all reviewers returned a simulated "
            "approval (simulated)."
        ),
        contributing_reviews=review_results,
    )
