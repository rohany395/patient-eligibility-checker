# Patient Eligibility Checker

Real-time insurance eligibility and cost clarity for behavioral-health intake. A patient
enters their insurance details and immediately sees whether mental-health care is covered
and what an in-network therapy session will cost — backed by real eligibility checks
against the [Stedi](https://www.stedi.com) clearinghouse sandbox, not hard-coded values.

> **Sandbox / mock data only.** This project never sends or stores real patient data (PHI).

## Why

Cost uncertainty is one of the biggest reasons people abandon mental-health intake: they
can't tell whether their insurance covers therapy or what they'll pay, so they give up
before booking. This app removes that friction at the point of signup by answering one
question clearly — *is therapy covered, and what will a session cost?*

## What it does

1. The patient enters their member ID, date of birth, and insurer.
2. The backend runs a real-time eligibility check (X12 270/271) through Stedi.
3. The response is normalized into a plain summary: covered or not, in-network copay,
   coinsurance, and the plan deductible — focused on mental-health benefits.
4. The UI shows a calm, plain-language answer. Failures become human-readable messages,
   never raw errors.

## Architecture

- `frontend/` — React + Vite + TypeScript. Renders the form and the result screen.
- `app/main.py` — FastAPI: `GET /health`, `POST /eligibility`, centralized error
  handling, CORS locked to the Vite origin.
- `app/models.py` — typed Pydantic request/response models.
- `app/services/stedi.py` — the only place that calls Stedi. Posts to the JSON
  eligibility endpoint; reads `STEDI_API_KEY` from the environment.
- `app/services/normalize.py` — turns Stedi's parsed `benefitsInformation` into a typed
  `EligibilitySummary`.
- `app/services/errors.py` — maps configuration / timeout / payer / member-not-found
  failures to safe, user-facing messages.
- `tests/` — backend tests plus captured Stedi responses used as fixtures.
- `scripts/capture_fixtures.py` — regenerates the test fixtures from live sandbox calls.

## Real integration, no PHI

Eligibility checks run against Stedi's sandbox using a **test** API key, which only accepts
Stedi's documented mock patients (fabricated test records — e.g. "Jane Doe / AETNA12345").
The app therefore exercises a real 270/271 eligibility pipeline while never touching real
protected health information. A test key cannot reach live payers, so there is no path to
real patient data.

## Design decisions

Real benefit data is messier than "covered: yes/no," so a few choices are worth calling out:

- **Service type.** Stedi's sandbox mocks general medical coverage (service type `30`). Its
  responses include mental-health benefit lines tagged `MH` (see
  `tests/fixtures/active_aetna.json`), which the normalizer extracts. The requested service
  type is a parameter, so a production deployment can request behavioral-health service
  types directly where a payer supports them.
- **Which cost to report.** A single response can carry many copays and coinsurance rates
  across service types and network tiers. The app deliberately reports the cost of an
  **in-network outpatient mental-health office visit** — the relevant number for someone
  booking a therapy session — choosing the outpatient line over inpatient.
- **Deductible fallback.** Mental-health benefit lines often carry no deductible of their
  own, but the plan-level deductible still applies. When there is no `MH`-specific
  deductible, the app falls back to the plan-level (service type `30`) deductible rather
  than reporting "none," which would understate what the patient owes.
- **Errors vs. non-coverage.** A payer outage or timeout produces a "temporarily
  unavailable, try again" message, kept strictly distinct from a genuine "not covered"
  answer. Raw EDI and stack traces are never surfaced to the patient.

## Testing

Tests read captured Stedi responses saved under `tests/fixtures/` — **real sandbox
responses, never hand-written.** Regenerate them with:

```bash
export STEDI_API_KEY=your_test_key
python scripts/capture_fixtures.py
```

This keeps the normalizer's tests grounded in what the payer actually returns, covering the
active, inactive, member-not-found (AAA 75), and payer-unavailable (AAA 42) cases.

## Running locally

Prerequisites: Python 3.12+, Node 18+, and a free Stedi sandbox test key.

```bash
# backend
pip install -r requirements.txt
export STEDI_API_KEY=your_test_key      # or put it in a local .env (gitignored)
uvicorn app.main:app --reload           # http://localhost:8000

# frontend (separate terminal)
cd frontend
npm install
npm run dev                             # http://localhost:5173
```

Run the checks:

```bash
pytest -q
cd frontend && npm run build
```

## Scope and production notes

Deliberately narrow: one eligibility lookup, done well. No auth, database, or analytics
layer. A production version would add payer enrollment for live checks, caching and retries
around payer timeouts, request-level observability (latency, payer error rates), and
audit-grade handling for real PHI.