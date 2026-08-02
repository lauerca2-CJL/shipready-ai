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

Do NOT implement business logic in this increment. This module currently
only documents the reviewer's responsibility and contract.
"""

# TODO: define OperationsReviewer.
# TODO: load the operations.md prompt template from prompts/.
# TODO: invoke the Cursor SDK with the submission and the loaded prompt.
# TODO: parse the agent's structured response into a ReviewResult.
