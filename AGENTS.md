# AGENTS.md — Eligibility & Cost-Clarity app

Instructions for any AI coding agent working in this repo (Codex, Cursor, etc.).
Keep this file short. Only put things here that an agent can't infer from the code.

## What this project is
A web app for behavioral-health patient onboarding: a person enters their insurance
details, the app checks their coverage in real time through the Stedi eligibility
sandbox, and shows a plain answer — covered or not, copay, in-network — for mental
health care specifically. Sandbox mock patients only; no real patient data, ever.

## Commands
- Install:       `pip install -r requirements.txt` then `cd frontend && npm install`
- Run backend:   `uvicorn app.main:app --reload`   (http://localhost:8000)
- Run frontend:  `cd frontend && npm run dev`       (http://localhost:5173)
- Test (run before calling any task done):  `pytest -q`
- Format:        `ruff format . && ruff check --fix .`

## Architecture (follow these — they are not obvious from the code)
- Backend: Python 3.12 + FastAPI, `httpx` for outbound HTTP. Frontend: React + Vite + TypeScript.
- Every call to Stedi goes through `app/services/stedi.py`. Route handlers never call Stedi directly.
- Converting Stedi's response into our own shape happens ONLY in `app/services/normalize.py`.
- API endpoints return typed Pydantic models, never raw dicts.
- The Stedi API key is read from the `STEDI_API_KEY` environment variable. Never hardcode or commit it.

## Testing
- Every function in `normalize.py` has a test in `tests/` that reads a saved sample
  response from `tests/fixtures/` (don't hit the live sandbox inside unit tests).
- Cover these cases: active coverage, inactive / not covered, member not found, and a
  behavioral-health carve-out (a different payer for mental health than for medical).
- `pytest -q` must pass before any task is considered finished.

## Hard constraints
- NEVER log, print, or store member IDs, names, or dates of birth.
- When checking coverage, ask Stedi for mental-health coverage specifically (service
  type MH), not just a general coverage check.
- Do not add a new production dependency without flagging it in your summary first.
- Turn insurer errors into plain, user-safe messages. Never surface raw EDI or stack
  traces to the patient view.
