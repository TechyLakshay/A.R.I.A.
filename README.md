# Jarvis

Voice-first personal assistant. Spec: [`docs/MASTER_SPEC.md`](docs/MASTER_SPEC.md) · UI: [`docs/UI_SPEC.md`](docs/UI_SPEC.md) · Roadmap: [`docs/ROADMAP.md`](docs/ROADMAP.md)

## Run (dev, two terminals)

```powershell
# 1 — backend (Python 3.12+)
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\uvicorn backend.main:app --host 127.0.0.1 --port 8741 --reload

# 2 — UI (Node 20+)
cd shared-ui
npm install
npm run dev
```

Open http://localhost:5173 — the orb connects over WebSocket and shows live events.

## Tests

```powershell
.venv\Scripts\pytest backend/tests -q
```
