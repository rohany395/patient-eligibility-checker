import asyncio
import json

import httpx
import pytest

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

    with pytest.raises(RuntimeError, match="STEDI_API_KEY is not set"):
        asyncio.run(run_sandbox_eligibility_check())
