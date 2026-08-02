"""
Review pipeline orchestration.

Responsibility:
    Own the end-to-end sequencing of a review run:
        1. Fan-out (parallel, independent): send the same SubmissionInput to
           the four diff-reviewers (reviewers/architecture.py, security.py,
           qa.py, operations.py).
        2. Fan-in (sequential, dependent): once all four ReviewResults are
           available, pass them — and nothing else — to the CAB reviewer
           (reviewers/cab.py) to produce the final ReleaseDecision.

    This is the only module that knows the shape of the review pipeline.
    Reviewers never call each other and never know the pipeline exists.

Planned implementation notes (not yet implemented):
    - The four diff-reviewers are independent of one another, so they are
      candidates for concurrent execution (the Cursor SDK's async client)
      rather than four sequential round-trips.
    - The CAB call is strictly sequential and depends on all four reviewer
      results being available first.
    - Partial-failure handling (e.g. one reviewer's agent call errors out or
      returns malformed structured output) needs a defined policy. Deferred
      to the increment where the pipeline is actually implemented.

Planned signature:

    def run_review_pipeline(submission: SubmissionInput) -> ReleaseDecision:
        '''Runs all four reviewers, then the CAB reviewer, and returns the
        final ReleaseDecision (with the individual ReviewResults attached
        for traceability).'''

Do NOT implement business logic in this increment. This module currently
only documents the planned orchestration flow.
"""

# TODO: implement run_review_pipeline().
