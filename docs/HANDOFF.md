# A.R.I.A. — Handoff Notes

Read after `claude.md` and `docs/ROADMAP.md`. This file is the working state as of **2026-09-18**; delete it once everything below is verified.

## What this project is

Voice-first assistant: wake word → OpenAI Realtime (STT+LLM+TTS in one WebSocket) → spoken answer. Source of truth: `docs/MASTER_SPEC.md`. Public repo: `github.com/TechyLakshay/A.R.I.A.` (branch `main`).

## Status snapshot

| Milestone | State |
|---|---|
| M1 skeleton (FastAPI, SQLite, WS, UI) | ✅ done, committed |
| M2 audio I/O (mic 16k / speaker 24k) | ✅ done, committed, user-verified |
| M3 wake word (openWakeWord "hey_jarvis" → WS events) | ✅ done, committed, user-verified (3/3 wakes) |
| M4 Realtime voice loop | ⚠️ **code complete, live-tested working, 2 open issues — see below; uncommitted? no — committed with this handoff** |
| M5–M8 | ❌ not started |

## Setup on a new PC (first time)

Prereqs: Python 3.12+, Node 20+, git.

```powershell
git clone https://github.com/TechyLakshay/A.R.I.A..git
cd A.R.I.A
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy .env.example .env        # then edit: OPENAI_API_KEY=sk-...
cd shared-ui; npm install; cd ..
```

First backend start downloads openWakeWord models (~5 MB, needs internet once).

## Run (two terminals)

```powershell
# Terminal 1
.venv\Scripts\uvicorn backend.main:app --host 127.0.0.1 --port 8741
# Terminal 2
cd shared-ui; npm run dev
```

Open http://localhost:5173 → say "Hey Jarvis" (interim free model) → ask "What's the capital of Japan?" → spoken answer in ~1–2s → follow-up works → 60s silence → back to idle.

## M4 — open issues (verify on the new PC)

1. **Double voice (was reported, cause identified, fix = process hygiene):** two backend processes were alive at once (restarts orphaned the python child of a killed shell), each opening its own Realtime session → two voices. **Before starting the backend, always run:**
   ```powershell
   Get-NetTCPConnection -LocalPort 8741 -State Listen -ErrorAction SilentlyContinue |
     ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
   ```
   With exactly one backend, there is exactly one voice. If it still doubles with one process, investigate `voice_gateway.py` session lifecycle.
2. **Wrong-language replies (fix applied 2026-09-18, needs retest):** `PERSONA` in `backend/core/realtime.py` now explicitly pins English, and transcription config sends `"language": "en"`. Note: an earlier manual edit had turned PERSONA into a tuple (syntax bug) — fixed. If it still switches languages, raise `wake`/session logs and check what `session.update` sends.

## Architecture in one paragraph (what talks to what)

`backend/core/voice_gateway.py` owns ONE mic stream in a background thread: while `idle` it feeds the openWakeWord detector (`wake.py`); on wake it asks the event loop to open a `RealtimeSession` (`realtime.py`, async, GA API `wss://api.openai.com/v1/realtime?model=gpt-realtime`); while `listening` it streams mic PCM16 to the session; Realtime's server VAD detects end-of-turn; audio deltas stream back and play through `AudioPlayer` (`audio.py`, 24 kHz); mic is muted while `speaking` (no echo); 60s silence closes the session. UI (`shared-ui/`) is display-only over `/ws` (events: `state`, `transcript.final`, `assistant.transcript`, `wake`, `error`).

## Debug toolbox

- `ARIA_LOG_LEVEL=DEBUG` env → gateway prints wake-score + mic-RMS every 2s (proves mic capture vs detection separately)
- `python scripts/check_audio.py test` — 5s record + playback (M2 sanity)
- `python scripts/check_wake.py 20` — standalone wake detector with live scores
- Backend log lines to expect: `wake detected — opening session` … `session closed (follow-up window elapsed)`
- If Realtime errors mention "beta API": make sure no pre-GA code is running (GA migration was `OpenAI-Beta` header removal + GA session shape)

## What's next (in order)

1. **Confirm M4 on the new PC** (both issues above) → tick M4 in `docs/ROADMAP.md`
2. **M5 — transcript in Electron** (currently browser tab): transcript thread + cards per `docs/UI_SPEC.md`; keep Electron minimal (`desktop/main.js`, tray + window loading shared-ui build)
3. **M6 — persistence**: write `sessions`/`turns`/`costs` rows (schema already exists in `backend/migrations/001_v1.sql`; stamp `t_wake/t_eot/t_first_audio` for the latency budget)
4. **M7 — soak + tune**: false-wake threshold tuning, 20-command stability run
5. **M8 — polish**, then V2 per MASTER_SPEC §14 (2A memory → 2B tools → …)

Optional quick win anytime: train a custom **"hey aria"** model at openwakeword.com/train (~10 min, free), save the `.onnx` into the repo, set `ARIA_WAKE_MODEL=<path>` in `.env` — no code change needed.
