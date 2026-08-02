# Product Vision — ReviewBoard AI

## Problem

Enterprise engineering organizations often run a manual "review board" step
before high-risk changes ship: architects, security engineers, QA leads, and
operations/SRE staff each look at a proposed change from their own lens, and
a release manager weighs their input before approving deployment. In
practice this process is:

- **Slow** — coordinating five specialists' calendars for every non-trivial
  change doesn't scale.
- **Inconsistent** — the quality of review depends heavily on who happens to
  be in the room and how much context they were given.
- **Opaque** — the reasoning behind a "hold" or "ship" decision is often
  captured in a Slack thread or a reviewer's head, not in a structured,
  reusable artifact.

## Vision

ReviewBoard AI simulates this review board using orchestrated AI agents,
each standing in for one specialist role. The goal is not to replace human
judgment on high-stakes releases, but to demonstrate that a **well-designed
multi-agent orchestration** — with strict single-responsibility boundaries
and structured hand-offs between agents — can produce the same kind of
layered, defensible review a human board would, consistently and quickly.

This project is explicitly a demonstration of **AI orchestration
engineering**: how to decompose a complex judgment task into independent
specialist agents, define the contracts between them, and coordinate their
execution — not a demonstration of AI-assisted code generation.

## Core principles

1. **Single responsibility per reviewer.** Each reviewer agent has exactly
   one lens (architecture, security, QA, operations) and is explicitly
   scoped away from the others' concerns. A reviewer that starts commenting
   on another discipline's territory is a design smell, not a feature.

2. **Structured hand-offs, not shared raw context.** Reviewers don't pass
   each other prose or the raw diff — they pass typed, structured results.
   The Release Manager is the clearest expression of this: it only ever sees
   `ReviewResult` objects, never the git diff itself.

3. **Transparency and traceability.** Every recommendation should be
   traceable back to the specific findings that produced it. The final
   `ReleaseRecommendation` retains references to the reviewer outputs it was
   synthesized from.

4. **Deterministic orchestration around non-deterministic judgment.** The
   *pipeline* — which reviewers run, in what order, with what inputs — is
   deterministic and code-defined. The *judgments* those reviewers produce
   are AI-generated and can vary. Keeping this boundary clean is what makes
   the system debuggable.

5. **Composable and extensible.** Adding a sixth reviewer (e.g. a
   Performance Reviewer, or a Compliance Reviewer) should mean adding one
   new module and one line of pipeline registration — not restructuring the
   system.

## Non-goals

- **Not a CI/CD gate or a replacement for human sign-off.** This is a
  decision-support prototype, not an automated deployment gatekeeper.
- **Not a general-purpose linter or static analysis tool.** Reviewers reason
  over the diff and PR description at a judgment level, not a syntax level.
- **Not a code generation demo.** The interesting engineering here is
  agent decomposition, contracts, and coordination — not producing code.
- **Not (yet) a multi-turn conversational reviewer.** Each reviewer renders
  one judgment per submission; iterative back-and-forth with a reviewer is
  out of scope for the prototype.

## Users / personas

- **The submitter** — an engineer who wants a fast, structured second
  opinion on a change before requesting human review.
- **The interviewer/evaluator** (for this prototype specifically) — someone
  assessing the quality of the AI orchestration design: how responsibilities
  are decomposed, how agents communicate, and how failures are handled.

## Success criteria for this prototype

- The five reviewer responsibilities are cleanly separated in both prompt
  design and code structure — no reviewer's implementation needs to know
  another reviewer's internals.
- The Release Manager's inability to access the raw diff is enforced by the
  code's structure (function signatures/types), not only by instruction.
- The pipeline's orchestration logic (fan-out, fan-in, error handling) is
  readable and explainable independent of any specific prompt wording.
- The Streamlit UI clearly surfaces each reviewer's individual verdict
  alongside the Release Manager's final synthesis, so the "board" metaphor
  is visible to the end user.

## Roadmap (incremental build plan)

- [x] **Phase 0 — Project scaffold** *(this increment)*: folder structure,
      placeholder modules, docs, dependencies.
- [ ] **Phase 1 — Data contracts**: implement `SubmissionInput`,
      `ReviewResult`, `ReleaseRecommendation` as validated models.
- [ ] **Phase 2 — Prompt templates**: author the persona prompts for all
      five reviewers.
- [ ] **Phase 3 — First reviewer, end-to-end**: wire one reviewer
      (e.g. Architecture) to the Cursor SDK and confirm the full
      input → agent → structured output path works.
- [ ] **Phase 4 — Full orchestration pipeline**: implement fan-out across
      all four diff reviewers and fan-in to the Release Manager.
- [ ] **Phase 5 — Streamlit UI**: input collection, live progress, and
      results rendering.
- [ ] **Phase 6 — Resilience and polish**: partial-failure handling, tests,
      error surfacing, and UX refinement.
