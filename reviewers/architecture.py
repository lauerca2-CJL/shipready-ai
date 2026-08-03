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

Sprint 3 note: review() returns a hardcoded placeholder ReviewResult. No
Cursor SDK or LLM call happens here yet — that's deferred to a future
sprint, at which point only this function's body changes; its signature
and the orchestrator's use of it stay the same.
"""

from models.review_models import ReviewResult, SubmissionInput

# TODO: load the architecture.md prompt template from prompts/.
# TODO: invoke the Cursor SDK with the submission and the loaded prompt.
# TODO: parse the agent's structured response into a ReviewResult.


def review(submission: SubmissionInput) -> ReviewResult:
    """Placeholder review — returns a simulated result, no AI involved."""
    return ReviewResult(
        reviewer_name="Architecture",
        verdict="approve",
        summary="Placeholder review: no structural issues detected (simulated).",
    )
