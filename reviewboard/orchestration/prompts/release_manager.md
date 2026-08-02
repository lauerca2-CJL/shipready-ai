<!--
Prompt template for the Release Manager persona.

Responsibility of this file:
    Holds the system/instruction prompt for
    reviewboard.reviewers.release_manager.ReleaseManager.

Important constraint reflected in this prompt (future increment):
    Unlike the other four persona prompts, this template must NEVER
    reference or expect a git diff as input. Its only inputs are the four
    ReviewResult objects produced by the other reviewers, serialized as
    structured JSON. This mirrors the code-level constraint in
    reviewboard/reviewers/release_manager.py, so the "no diff access" rule
    is enforced at both the prompt layer and the type layer.

Planned sections (to be authored in a future increment):
    - Role framing: "You are the Release Manager chairing an enterprise
      engineering review board..."
    - Inputs: four structured ReviewResult JSON blobs (Architecture,
      Security, QA, Operations) — explicitly no diff, no PR description.
    - Required output format: JSON matching the ReleaseRecommendation
      schema.
-->
