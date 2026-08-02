"""
Orchestration layer.

Responsibility:
    Coordinates the fan-out/fan-in execution of the review board:
        1. Fan-out: run ArchitectureReviewer, SecurityReviewer, QAReviewer,
           and OperationsReviewer concurrently against the same
           SubmissionInput.
        2. Fan-in: pass their four ReviewResults (and nothing else) to the
           ReleaseManager to produce the final ReleaseRecommendation.

    This is the only layer that knows the pipeline's shape — reviewers don't
    know about each other, and the UI doesn't know how reviewers are
    executed (sequentially, concurrently, local vs. cloud agents, etc.).

Modules:
    pipeline.py   The run_review_pipeline() entrypoint used by app.py.
    prompts/      Prompt templates, one per persona, kept as data (markdown)
                  rather than inline strings so they can be authored and
                  reviewed independently of orchestration code.
"""
