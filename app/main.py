from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.models import BadRequestResponse, EligibilityRequest
from app.services.errors import EligibilityServiceError
from app.services.normalize import (
    EligibilitySummary,
    normalize_eligibility_response,
    raise_for_eligibility_error,
)
from app.services.stedi import run_eligibility_check


class HealthResponse(BaseModel):
    status: str


app = FastAPI(title="Patient Eligibility Checker")


def register_exception_handlers(fastapi_app: FastAPI) -> None:
    @fastapi_app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request,
        _exc: RequestValidationError,
    ) -> JSONResponse:
        error = BadRequestResponse(
            code="bad_request",
            message="Please check the insurance details and try again.",
        )
        return JSONResponse(status_code=400, content=error.model_dump())

    @fastapi_app.exception_handler(EligibilityServiceError)
    async def eligibility_service_error_handler(
        _request,
        exc: EligibilityServiceError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_response().model_dump(),
        )


register_exception_handlers(app)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/eligibility", response_model=EligibilitySummary)
async def check_eligibility(request: EligibilityRequest) -> EligibilitySummary:
    raw_response = await run_eligibility_check(
        member_id=request.member_id,
        date_of_birth=request.date_of_birth,
        insurer=request.insurer,
    )
    summary = normalize_eligibility_response(raw_response)
    raise_for_eligibility_error(summary)
    return summary
