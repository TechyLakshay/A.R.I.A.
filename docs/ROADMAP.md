# Roadmap

Current phase: **V1 — Proof of Life** (MASTER_SPEC §13). Full V2 plan: MASTER_SPEC §14.

## V1 milestones

- [x] **M1 — Skeleton**: FastAPI boots, SQLite migrations, WS echo, shared-ui orb renders (acceptance: `/health` 200, UI shows events)
- [ ] **M2 — Audio I/O**: mic 16kHz capture + speaker 24kHz playback (acceptance: record 5s, clean playback)
- [ ] **M3 — Wake word**: Porcupine "Jarvis" → wake events (acceptance: 10/10 wakes, 0 false in 10 min)
- [ ] **M4 — Realtime loop**: wake → OpenAI Realtime → spoken answer < 2s, 5-turn follow-up
- [ ] **M5 — UI transcript**: live transcript + states in Electron (or browser tab)
- [ ] **M6 — Persistence**: sessions/turns/costs rows per session
- [ ] **M7 — Soak + tune**: < 1 false wake/hr, 20 commands no crash
- [ ] **M8 — Polish**: README, error path on Realtime disconnect

Keys needed: `PICOVOICE_ACCESS_KEY` (M3), `OPENAI_API_KEY` (M4).
