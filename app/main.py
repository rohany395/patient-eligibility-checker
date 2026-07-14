from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.errors import EligibilityServiceError


class HealthResponse(BaseModel):
    status: str


app = FastAPI(title="Patient Eligibility Checker")


def register_exception_handlers(fastapi_app: FastAPI) -> None:
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
