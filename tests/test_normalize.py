import json
from decimal import Decimal
from pathlib import Path

from app.services.normalize import normalize_eligibility_response


FIXTURE_DIR = Path(__file__).parent / "fixtures"
CAPTURED_FIXTURES = {
    "active_aetna.json",
    "active_uhc.json",
    "inactive_uhc.json",
    "member_not_found_aaa75.json",
    "payer_unavailable_aaa42.json",
}


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_DIR / name).read_text())


def test_normalize_tests_use_only_captured_fixtures() -> None:
    assert CAPTURED_FIXTURES <= {path.name for path in FIXTURE_DIR.iterdir()}


def test_normalize_active_aetna_mental_health_benefits() -> None:
    result = normalize_eligibility_response(load_fixture("active_aetna.json"))

    assert result.covered is True
    assert result.copay == Decimal("30")
    assert result.coinsurance == Decimal("0")
    assert result.deductible == Decimal("500")
    assert result.in_network is True
    assert result.mental_health.service_type_code == "MH"
    assert result.mental_health.status == "active"
    assert result.mental_health.copay == Decimal("30")
    assert result.mental_health.coinsurance == Decimal("0")
    assert result.mental_health.deductible == Decimal("500")
    assert result.mental_health.out_of_network_copay is None
    assert result.mental_health.out_of_network_coinsurance == Decimal("0.5")
    assert result.mental_health.out_of_network_deductible is None
    assert result.mental_health.payer_name == "AETNA INC"
    assert result.mental_health.carve_out is False


def test_normalize_active_uhc_mental_health_coverage_without_costs() -> None:
    result = normalize_eligibility_response(load_fixture("active_uhc.json"))

    assert result.covered is True
    assert result.copay is None
    assert result.coinsurance is None
    assert result.deductible == Decimal("0")
    assert result.in_network is True
    assert result.mental_health.service_type_code == "MH"
    assert result.mental_health.status == "active"
    assert result.mental_health.deductible == Decimal("0")
    assert result.mental_health.payer_name == "UNITEDHEALTHCARE"


def test_normalize_inactive_uhc_without_mental_health_coverage() -> None:
    result = normalize_eligibility_response(load_fixture("inactive_uhc.json"))

    assert result.covered is False
    assert result.copay is None
    assert result.coinsurance is None
    assert result.deductible is None
    assert result.in_network is None
    assert result.mental_health.service_type_code == "MH"
    assert result.mental_health.status == "inactive"
    assert result.mental_health.payer_name == "UNITEDHEALTHCARE"


def test_normalize_member_not_found_aaa75() -> None:
    result = normalize_eligibility_response(load_fixture("member_not_found_aaa75.json"))

    assert result.covered is False
    assert result.mental_health.status == "member_not_found"
    assert result.mental_health.copay is None
    assert result.mental_health.coinsurance is None
    assert result.mental_health.deductible is None


def test_normalize_payer_unavailable_aaa42() -> None:
    result = normalize_eligibility_response(load_fixture("payer_unavailable_aaa42.json"))

    assert result.covered is False
    assert result.mental_health.status == "payer_unavailable"
    assert result.mental_health.copay is None
    assert result.mental_health.coinsurance is None
    assert result.mental_health.deductible is None
