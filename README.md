# Patient Eligibility Checker

A small web app for behavioral-health patient onboarding. A user enters insurance details, the backend checks eligibility through Stedi, and the UI shows a simple coverage answer for mental-health care.

This project is for Stedi sandbox/mock patients only. Do not enter real patient data.

## Architecture

- `frontend/`: React + Vite + TypeScript app. It renders the form and coverage result.
- `app/main.py`: FastAPI app with `GET /health` and `POST /eligibility`.
- `app/models.py`: Pydantic request/error models.
- `app/services/stedi.py`: the only place that calls Stedi. It posts to Stedi's JSON eligibility endpoint and reads `STEDI_API_KEY` from the environment or local `.env`.
- `app/services/normalize.py`: converts Stedi's response into the app's clean eligibility summary.
- `app/services/errors.py`: maps configuration, timeout, payer, and member-not-found failures to safe messages.
- `tests/`: backend tests and saved fixture responses.

## Request Flow

1. The frontend sends patient name, member ID, date of birth, and insurer to `POST /eligibility`.
2. FastAPI validates the request.
3. `stedi.py` builds the Stedi eligibility request and calls Stedi.
4. `normalize.py` extracts mental-health/psychotherapy coverage, copay, coinsurance, deductible, and network status.
5. The API returns a typed summary for the frontend to display.

## Stedi Notes

- Stedi calls use `https://healthcare.us.stedi.com/2024-04-01/change/medicalnetwork/eligibility/v3`.
- Test API keys only accept Stedi's documented mock requests.
- The mock-compatible request uses service type `30`; the normalizer reads mental-health benefits from Stedi response service types such as `A6` Psychotherapy and `MH`.
- Never commit `STEDI_API_KEY`.

## Run

Backend:

```bash
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm run dev
```

## Test

```bash
pytest -q
```

Frontend build:

```bash
cd frontend
npm run build
```
