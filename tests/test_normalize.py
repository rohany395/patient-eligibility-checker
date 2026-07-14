import json
from decimal import Decimal
from pathlib import Path

from app.services.normalize import normalize_eligibility_response


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_DIR / name).read_text())


def test_normalize_eligibility_response_active_mental_health() -> None:
    result = normalize_eligibility_response(
        load_fixture("active_mental_health.json")
    )

    assert result.covered is True
    assert result.copay == Decimal("25")
    assert result.coinsurance == Decimal("0.2")
    assert result.deductible == Decimal("500")
    assert result.in_network is True
    assert result.mental_health.status == "active"
    assert result.mental_health.service_type_code == "MH"
    assert result.mental_health.payer_name == "Sandbox Health Plan"
    assert result.mental_health.carve_out is False


def test_normalize_eligibility_response_inactive_mental_health() -> None:
    result = normalize_eligibility_response(
        load_fixture("inactive_mental_health.json")
    )

    assert result.covered is False
    assert result.copay is None
    assert result.coinsurance is None
    assert result.deductible is None
    assert result.in_network is None
    assert result.mental_health.status == "inactive"


def test_normalize_eligibility_response_member_not_found() -> None:
    result = normalize_eligibility_response(load_fixture("member_not_found.json"))

    assert result.covered is False
    assert result.mental_health.status == "member_not_found"
    assert result.mental_health.copay is None
    assert result.mental_health.coinsurance is None
    assert result.mental_health.deductible is None


def test_normalize_eligibility_response_behavioral_health_carve_out() -> None:
    result = normalize_eligibility_response(
        load_fixture("behavioral_health_carve_out.json")
    )

    assert result.covered is True
    assert result.copay == Decimal("15")
    assert result.coinsurance == Decimal("0.1")
    assert result.deductible is None
    assert result.in_network is True
    assert result.mental_health.status == "active"
    assert result.mental_health.payer_name == "Sandbox Behavioral Health Plan"
    assert result.mental_health.carve_out is True
