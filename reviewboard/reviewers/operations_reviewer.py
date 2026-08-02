"""
OperationsReviewer

Single responsibility:
    Evaluate operational/deployment risk — backward compatibility, migration
    safety, rollback strategy, observability (logging/metrics/alerts), and
    infrastructure or config changes implied by the diff.

Explicitly OUT of scope for this reviewer (owned by other personas):
    - Design/structural quality -> ArchitectureReviewer
    - Security posture          -> SecurityReviewer
    - Test coverage             -> QAReviewer

Inputs:  SubmissionInput (diff, PR description, optional API spec for
         contract-compatibility checks).
Output:  ReviewResult (see reviewboard.models.review).

Left intentionally unimplemented for this scaffolding increment.
"""

# TODO: class OperationsReviewer(BaseReviewer): ...
