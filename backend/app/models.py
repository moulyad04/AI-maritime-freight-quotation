from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class SignupRequest(BaseModel):
    username: str
    password: str = Field(min_length=6)

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Username cannot be empty")
        return v.strip()


class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator("username", "password")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("This field cannot be empty")
        return v.strip()


class RouteRequest(BaseModel):
    origin: str
    destination: str
    cargo_type: str
    containers: int


class QuotationRequest(BaseModel):
    origin: str
    destination: str
    cargo_type: str
    containers: int = Field(gt=0)
    documents_ready: list[str] = Field(default_factory=list)


class DecisionRequest(BaseModel):
    status: Literal["accepted", "rejected"]


class QuotationUpdateRequest(BaseModel):
    recommended_route: Optional[str] = None
    containers: Optional[int] = None
    freight_per_container_usd: Optional[float] = None
    total_freight_usd: Optional[float] = None
    transit_time_days: Optional[int] = None