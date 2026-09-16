# Phase 1 — Voice loop

Goal: "Hey Aria, what's the weather?" → spoken answer < 2s. No tools, no memory, no mobile.

Pipeline: mic → openWakeWord → OpenAI Realtime (server VAD + STT + LLM + TTS) → speaker.
Electron/browser is display-only over one WebSocket. Details: MASTER_SPEC §7(a), §10, §13.

Done = M3 + M4 + M6 + M7 acceptance all green. Commit after every milestone.
