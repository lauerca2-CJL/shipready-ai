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

Do NOT implement business logic in this increment. This module currently
only documents the reviewer's responsibility and contract.
"""

# TODO: define ArchitectureReviewer.
# TODO: load the architecture.md prompt template from prompts/.
# TODO: invoke the Cursor SDK with the submission and the loaded prompt.
# TODO: parse the agent's structured response into a ReviewResult.
