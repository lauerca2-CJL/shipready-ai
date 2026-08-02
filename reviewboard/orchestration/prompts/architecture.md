<!--
Prompt template for the Architecture Reviewer persona.

Responsibility of this file:
    Holds the system/instruction prompt for
    reviewboard.reviewers.architecture_reviewer.ArchitectureReviewer, kept
    as data (not a Python string literal) so it can be authored and
    iterated on independently of orchestration code.

Planned sections (to be authored in a future increment):
    - Role framing: "You are the Architecture Reviewer on an enterprise
      engineering review board..."
    - Scope: what this persona evaluates (see architecture_reviewer.py
      docstring) and explicit exclusions (security, QA, operations).
    - Inputs it will receive: git diff, PR description, optional API spec.
    - Required output format: JSON matching the ReviewResult schema.
-->
