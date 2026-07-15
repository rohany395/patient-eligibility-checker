import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_DIR / name).read_text())


def test_eligibility_endpoint_returns_normalized_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_run_eligibility_check(**_kwargs) -> dict[str, object]:
        return load_fixture("active_mental_health.json")

    monkeypatch.setattr(
        "app.main.run_eligibility_check",
        fake_run_eligibility_check,
    )

    response = TestClient(app).post(
        "/eligibility",
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "member_id": "TESTMEMBER",
            "date_of_birth": "2000-01-01",
            "insurer": "unitedhealthcare",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "covered": True,
        "copay": "25",
        "coinsurance": "0.2",
        "deductible": "500",
        "in_network": True,
        "mental_health": {
            "service_type_code": "MH",
            "status": "active",
            "copay": "25",
            "coinsurance": "0.2",
            "deductible": "500",
            "in_network": True,
            "payer_name": "Sandbox Health Plan",
            "carve_out": False,
        },
    }


def test_eligibility_endpoint_returns_clean_400_for_bad_request() -> None:
    response = TestClient(app).post(
        "/eligibility",
        json={
            "first_name": "",
            "last_name": "",
            "member_id": "",
            "date_of_birth": "not-a-date",
            "insurer": "unknown",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": "bad_request",
        "message": "Please check the insurance details and try again.",
    }


def test_eligibility_endpoint_allows_vite_cors_preflight() -> None:
    response = TestClient(app).options(
        "/eligibility",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "http://127.0.0.1:5173"
    )


def test_eligibility_endpoint_returns_clean_error_for_member_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_run_eligibility_check(**_kwargs) -> dict[str, object]:
        return load_fixture("member_not_found.json")

    monkeypatch.setattr(
        "app.main.run_eligibility_check",
        fake_run_eligibility_check,
    )

    response = TestClient(app).post(
        "/eligibility",
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "member_id": "TESTMEMBER",
            "date_of_birth": "2000-01-01",
            "insurer": "unitedhealthcare",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "code": "member_not_found",
        "message": (
            "We could not find that member with the insurance details provided."
        ),
    }
