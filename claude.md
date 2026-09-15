# Jarvis — Project Rules for Claude

## Read First
- docs/MASTER_SPEC.md — full architecture
- docs/ROADMAP.md — current phase and next milestone

## Core Principles
- SQLite only (with sqlite-vec). No other DBs.
- No LangChain. LangGraph only from V2H onward.
- Tools are single files in backend/tools/, auto-discovered.
- Every tool handler takes user_id as first arg (SaaS-ready).
- Ship V1 fast. Don't over-engineer.

## Current Focus
Phase 1 — Voice loop (see docs/phases/1_voice_loop.md)

## Style
- Python: type hints, small functions, no classes unless needed.
- Tests for every tool.
- Commit after each working milestone.