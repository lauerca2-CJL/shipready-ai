"""
Security reviewer.

Responsibility:
    Evaluate the diff for security risk — injection vectors, authN/authZ
    regressions, secrets handling, unsafe dependencies, and (when an API
    specification is available) whether new/changed endpoints introduce
    exposure.

Explicitly OUT of scope for this reviewer (owned by other personas):
    - General code structure/design -> reviewers/architecture.py
    - Test coverage                 -> reviewers/qa.py
    - Deployment/runtime concerns   -> reviewers/operations.py

Inputs:  SubmissionInput (git diff + PR description) — see
         models/review_models.py.
Output:  ReviewResult — see models/review_models.py.

Sprint 3 note: review() returns a hardcoded placeholder ReviewResult. No
Cursor SDK or LLM call happens here yet — that's deferred to a future
sprint, at which point only this function's body changes; its signature
and the orchestrator's use of it stay the same.
"""

from models.review_models import ReviewResult, SubmissionInput

# TODO: load the security.md prompt template from prompts/.
# TODO: invoke the Cursor SDK with the submission and the loaded prompt.
# TODO: parse the agent's structured response into a ReviewResult.


def review(submission: SubmissionInput) -> ReviewResult:
    """Placeholder review — returns a simulated result, no AI involved."""
    return ReviewResult(
        reviewer_name="Security",
        verdict="approve",
        summary="Placeholder review: no vulnerabilities detected (simulated).",
    )
