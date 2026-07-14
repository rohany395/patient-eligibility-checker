import asyncio
import json

import httpx
import pytest

from app.services.errors import EligibilityServiceError
from app.services.stedi import (
    SANDBOX_MENTAL_HEALTH_REQUEST,
    STEDI_ELIGIBILITY_URL,
    run_sandbox_eligibility_check,
)


def test_run_sandbox_eligibility_check_sends_documented_mh_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("STEDI_API_KEY", "test_key")
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers["Authorization"]
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"id": "response_id", "status": "ok"})

    transport = httpx.MockTransport(handler)

    async def run_check() -> dict[str, object]:
        async with httpx.AsyncClient(transport=transport) as client:
            return await run_sandbox_eligibility_check(client=client)

    response = asyncio.run(run_check())

    assert response == {"id": "response_id", "status": "ok"}
    assert captured["url"] == STEDI_ELIGIBILITY_URL
    assert captured["authorization"] == "Key test_key"
    assert captured["body"] == SANDBOX_MENTAL_HEALTH_REQUEST
    assert (
        SANDBOX_MENTAL_HEALTH_REQUEST["encounter"]["serviceTypeCodes"]
        == ["MH"]
    )


def test_run_sandbox_eligibility_check_requires_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("STEDI_API_KEY", raising=False)

    with pytest.raises(EligibilityServiceError) as exc_info:
        asyncio.run(run_sandbox_eligibility_check())

    assert exc_info.value.code == "configuration_error"
    assert exc_info.value.status_code == 503


def test_run_sandbox_eligibility_check_maps_timeout_to_user_safe_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("STEDI_API_KEY", "test_key")

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("raw timeout details", request=request)

    transport = httpx.MockTransport(handler)

    async def run_check() -> None:
        async with httpx.AsyncClient(transport=transport) as client:
            await run_sandbox_eligibility_check(client=client)

    with pytest.raises(EligibilityServiceError) as exc_info:
        asyncio.run(run_check())

    error = exc_info.value
    assert error.code == "timeout"
    assert error.status_code == 504
    assert "raw timeout details" not in error.message


def test_run_sandbox_eligibility_check_maps_payer_error_to_user_safe_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("STEDI_API_KEY", "test_key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            500,
            request=request,
            text="raw payer error with EDI details",
        )

    transport = httpx.MockTransport(handler)

    async def run_check() -> None:
        async with httpx.AsyncClient(transport=transport) as client:
            await run_sandbox_eligibility_check(client=client)

    with pytest.raises(EligibilityServiceError) as exc_info:
        asyncio.run(run_check())

    error = exc_info.value
    assert error.code == "payer_error"
    assert error.status_code == 502
    assert "raw payer error" not in error.message
    assert "EDI" not in error.message


def test_run_sandbox_eligibility_check_maps_malformed_json_to_user_safe_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("STEDI_API_KEY", "test_key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, text="not json")

    transport = httpx.MockTransport(handler)

    async def run_check() -> None:
        async with httpx.AsyncClient(transport=transport) as client:
            await run_sandbox_eligibility_check(client=client)

    with pytest.raises(EligibilityServiceError) as exc_info:
        asyncio.run(run_check())

    assert exc_info.value.code == "payer_error"
    assert exc_info.value.status_code == 502
