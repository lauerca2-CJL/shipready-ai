"""
QAReviewer

Single responsibility:
    Evaluate testability and test coverage implications of the change —
    whether the diff includes/updates tests proportional to its risk,
    whether edge cases implied by the PR description are covered, and
    whether the change is verifiable pre-deployment.

Explicitly OUT of scope for this reviewer (owned by other personas):
    - Design/structural quality   -> ArchitectureReviewer
    - Security posture            -> SecurityReviewer
    - Deployment/runtime concerns -> OperationsReviewer

Inputs:  SubmissionInput (diff, PR description).
Output:  ReviewResult (see reviewboard.models.review).

Left intentionally unimplemented for this scaffolding increment.
"""

# TODO: class QAReviewer(BaseReviewer): ...
