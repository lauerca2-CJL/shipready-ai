"""
Data contracts exchanged between pipeline stages.

These models are the backbone of the orchestration story: every reviewer
consumes a SubmissionInput and produces a ReviewResult, and the Release
Manager consumes only ReviewResults (never the raw SubmissionInput) to
produce a ReleaseRecommendation. Keeping these as explicit typed models —
rather than passing dicts or raw strings — makes the hand-offs between
agents auditable and enforces the single-responsibility boundaries between
reviewers at the type level, not just by convention.

Modules:
    inputs.py          SubmissionInput — what the user uploads.
    review.py           ReviewResult / Finding — what each reviewer produces.
    recommendation.py   ReleaseRecommendation — the Release Manager's output.
"""
