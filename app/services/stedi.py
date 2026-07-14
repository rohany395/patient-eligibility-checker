from __future__ import annotations

import os
from datetime import date
from typing import Any

import httpx

from app.models import Insurer
from app.services.errors import (
    configuration_error,
    payer_error,
    timeout_error,
)


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

TRADING_PARTNER_SERVICE_IDS: dict[Insurer, str] = {
    "aetna": "60054",
    "cigna": "62308",
    "unitedhealthcare": "87726",
    "cms": "CMS",
}


def _get_stedi_api_key() -> str:
    api_key = os.environ.get("STEDI_API_KEY")
    if not api_key:
        raise configuration_error()
    return api_key


async def run_sandbox_eligibility_check(
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    return await _post_eligibility_request(SANDBOX_MENTAL_HEALTH_REQUEST, client)


async def run_eligibility_check(
    *,
    member_id: str,
    date_of_birth: date,
    insurer: Insurer,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    payload = {
        "tradingPartnerServiceId": TRADING_PARTNER_SERVICE_IDS[insurer],
        "encounter": {
            "serviceTypeCodes": ["MH"],
        },
        "provider": {
            "organizationName": "ACME Health Services",
            "npi": "1999999984",
        },
        "subscriber": {
            "dateOfBirth": date_of_birth.strftime("%Y%m%d"),
            "memberId": member_id,
        },
    }
    return await _post_eligibility_request(payload, client)


async def _post_eligibility_request(
    payload: dict[str, Any],
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    api_key = _get_stedi_api_key()
    headers = {
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json",
    }

    try:
        if client is not None:
            response = await client.post(
                STEDI_ELIGIBILITY_URL,
                headers=headers,
                json=payload,
            )
        else:
            async with httpx.AsyncClient(timeout=30.0) as stedi_client:
                response = await stedi_client.post(
                    STEDI_ELIGIBILITY_URL,
                    headers=headers,
                    json=payload,
                )

        response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise timeout_error() from exc
    except (httpx.HTTPStatusError, httpx.RequestError) as exc:
        raise payer_error() from exc

    try:
        response_json = response.json()
    except ValueError as exc:
        raise payer_error() from exc

    if not isinstance(response_json, dict):
        raise payer_error()
    return response_json
