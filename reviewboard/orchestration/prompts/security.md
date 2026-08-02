<!--
Prompt template for the Security Reviewer persona.

Responsibility of this file:
    Holds the system/instruction prompt for
    reviewboard.reviewers.security_reviewer.SecurityReviewer, kept as data
    (not a Python string literal) so it can be authored and iterated on
    independently of orchestration code.

Planned sections (to be authored in a future increment):
    - Role framing: "You are the Security Reviewer on an enterprise
      engineering review board..."
    - Scope: what this persona evaluates (see security_reviewer.py
      docstring) and explicit exclusions (architecture, QA, operations).
    - Inputs it will receive: git diff, PR description, optional API spec.
    - Required output format: JSON matching the ReviewResult schema.
-->
