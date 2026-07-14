from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


EligibilityErrorCode = Literal[
    "member_not_found",
    "payer_error",
    "timeout",
    "configuration_error",
]


class EligibilityErrorResponse(BaseModel):
    code: EligibilityErrorCode
    message: str


class EligibilityServiceError(Exception):
    def __init__(
        self,
        code: EligibilityErrorCode,
        message: str,
        *,
        status_code: int,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code

    def to_response(self) -> EligibilityErrorResponse:
        return EligibilityErrorResponse(code=self.code, message=self.message)


def member_not_found_error() -> EligibilityServiceError:
    return EligibilityServiceError(
        "member_not_found",
        "We could not find that member with the insurance details provided.",
        status_code=404,
    )


def payer_error() -> EligibilityServiceError:
    return EligibilityServiceError(
        "payer_error",
        (
            "The insurance eligibility system could not complete the check "
            "right now. Please try again later."
        ),
        status_code=502,
    )


def timeout_error() -> EligibilityServiceError:
    return EligibilityServiceError(
        "timeout",
        (
            "The insurance eligibility system took too long to respond. "
            "Please try again in a few minutes."
        ),
        status_code=504,
    )


def configuration_error() -> EligibilityServiceError:
    return EligibilityServiceError(
        "configuration_error",
        "Eligibility checks are not available right now. Please try again later.",
        status_code=503,
    )
