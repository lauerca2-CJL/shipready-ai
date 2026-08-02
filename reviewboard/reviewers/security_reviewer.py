"""
SecurityReviewer

Single responsibility:
    Evaluate the diff for security risk — injection vectors, authN/authZ
    regressions, secrets handling, unsafe dependencies, and (when an API
    spec is provided) whether new/changed endpoints introduce exposure.

Explicitly OUT of scope for this reviewer (owned by other personas):
    - General code structure/design -> ArchitectureReviewer
    - Test coverage                 -> QAReviewer
    - Deployment/runtime concerns   -> OperationsReviewer

Inputs:  SubmissionInput (diff, PR description, optional API spec).
Output:  ReviewResult (see reviewboard.models.review).

Left intentionally unimplemented for this scaffolding increment.
"""

# TODO: class SecurityReviewer(BaseReviewer): ...
