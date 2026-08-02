<!--
Prompt template for the Operations Reviewer persona.

Responsibility of this file:
    Holds the system/instruction prompt for
    reviewboard.reviewers.operations_reviewer.OperationsReviewer, kept as
    data (not a Python string literal) so it can be authored and iterated
    on independently of orchestration code.

Planned sections (to be authored in a future increment):
    - Role framing: "You are the Operations Reviewer on an enterprise
      engineering review board..."
    - Scope: what this persona evaluates (see operations_reviewer.py
      docstring) and explicit exclusions (architecture, security, QA).
    - Inputs it will receive: git diff, PR description, optional API spec.
    - Required output format: JSON matching the ReviewResult schema.
-->
