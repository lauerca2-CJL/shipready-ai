<!--
Prompt template for the QA Reviewer persona.

Responsibility of this file:
    Holds the system/instruction prompt for
    reviewboard.reviewers.qa_reviewer.QAReviewer, kept as data (not a
    Python string literal) so it can be authored and iterated on
    independently of orchestration code.

Planned sections (to be authored in a future increment):
    - Role framing: "You are the QA Reviewer on an enterprise engineering
      review board..."
    - Scope: what this persona evaluates (see qa_reviewer.py docstring)
      and explicit exclusions (architecture, security, operations).
    - Inputs it will receive: git diff, PR description.
    - Required output format: JSON matching the ReviewResult schema.
-->
