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

Do NOT implement business logic in this increment. This module currently
only documents the reviewer's responsibility and contract.
"""

# TODO: define SecurityReviewer.
# TODO: load the security.md prompt template from prompts/.
# TODO: invoke the Cursor SDK with the submission and the loaded prompt.
# TODO: parse the agent's structured response into a ReviewResult.
