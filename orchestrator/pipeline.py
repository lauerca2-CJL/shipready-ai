"""
Review pipeline orchestration.

Responsibility:
    Own the end-to-end sequencing of a review run:
        1. Run the four diff-reviewers (reviewers/architecture.py,
           security.py, qa.py, operations.py) against the same
           SubmissionInput, in that fixed order.
        2. Once all four ReviewResults are available, pass them — and
           nothing else — to the CAB reviewer (reviewers/cab.py) to produce
           the final ReleaseDecision.

    This is the only module that knows the shape of the review pipeline.
    Reviewers never call each other and never know the pipeline exists.

Sprint 3 note: this runs the reviewers sequentially (not concurrently) and
every reviewer returns a hardcoded placeholder result — no Cursor SDK or
LLM call happens anywhere in this module. See ARCHITECTURE.md section 2 for
the eventual concurrent fan-out design and section 5 for the planned Cursor
SDK integration; neither is wired up yet.

run_review_pipeline() is a generator that yields (step_name, summary) after
each reviewer completes, so callers (the dashboard) can update UI state
incrementally instead of waiting for the whole pipeline to finish. A short
delay — read from config.REVIEW_STEP_DELAY_SECONDS rather than hardcoded
here — is inserted between steps purely so the sequential workflow is
visible to a human watching the dashboard; it stands in for the real
latency a live agent call will eventually have.
"""

import time
from typing import Iterator, List, Optional, Tuple

from config import REVIEW_STEP_DELAY_SECONDS
from models.review_models import ReviewResult, SubmissionInput
from reviewers import architecture, cab, operations, qa, security

# Fixed fan-out order per PROJECT_CHARTER.md's review specialists.
_DIFF_REVIEWERS = (
    architecture,
    security,
    qa,
    operations,
)


def run_review_pipeline(
    submission: Optional[SubmissionInput] = None,
) -> Iterator[Tuple[str, str]]:
    """
    Run the four diff-reviewers in order, then the CAB reviewer.

    Yields (step_name, summary) once per completed step (Architecture,
    Security, QA, Operations, then "Change Advisory Board"), with a short
    delay between steps. The CAB reviewer only ever receives the four
    ReviewResults collected here — never `submission` — preserving the
    "no diff access" rule documented in reviewers/cab.py.
    """
    submission = submission or SubmissionInput()
    review_results: List[ReviewResult] = []

    for reviewer_module in _DIFF_REVIEWERS:
        result = reviewer_module.review(submission)
        review_results.append(result)
        yield result.reviewer_name, result.summary
        time.sleep(REVIEW_STEP_DELAY_SECONDS)

    decision = cab.review(review_results)
    yield "Change Advisory Board", decision.rationale
