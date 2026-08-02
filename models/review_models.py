"""
Typed data contracts exchanged between pipeline stages.

Responsibility:
    Define every hand-off in the system as an explicit, typed model rather
    than a dict or raw string, so:
        - Each stage's input/output is validated and inspectable.
        - The CAB reviewer's isolation from the raw diff is a type-level
          guarantee (its input type simply has no field for a diff),
          not just an instruction in a prompt.
        - Reviewers are swappable/mockable in tests because their contract
          is a plain data shape, not a specific prompt or SDK call.

Planned models (not yet implemented):
    SubmissionInput
        - diff_text: str            The raw unified git diff.
        - pr_description: str       The pull request title/description.
        - api_spec: str | None      Optional API specification, raw text.
        Produced by: ui/dashboard.py (from user input).
        Consumed by: reviewers/architecture.py, security.py, qa.py,
                     operations.py.

    Finding
        - severity: Literal["info", "low", "medium", "high", "critical"]
        - title: str
        - detail: str
        - reference: str | None     Optional file/line pointer into the diff.

    ReviewResult
        - reviewer_name: str
        - verdict: Literal["approve", "approve_with_comments", "block"]
        - summary: str
        - findings: list[Finding]
        Produced by: each of the four diff-reviewers.
        Consumed by: reviewers/cab.py, ui/dashboard.py.

    ReleaseDecision
        - decision: Literal["ship", "ship_with_conditions", "hold"]
        - rationale: str
        - conditions: list[str]
        - contributing_reviews: list[ReviewResult]
        Produced by: reviewers/cab.py.
        Consumed by: ui/dashboard.py.

Do NOT implement business logic in this increment. This module currently
only documents the planned data contracts.
"""

# TODO: implement Finding, ReviewResult, SubmissionInput, and
# ReleaseDecision as pydantic BaseModels.
