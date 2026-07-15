import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import register_exception_handlers
from app.services.errors import EligibilityServiceError, payer_error
from app.services.normalize import (
    normalize_eligibility_response,
    raise_for_eligibility_error,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_member_not_found_maps_to_user_safe_error() -> None:
    raw_response = json.loads(
        (FIXTURE_DIR / "member_not_found_aaa75.json").read_text()
    )
    summary = normalize_eligibility_response(raw_response)

    with pytest.raises(EligibilityServiceError) as exc_info:
        raise_for_eligibility_error(summary)

    error = exc_info.value
    assert error.code == "member_not_found"
    assert error.status_code == 404
    assert error.to_response().model_dump() == {
        "code": "member_not_found",
        "message": (
            "We could not find that member with the insurance details provided."
        ),
    }


def test_payer_unavailable_maps_to_user_safe_error() -> None:
    raw_response = json.loads(
        (FIXTURE_DIR / "payer_unavailable_aaa42.json").read_text()
    )
    summary = normalize_eligibility_response(raw_response)

    with pytest.raises(EligibilityServiceError) as exc_info:
        raise_for_eligibility_error(summary)

    error = exc_info.value
    assert error.code == "payer_error"
    assert error.status_code == 502
    assert error.to_response().model_dump() == {
        "code": "payer_error",
        "message": (
            "The insurance eligibility system could not complete the check "
            "right now. Please try again later."
        ),
    }


def test_active_result_does_not_raise_user_safe_error() -> None:
    raw_response = json.loads((FIXTURE_DIR / "active_aetna.json").read_text())
    summary = normalize_eligibility_response(raw_response)

    raise_for_eligibility_error(summary)


def test_api_exception_handler_returns_clean_error_response() -> None:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/test-error")
    def test_error() -> None:
        raise payer_error()

    response = TestClient(app).get("/test-error")

    assert response.status_code == 502
    assert response.json() == {
        "code": "payer_error",
        "message": (
            "The insurance eligibility system could not complete the check "
            "right now. Please try again later."
        ),
    }
