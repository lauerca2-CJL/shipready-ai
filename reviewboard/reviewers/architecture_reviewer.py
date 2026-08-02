"""
ArchitectureReviewer

Single responsibility:
    Evaluate the structural and design soundness of the proposed change —
    module boundaries, coupling, abstraction choices, adherence to existing
    architectural patterns, and long-term maintainability.

Explicitly OUT of scope for this reviewer (owned by other personas):
    - Security vulnerabilities            -> SecurityReviewer
    - Test coverage / QA process          -> QAReviewer
    - Deployment/runtime operational risk -> OperationsReviewer

Inputs:  SubmissionInput (diff + PR description; API spec if relevant to
         interface/contract design).
Output:  ReviewResult (see reviewboard.models.review).

Left intentionally unimplemented for this scaffolding increment.
"""

# TODO: class ArchitectureReviewer(BaseReviewer): ...
