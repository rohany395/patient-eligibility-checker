#!/usr/bin/env python3
"""Capture REAL Stedi sandbox eligibility responses as test fixtures.

Sends each documented mock patient to the Stedi sandbox using your TEST api key
and saves the raw JSON response to tests/fixtures/<name>.json.

These are the only source of truth for the normalizer's tests. Never hand-write
a fixture — if the sandbox can't produce a response, there is no fixture for it.

Usage:
    export STEDI_API_KEY=your_test_key   # a *test* key, not production
    python scripts/capture_fixtures.py

Requires only the Python standard library (no extra installs).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

STEDI_URL = (
    "https://healthcare.us.stedi.com/2024-04-01/change/"
    "medicalnetwork/eligibility/v3"
)

# Provider org name + NPI can be anything that passes NPI check-digit validation.
# 1999999984 is the dummy NPI Stedi's own docs use.
PROVIDER = {"organizationName": "Provider Name", "npi": "1999999984"}

# Documented mock patients. Values are EXACT — do not edit them, or the sandbox
# will not match them to a canned response. Service type 30 is the only type the
# sandbox mocks for active coverage.
PATIENTS = [
    {
        "fixture": "active_aetna",
        "tradingPartnerServiceId": "60054",
        "subscriber": {
            "firstName": "Jane", "lastName": "Doe",
            "dateOfBirth": "20040404", "memberId": "AETNA12345",
        },
    },
    {
        "fixture": "active_uhc",
        "tradingPartnerServiceId": "87726",
        "subscriber": {
            "firstName": "Jane", "lastName": "Doe",
            "dateOfBirth": "19710101", "memberId": "UHC123456",
        },
    },
    {
        "fixture": "inactive_uhc",
        "tradingPartnerServiceId": "87726",
        "subscriber": {
            "firstName": "Jane", "lastName": "Doe",
            "dateOfBirth": "19710101", "memberId": "UHCINACTIVE",
        },
    },
    {
        "fixture": "member_not_found_aaa75",
        "tradingPartnerServiceId": "87726",
        "subscriber": {
            "firstName": "Jane", "lastName": "Doe",
            "dateOfBirth": "19900101", "memberId": "UHCAAA75",
        },
    },
    {
        "fixture": "payer_unavailable_aaa42",
        "tradingPartnerServiceId": "87726",
        "subscriber": {
            "firstName": "Jane", "lastName": "Doe",
            "dateOfBirth": "20010101", "memberId": "UHCAAA42",
        },
    },
]


def build_payload(patient: dict) -> dict:
    return {
        "tradingPartnerServiceId": patient["tradingPartnerServiceId"],
        "provider": PROVIDER,
        "subscriber": patient["subscriber"],
        "encounter": {"serviceTypeCodes": ["30"]},
    }


def post_eligibility(payload: dict, api_key: str) -> tuple[int, object]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        STEDI_URL,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Key {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = response.status
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        # AAA errors usually come back as 200, but capture any HTTP error body too.
        status = exc.code
        body = exc.read().decode("utf-8")
    try:
        return status, json.loads(body)
    except ValueError:
        return status, body


def main() -> int:
    api_key = os.environ.get("STEDI_API_KEY")
    if not api_key:
        print("ERROR: set STEDI_API_KEY (a *test* key) before running.", file=sys.stderr)
        return 1

    repo_root = Path(__file__).resolve().parents[1]
    fixtures_dir = repo_root / "tests" / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    exit_code = 0
    for patient in PATIENTS:
        name = patient["fixture"]
        status, parsed = post_eligibility(build_payload(patient), api_key)
        out_path = fixtures_dir / f"{name}.json"

        if isinstance(parsed, dict):
            out_path.write_text(json.dumps(parsed, indent=2) + "\n")
            # A tiny, non-PHI summary so you can eyeball what came back.
            hint = parsed.get("status") or (
                "AAA error" if "AAA" in json.dumps(parsed) else "ok"
            )
            print(f"  [{status}] {name:28s} -> {out_path.relative_to(repo_root)}  ({hint})")
        else:
            # Non-JSON body: save it so you can see what went wrong, and flag it.
            out_path.with_suffix(".txt").write_text(str(parsed))
            print(f"  [{status}] {name:28s} -> NON-JSON response, saved .txt (investigate)")
            exit_code = 1

    print("\nDone. Review the files in tests/fixtures/ before writing tests against them.")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())