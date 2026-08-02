"""
CAB (Change Advisory Board) reviewer.

Responsibility:
    Synthesize the four ReviewResults (Architecture, Security, QA,
    Operations) into one final release decision.

Architectural rule (to be enforced by the eventual function/method
signature, not just prompt wording):
    The CAB reviewer NEVER receives the raw git diff or PR description. It
    only ever consumes the four ReviewResult objects produced by the other
    reviewers. If it ever seems to need "just a bit more context," that is
    a signal a ReviewResult schema is missing a field — not a reason to
    give the CAB reviewer diff access.

Inputs:  list[ReviewResult] — exactly four, one per reviewer above.
Output:  ReleaseDecision — see models/review_models.py.

Do NOT implement business logic in this increment. This module currently
only documents the CAB's responsibility and contract.
"""

# TODO: define CAB / run_cab().
# TODO: load the cab.md prompt template from prompts/.
# TODO: invoke the Cursor SDK with only the four ReviewResults (no diff).
# TODO: parse the agent's structured response into a ReleaseDecision.
