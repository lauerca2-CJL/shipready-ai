"""
ReleaseRecommendation — the final output of the entire review board.

Responsibility:
    - Represents the Release Manager's synthesis of all four ReviewResults
      into a single go/no-go recommendation for deployment.
    - This is the only model that represents a cross-cutting judgment; it is
      produced exclusively by the Release Manager and never by an individual
      reviewer.

Planned fields (not yet implemented):
    - decision: Literal["ship", "ship_with_conditions", "hold"]
    - rationale: str                     Synthesized reasoning across reviewers.
    - conditions: list[str]              Required follow-ups if not a clean ship.
    - contributing_reviews: list[ReviewResult]
      The reviewer outputs this recommendation was based on, retained for
      traceability/audit when rendered in the UI.

Left intentionally unimplemented for this scaffolding increment.
"""

# TODO: implement as a pydantic BaseModel.
