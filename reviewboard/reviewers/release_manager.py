"""
ReleaseManager

Single responsibility:
    Synthesize the four ReviewResults (Architecture, Security, QA,
    Operations) into one final ReleaseRecommendation.

Architectural rule (enforced by signature, not just prompt wording):
    The Release Manager NEVER receives the SubmissionInput or the git diff.
    Its planned `review(...)` method accepts only a list[ReviewResult] — the
    signature simply has no parameter through which a diff could be passed.
    This is deliberate: the Release Manager's job is to weigh already-
    expressed expert judgments, not to re-derive them from raw code. If it
    ever seems to need "just a bit more context," that's a signal a
    reviewer's ReviewResult schema is missing a field — not a reason to
    give the Release Manager diff access.

Inputs:  list[ReviewResult] — exactly four, one per reviewer above.
Output:  ReleaseRecommendation (see reviewboard.models.recommendation).

Note: this class intentionally does NOT subclass BaseReviewer
(reviewboard/reviewers/base.py), since BaseReviewer's contract is built
around consuming a SubmissionInput, which this class must never accept.

Left intentionally unimplemented for this scaffolding increment.
"""

# TODO: class ReleaseManager:
#     def review(self, review_results: list[ReviewResult]) -> ReleaseRecommendation: ...
