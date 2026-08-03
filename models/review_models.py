"""
Typed data contracts exchanged between pipeline stages.

Responsibility:
    Define every hand-off in the system as an explicit, typed model rather
    than a dict or raw string, so:
        - Each stage's input/output is validated and inspectable.
        - The CAB reviewer's isolation from the raw diff is a type-level
          guarantee (CAB.review() takes list[ReviewResult], which has no
          field for a diff), not just an instruction in a prompt.
        - Reviewers are swappable/mockable in tests because their contract
          is a plain data shape, not a specific prompt or SDK call.

Sprint 3 note: these models are populated with placeholder data by
reviewers/*.py — no Cursor SDK or LLM call produces them yet. Real reviewer
implementations (a future sprint) will fill the same shapes.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class SubmissionInput(BaseModel):
    """What the user submits for review. Produced by ui/dashboard.py."""

    diff_text: str = ""
    pr_description: str = ""
    api_spec: Optional[str] = None


class Finding(BaseModel):
    """A single structured observation within a ReviewResult."""

    severity: Literal["info", "low", "medium", "high", "critical"] = "info"
    title: str
    detail: str
    reference: Optional[str] = None


class ReviewResult(BaseModel):
    """
    The structured output of one diff-reviewer (Architecture, Security, QA,
    or Operations). Consumed by the CAB reviewer and the dashboard.
    """

    reviewer_name: str
    verdict: Literal["approve", "approve_with_comments", "block"] = "approve"
    summary: str
    findings: List[Finding] = Field(default_factory=list)


class ReleaseDecision(BaseModel):
    """
    The CAB reviewer's synthesis of all four ReviewResults into a final
    release decision. Consumed by the dashboard.
    """

    decision: Literal["ship", "ship_with_conditions", "hold"] = "ship"
    rationale: str
    conditions: List[str] = Field(default_factory=list)
    contributing_reviews: List[ReviewResult] = Field(default_factory=list)
