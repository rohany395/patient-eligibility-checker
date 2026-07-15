# PROJECT.md — Build plan

A step-by-step build plan for the eligibility app. Work ONE task at a time, in order.
For each task: plan it first, get the plan approved, implement, verify with the stated
check, then commit before moving on. Keep tasks small — if a task feels big, split it.

## Reference
- Stedi eligibility mock requests (the source of truth for test data):
  https://www.stedi.com/docs/healthcare/api-reference/mock-requests-eligibility-checks
- Sandbox rule: active-coverage mocks support service type `30` ONLY. There is no
  mental-health (MH) mock and no carve-out mock. Request `30`; keep service type a parameter.
- You MUST use the documented mock patients' exact values. Any other name / DOB / member
  ID returns an error. The ones this project uses (all real, from the docs above):

  | Case                     | Payer ID | Name       | DOB (YYYYMMDD) | Member ID   |
  |--------------------------|----------|------------|----------------|-------------|
  | Active                   | 60054    | Jane Doe   | 20040404       | AETNA12345  |
  | Active (alt)             | 87726    | Jane Doe   | 19710101       | UHC123456   |
  | Inactive / not covered   | 87726    | Jane Doe   | 19710101       | UHCINACTIVE |
  | Member not found (AAA 75)| 87726    | Jane Doe   | 19900101       | UHCAAA75    |
  | Payer unavailable (AAA 42)| 87726   | Jane Doe   | 20010101       | UHCAAA42    |

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
one documented sandbox mock patient and returns the raw JSON response. Read the key from
`STEDI_API_KEY`. Request service type `30` (the only type the sandbox mocks), but make
the service type a PARAMETER so production could request behavioral-health types. Use a
documented mock patient's EXACT values (e.g. Aetna, payer 60054, Jane Doe, DOB 2004-04-04,
member AETNA12345).
**Verify:** one real call to the sandbox returns a response you can print.

### 3. Capture fixtures, then normalizer + tests  ☐
FIRST run `python scripts/capture_fixtures.py` to save REAL sandbox responses into
`tests/fixtures/` (active, inactive, member-not-found, payer-unavailable). Then in
`app/services/normalize.py`, turn Stedi's response into a clean typed model: covered,
copay, coinsurance, deductible, in-network. Consume Stedi's parsed `benefits` JSON
(simplest) OR parse the raw `x12` string (more impressive) — but validate against the
CAPTURED fixtures either way. Write tests that read those captured fixtures.
Do NOT hand-write fixtures. Expect the first run to fail if the normalizer assumed
mental-health segments; fix it against what the real `30` responses actually contain.
**Verify:** `pytest -q` passes against the captured responses. (Core correctness step —
don't rush it.)

### 4. Error handling  ☐
Handle the failure cases — member not found (AAA 75), payer / system error (AAA 42),
timeout — and map each to a plain, user-safe message. No raw EDI or stack traces reach
the patient.
**Verify:** tests (using captured error fixtures) pass; the API returns clean messages, not 500s.

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
- No fabricated fixtures, ever. A fixture the sandbox can't produce is not a fixture.
- Don't make the UI fancy before the backend is correct. Backend first, polish last.

## README must state
- Built entirely against Stedi's sandbox on a test key — no real PHI is ever touched.
- The sandbox only mocks general medical coverage (service type 30); the service type is
  parameterized so a production deployment would request behavioral-health types.

## Stretch (only after all six are done)
- Add a small "ops / debug" view showing the raw request/response and the call latency.
- Add lightweight event logging (step reached, result shown) so you can talk about
  onboarding conversion in an interview — without building a real analytics system.