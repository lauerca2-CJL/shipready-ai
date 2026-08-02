"""
QA reviewer.

Responsibility:
    Evaluate testability and test coverage implications of the change —
    whether the diff includes/updates tests proportional to its risk,
    whether edge cases implied by the PR description are covered, and
    whether the change is verifiable before deployment.

Explicitly OUT of scope for this reviewer (owned by other personas):
    - Design/structural quality   -> reviewers/architecture.py
    - Security posture            -> reviewers/security.py
    - Deployment/runtime concerns -> reviewers/operations.py

Inputs:  SubmissionInput (git diff + PR description) — see
         models/review_models.py.
Output:  ReviewResult — see models/review_models.py.

Do NOT implement business logic in this increment. This module currently
only documents the reviewer's responsibility and contract.
"""

# TODO: define QAReviewer.
# TODO: load the qa.md prompt template from prompts/.
# TODO: invoke the Cursor SDK with the submission and the loaded prompt.
# TODO: parse the agent's structured response into a ReviewResult.
