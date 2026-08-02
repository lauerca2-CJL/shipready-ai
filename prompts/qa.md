<!--
Persona prompt template for the QA reviewer (reviewers/qa.py).

Responsibility of this file:
    Hold the system/instruction prompt for the QA persona as data, separate
    from orchestration code, so prompt engineering can be authored and
    reviewed independently.

TODO: write the actual instruction prompt. It should:
    - Establish the persona (testability/test coverage reviewer).
    - State what is explicitly out of scope (architecture, security,
      operations).
    - Require a structured JSON response matching the ReviewResult schema
      defined in models/review_models.py.

No prompt content has been authored yet — this is a placeholder only.
-->
