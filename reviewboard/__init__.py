"""
ReviewBoard AI
==============

Simulates an enterprise Engineering Review Board that evaluates software
changes before deployment by orchestrating multiple specialized AI reviewer
agents via the Cursor SDK.

Package layout:
    models/         Structured data contracts passed between pipeline stages.
    reviewers/      One module per specialized reviewer persona.
    orchestration/  Coordinates reviewers and prompt templates (fan-out/fan-in).
    ui/             Streamlit presentation layer (no orchestration logic).
"""
