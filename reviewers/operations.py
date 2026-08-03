"""
Operations reviewer.

Responsibility:
    Evaluate operational/deployment risk — backward compatibility, migration
    safety, rollback strategy, observability (logging/metrics/alerts), and
    infrastructure or config changes implied by the diff.

Explicitly OUT of scope for this reviewer (owned by other personas):
    - Design/structural quality -> reviewers/architecture.py
    - Security posture          -> reviewers/security.py
    - Test coverage             -> reviewers/qa.py

Inputs:  SubmissionInput (git diff + PR description, optional API spec for
         contract-compatibility checks) — see models/review_models.py.
Output:  ReviewResult — see models/review_models.py.

Sprint 3 note: review() returns a hardcoded placeholder ReviewResult. No
Cursor SDK or LLM call happens here yet — that's deferred to a future
sprint, at which point only this function's body changes; its signature
and the orchestrator's use of it stay the same.
"""

from models.review_models import ReviewResult, SubmissionInput

# TODO: load the operations.md prompt template from prompts/.
# TODO: invoke the Cursor SDK with the submission and the loaded prompt.
# TODO: parse the agent's structured response into a ReviewResult.


def review(submission: SubmissionInput) -> ReviewResult:
    """Placeholder review — returns a simulated result, no AI involved."""
    return ReviewResult(
        reviewer_name="Operations",
        verdict="approve",
        summary="Placeholder review: deployment risk looks low (simulated).",
    )
