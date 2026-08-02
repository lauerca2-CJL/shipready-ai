"""
BaseReviewer — shared contract for the four diff-reviewing agents.

Responsibility:
    - Defines the common interface every diff-reviewer persona implements,
      so the orchestration pipeline can treat all four uniformly (fan-out to
      identical `.review(submission)` calls regardless of persona).
    - Owns the shared mechanics that should NOT be duplicated per reviewer:
        - Loading the reviewer's prompt template from
          reviewboard/orchestration/prompts/.
        - Invoking the Cursor SDK (one-shot Agent.prompt call — each review
          is a single independent judgment, not a multi-turn conversation).
        - Parsing the agent's structured (JSON) response into a
          ReviewResult, surfacing parse failures distinctly from agent
          execution failures.

Planned shape (not yet implemented):

    class BaseReviewer(ABC):
        persona_name: str
        prompt_filename: str

        def build_prompt(self, submission: SubmissionInput) -> str: ...
        def review(self, submission: SubmissionInput) -> ReviewResult: ...

Note: ReleaseManager intentionally does NOT subclass BaseReviewer — see
reviewboard/reviewers/release_manager.py for why its contract differs.

Left intentionally unimplemented for this scaffolding increment.
"""

# TODO: implement BaseReviewer as an abstract base class.
