"""
ReviewResult — the structured output produced by EACH specialized reviewer.

Responsibility:
    - Defines a single, shared output shape that every diff-reviewer
      (Architecture, Security, QA, Operations) must conform to. A shared
      shape is what lets the orchestration pipeline treat all four
      reviewers uniformly, and lets the Release Manager consume them
      generically without knowing the internals of any one persona.

Planned fields (not yet implemented):
    - reviewer_name: str             e.g. "Architecture Reviewer"
    - verdict: Literal["approve", "approve_with_comments", "block"]
    - summary: str                   One-paragraph human-readable summary.
    - findings: list[Finding]        Structured list of individual findings.

Planned Finding sub-model:
    - severity: Literal["info", "low", "medium", "high", "critical"]
    - title: str
    - detail: str
    - reference: str | None          Optional file/line pointer into the diff.

Left intentionally unimplemented for this scaffolding increment.
"""

# TODO: implement Finding and ReviewResult as pydantic BaseModels.
