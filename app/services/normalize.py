from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Literal

from pydantic import BaseModel

from app.services.errors import member_not_found_error, payer_error


BenefitStatus = Literal[
    "active",
    "inactive",
    "member_not_found",
    "payer_unavailable",
    "unknown",
]
MENTAL_HEALTH_SERVICE_TYPE_CODE = "MH"


class MentalHealthBenefit(BaseModel):
    service_type_code: str
    status: BenefitStatus
    copay: Decimal | None
    coinsurance: Decimal | None
    deductible: Decimal | None
    in_network: bool | None
    out_of_network_copay: Decimal | None
    out_of_network_coinsurance: Decimal | None
    out_of_network_deductible: Decimal | None
    payer_name: str | None
    carve_out: bool


class EligibilitySummary(BaseModel):
    covered: bool
    copay: Decimal | None
    coinsurance: Decimal | None
    deductible: Decimal | None
    in_network: bool | None
    mental_health: MentalHealthBenefit


def normalize_eligibility_response(raw_response: dict[str, Any]) -> EligibilitySummary:
    aaa_codes = _top_level_aaa_codes(raw_response)
    if "75" in aaa_codes:
        return _empty_summary("member_not_found", raw_response)
    if "42" in aaa_codes:
        return _empty_summary("payer_unavailable", raw_response)

    benefits = _mental_health_benefits(raw_response)
    covered = any(benefit.get("code") == "1" for benefit in benefits)
    status: BenefitStatus
    if covered:
        status = "active"
    elif _has_inactive_coverage(raw_response):
        status = "inactive"
    else:
        status = "unknown"

    copay = _benefit_decimal(benefits, code="B", field="benefitAmount", network="Y")
    coinsurance = _benefit_decimal(
        benefits,
        code="A",
        field="benefitPercent",
        network="Y",
    )
    deductible = _benefit_decimal(
        benefits,
        code="C",
        field="benefitAmount",
        network="Y",
    )
    out_of_network_copay = _benefit_decimal(
        benefits,
        code="B",
        field="benefitAmount",
        network="N",
    )
    out_of_network_coinsurance = _benefit_decimal(
        benefits,
        code="A",
        field="benefitPercent",
        network="N",
    )
    out_of_network_deductible = _benefit_decimal(
        benefits,
        code="C",
        field="benefitAmount",
        network="N",
    )

    mental_health = MentalHealthBenefit(
        service_type_code=MENTAL_HEALTH_SERVICE_TYPE_CODE,
        status=status,
        copay=copay,
        coinsurance=coinsurance,
        deductible=deductible,
        in_network=True if covered else None,
        out_of_network_copay=out_of_network_copay,
        out_of_network_coinsurance=out_of_network_coinsurance,
        out_of_network_deductible=out_of_network_deductible,
        payer_name=_payer_name(raw_response),
        carve_out=False,
    )
    return EligibilitySummary(
        covered=covered,
        copay=copay,
        coinsurance=coinsurance,
        deductible=deductible,
        in_network=mental_health.in_network,
        mental_health=mental_health,
    )


def _empty_summary(
    status: BenefitStatus,
    raw_response: dict[str, Any],
) -> EligibilitySummary:
    mental_health = MentalHealthBenefit(
        service_type_code=MENTAL_HEALTH_SERVICE_TYPE_CODE,
        status=status,
        copay=None,
        coinsurance=None,
        deductible=None,
        in_network=None,
        out_of_network_copay=None,
        out_of_network_coinsurance=None,
        out_of_network_deductible=None,
        payer_name=_payer_name(raw_response),
        carve_out=False,
    )
    return EligibilitySummary(
        covered=False,
        copay=None,
        coinsurance=None,
        deductible=None,
        in_network=None,
        mental_health=mental_health,
    )


def _top_level_aaa_codes(raw_response: dict[str, Any]) -> set[str]:
    errors = raw_response.get("errors")
    if not isinstance(errors, list):
        return set()

    codes: set[str] = set()
    for error in errors:
        if not isinstance(error, dict):
            continue
        if error.get("field") == "AAA" and isinstance(error.get("code"), str):
            codes.add(error["code"])
    return codes


def _mental_health_benefits(raw_response: dict[str, Any]) -> list[dict[str, Any]]:
    benefits = raw_response.get("benefitsInformation")
    if not isinstance(benefits, list):
        return []

    mental_health_benefits: list[dict[str, Any]] = []
    for benefit in benefits:
        if not isinstance(benefit, dict):
            continue
        if MENTAL_HEALTH_SERVICE_TYPE_CODE in _string_list(
            benefit.get("serviceTypeCodes")
        ):
            mental_health_benefits.append(benefit)
    return mental_health_benefits


def _has_inactive_coverage(raw_response: dict[str, Any]) -> bool:
    benefits = raw_response.get("benefitsInformation")
    if not isinstance(benefits, list):
        return False
    return any(
        isinstance(benefit, dict) and benefit.get("code") == "6"
        for benefit in benefits
    )


def _benefit_decimal(
    benefits: list[dict[str, Any]],
    *,
    code: str,
    field: str,
    network: Literal["Y", "N"],
) -> Decimal | None:
    for benefit in benefits:
        if benefit.get("code") != code:
            continue
        if benefit.get("inPlanNetworkIndicatorCode") != network:
            continue
        value = _decimal_or_none(benefit.get(field))
        if value is not None:
            return value
    return None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _decimal_or_none(value: Any) -> Decimal | None:
    if not isinstance(value, str | int | float):
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def _payer_name(raw_response: dict[str, Any]) -> str | None:
    payer = raw_response.get("payer")
    if not isinstance(payer, dict):
        return None
    name = payer.get("name") or payer.get("payerName")
    return name if isinstance(name, str) else None


def raise_for_eligibility_error(summary: EligibilitySummary) -> None:
    if summary.mental_health.status == "member_not_found":
        raise member_not_found_error()
    if summary.mental_health.status == "payer_unavailable":
        raise payer_error()
