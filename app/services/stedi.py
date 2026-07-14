from __future__ import annotations

import os
from typing import Any

import httpx


STEDI_ELIGIBILITY_URL = (
    "https://healthcare.us.stedi.com/2024-04-01/change/"
    "medicalnetwork/eligibility/v3"
)

SANDBOX_MENTAL_HEALTH_REQUEST: dict[str, Any] = {
    "tradingPartnerServiceId": "ABDCE",
    "encounter": {
        "serviceTypeCodes": ["MH"],
    },
    "provider": {
        "organizationName": "ACME Health Services",
        "npi": "1999999984",
    },
    "subscriber": {
        "dateOfBirth": "19000101",
        "firstName": "Jane",
        "lastName": "Doe",
        "memberId": "1234567890",
    },
}


def _get_stedi_api_key() -> str:
    api_key = os.environ.get("STEDI_API_KEY")
    if not api_key:
        raise RuntimeError("STEDI_API_KEY is not set")
    return api_key


async def run_sandbox_eligibility_check(
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    api_key = _get_stedi_api_key()
    headers = {
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json",
    }

    if client is not None:
        response = await client.post(
            STEDI_ELIGIBILITY_URL,
            headers=headers,
            json=SANDBOX_MENTAL_HEALTH_REQUEST,
        )
    else:
        async with httpx.AsyncClient(timeout=30.0) as stedi_client:
            response = await stedi_client.post(
                STEDI_ELIGIBILITY_URL,
                headers=headers,
                json=SANDBOX_MENTAL_HEALTH_REQUEST,
            )

    response.raise_for_status()
    response_json = response.json()
    if not isinstance(response_json, dict):
        raise RuntimeError("Stedi returned a non-object JSON response")
    return response_json
