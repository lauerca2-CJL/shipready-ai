<!--
Persona prompt template for the CAB (Change Advisory Board) reviewer
(reviewers/cab.py).

Responsibility of this file:
    Hold the system/instruction prompt for the CAB persona as data, separate
    from orchestration code, so prompt engineering can be authored and
    reviewed independently.

TODO: write the actual instruction prompt. It should:
    - Establish the persona (final release decision synthesizer).
    - Explicitly state that this prompt must never reference or expect raw
      diff content — its only input is the four ReviewResults.
    - Require a structured JSON response matching the ReleaseDecision schema
      defined in models/review_models.py.

No prompt content has been authored yet — this is a placeholder only.
-->
