from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


Insurer = Literal["aetna", "cigna", "unitedhealthcare", "cms"]


class EligibilityRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=35)
    last_name: str = Field(min_length=1, max_length=60)
    member_id: str = Field(min_length=1, max_length=64)
    date_of_birth: date
    insurer: Insurer


class BadRequestResponse(BaseModel):
    code: Literal["bad_request"]
    message: str
