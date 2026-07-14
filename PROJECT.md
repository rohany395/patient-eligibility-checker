# PROJECT.md — Build plan

A step-by-step build plan for the eligibility app. Work ONE task at a time, in order.
For each task: plan it first, get the plan approved, implement, verify with the stated
check, then commit before moving on. Keep tasks small — if a task feels big, split it.

## Reference
- Stedi healthcare / eligibility docs — read the real-time eligibility section BEFORE
  Task 2, and don't guess the request/response format. (Confirm the current URL at
  https://www.stedi.com/docs.)
- The sandbox uses fixed mock patients and mock payers (Aetna, Cigna, UnitedHealthcare, CMS).
- Sign-up is free. Put the sandbox key in a local `.env` as `STEDI_API_KEY` (never commit it).

## How to work each task
1. **Plan** — describe the change and the files it touches. No code yet. Review it.
2. **Implement** — apply the approved plan.
3. **Verify** — run the check listed under the task.
4. **Commit** — one commit per task, with a clear message. Then start the next task.

## Tasks

### 1. Scaffold  ☐
Set up a FastAPI backend (`app/`) and a Vite + React + TypeScript frontend (`frontend/`)
in this repo, plus a `GET /health` endpoint that returns `{"status": "ok"}`.
**Verify:** backend and frontend both start; hitting /health returns ok.

### 2. Stedi client  ☐
In `app/services/stedi.py`, add a function that runs a real-time eligibility check for
one sandbox mock patient and returns the raw JSON response. Read the key from
`STEDI_API_KEY`. Request mental-health coverage specifically.
**Verify:** one real call to the sandbox returns a response you can print.

### 3. Normalizer + tests  ☐
In `app/services/normalize.py`, turn Stedi's raw response into a clean typed model:
covered (yes/no), copay, coinsurance, deductible, in-network, and the mental-health
benefit specifically. Save real sample responses into `tests/fixtures/` and write tests
for: active, inactive, member-not-found, and a behavioral-health carve-out.
**Verify:** `pytest -q` passes. (This is the core correctness step — don't rush it.)

### 4. Error handling  ☐
Handle the failure cases — member not found, payer / system error, timeout — and map
each to a plain, user-safe message. No raw EDI or stack traces reach the patient.
**Verify:** tests for each failure case pass; the API returns clean messages, not 500s.

### 5. API endpoint  ☐
Add `POST /eligibility` that takes the patient / insurer input, calls the client, runs
the normalizer, and returns the typed result. Handle bad input with a clear 400.
**Verify:** calling the endpoint (curl or the /docs UI) returns a clean result for a
known mock patient and a clean error for a bad request.

### 6. Frontend  ☐
Build the input form (member ID, date of birth, insurer) and a result screen that shows
the plain-English answer ("Covered — $25 per session, in-network"). Show a friendly
message on the failure cases from Task 4.
**Verify:** end to end in the browser — enter a mock patient, see the coverage answer.

## Scope discipline (do NOT do these)
- No A/B testing framework, no analytics platform, no auth / login system.
- No database unless a task above needs one (it doesn't — this is a stateless lookup).
- Don't make the UI fancy before the backend is correct. Backend first, polish last.

## Stretch (only after all six are done)
- Add a small "ops / debug" view showing the raw request/response and the call latency.
- Add lightweight event logging (step reached, result shown) so you can talk about
  onboarding conversion in an interview — without building a real analytics system.
