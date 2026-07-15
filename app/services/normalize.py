from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Literal

from pydantic import BaseModel

from app.services.errors import member_not_found_error


BenefitStatus = Literal["active", "inactive", "member_not_found", "unknown"]
MENTAL_HEALTH_SERVICE_TYPE_CODES = {"A6", "MH"}
MENTAL_HEALTH_SERVICE_TERMS = ("mental", "behavioral", "psychotherapy")


class MentalHealthBenefit(BaseModel):
    service_type_code: str
    status: BenefitStatus
    copay: Decimal | None
    coinsurance: Decimal | None
    deductible: Decimal | None
    in_network: bool | None
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
    benefits_information = raw_response.get("benefitsInformation")
    if isinstance(benefits_information, list):
        return _normalize_json_benefits(raw_response, benefits_information)

    x12 = raw_response.get("x12")
    if not isinstance(x12, str):
        status: BenefitStatus = "unknown"
        mental_health = MentalHealthBenefit(
            service_type_code="MH",
            status=status,
            copay=None,
            coinsurance=None,
            deductible=None,
            in_network=None,
            payer_name=None,
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

    copay: Decimal | None = None
    coinsurance: Decimal | None = None
    deductible: Decimal | None = None
    in_network: bool | None = None
    status: BenefitStatus = "unknown"
    payer_name: str | None = None
    mental_health_payer_name: str | None = None
    last_segment_was_mental_health_benefit = False

    for raw_segment in x12.split("~"):
        segment = raw_segment.strip()
        if not segment:
            continue

        parts = segment.split("*")
        tag = parts[0]

        if tag == "AAA":
            aaa_code = parts[3] if len(parts) > 3 else None
            if aaa_code == "75":
                status = "member_not_found"
                break
            continue

        if tag == "NM1" and len(parts) > 3:
            if parts[1] == "PR":
                payer_name = parts[3] or None
            elif parts[1] == "VN" and last_segment_was_mental_health_benefit:
                mental_health_payer_name = parts[3] or None
            continue

        if tag != "EB":
            continue

        service_codes = parts[3].split(":") if len(parts) > 3 and parts[3] else []
        benefit_description = parts[5].lower() if len(parts) > 5 else ""
        is_mental_health_benefit = bool(
            set(service_codes) & MENTAL_HEALTH_SERVICE_TYPE_CODES
        ) or any(
            term in benefit_description for term in MENTAL_HEALTH_SERVICE_TERMS
        )
        last_segment_was_mental_health_benefit = is_mental_health_benefit
        if not is_mental_health_benefit:
            continue

        benefit_code = parts[1] if len(parts) > 1 else ""
        monetary_amount = (
            Decimal(parts[7])
            if len(parts) > 7 and parts[7]
            else None
        )
        percent = (
            Decimal(parts[8])
            if len(parts) > 8 and parts[8]
            else None
        )
        network_code = parts[12] if len(parts) > 12 else None

        if benefit_code == "1":
            status = "active"
        elif benefit_code in {"6", "I"}:
            status = "inactive"
        elif benefit_code == "B":
            copay = monetary_amount
        elif benefit_code == "A":
            coinsurance = percent or monetary_amount
        elif benefit_code == "C":
            deductible = monetary_amount

        if network_code == "Y":
            in_network = True
        elif network_code == "N":
            in_network = False

    if status != "active":
        covered = False
    else:
        covered = True

    payer_for_mental_health = mental_health_payer_name or payer_name
    carve_out = (
        bool(mental_health_payer_name)
        and bool(payer_name)
        and mental_health_payer_name != payer_name
    )
    mental_health = MentalHealthBenefit(
        service_type_code="MH",
        status=status,
        copay=copay,
        coinsurance=coinsurance,
        deductible=deductible,
        in_network=in_network,
        payer_name=payer_for_mental_health,
        carve_out=carve_out,
    )
    return EligibilitySummary(
        covered=covered,
        copay=copay,
        coinsurance=coinsurance,
        deductible=deductible,
        in_network=in_network,
        mental_health=mental_health,
    )


def _normalize_json_benefits(
    raw_response: dict[str, Any],
    benefits_information: list[Any],
) -> EligibilitySummary:
    copay: Decimal | None = None
    coinsurance: Decimal | None = None
    deductible: Decimal | None = None
    in_network: bool | None = None
    status: BenefitStatus = "unknown"
    service_type_code = "A6"

    for benefit in benefits_information:
        if not isinstance(benefit, dict) or not _is_mental_health_json_benefit(benefit):
            continue

        service_codes = _string_list(benefit.get("serviceTypeCodes"))
        for service_code in service_codes:
            if service_code in MENTAL_HEALTH_SERVICE_TYPE_CODES:
                service_type_code = service_code
                break

        benefit_code = benefit.get("code")
        if benefit_code == "1":
            status = "active"
        elif benefit_code in {"6", "I"}:
            status = "inactive"
        elif benefit_code == "B":
            copay = _decimal_or_none(benefit.get("benefitAmount"))
        elif benefit_code == "A":
            coinsurance = _decimal_or_none(
                benefit.get("benefitPercent") or benefit.get("benefitAmount")
            )
        elif benefit_code == "C":
            deductible = _decimal_or_none(benefit.get("benefitAmount"))

        network_code = benefit.get("inPlanNetworkIndicatorCode")
        if network_code == "Y":
            in_network = True
        elif network_code == "N":
            in_network = False

    mental_health = MentalHealthBenefit(
        service_type_code=service_type_code,
        status=status,
        copay=copay,
        coinsurance=coinsurance,
        deductible=deductible,
        in_network=in_network,
        payer_name=_payer_name(raw_response),
        carve_out=False,
    )
    return EligibilitySummary(
        covered=status == "active",
        copay=copay,
        coinsurance=coinsurance,
        deductible=deductible,
        in_network=in_network,
        mental_health=mental_health,
    )


def _is_mental_health_json_benefit(benefit: dict[str, Any]) -> bool:
    service_codes = set(_string_list(benefit.get("serviceTypeCodes")))
    if service_codes & MENTAL_HEALTH_SERVICE_TYPE_CODES:
        return True

    searchable_values = [
        benefit.get("name"),
        benefit.get("planCoverage"),
        *_string_list(benefit.get("serviceTypes")),
    ]
    return any(
        term in value.lower()
        for value in searchable_values
        if isinstance(value, str)
        for term in MENTAL_HEALTH_SERVICE_TERMS
    )


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
