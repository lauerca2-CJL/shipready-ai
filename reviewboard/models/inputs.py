"""
SubmissionInput — the raw materials a user uploads for review.

Responsibility:
    - Represents exactly what the human submits: the git diff, the PR
      description, and an optional API specification.
    - This is the ONLY model in the system that carries the raw diff.
      The four diff-reviewers receive it directly; the Release Manager
      never does (see reviewboard.reviewers.release_manager).

Planned fields (not yet implemented):
    - diff_text: str            The raw unified git diff.
    - pr_description: str       The pull request title/description.
    - api_spec: str | None      Optional API specification, raw text.
    - submitted_at: datetime    Timestamp, for auditability in the UI.

Planned validation:
    - diff_text and pr_description should be required/non-empty.
    - api_spec is optional and may be None.

Left intentionally unimplemented for this scaffolding increment.
"""

# TODO: implement as a pydantic BaseModel (or frozen dataclass) with the
# fields described above.
