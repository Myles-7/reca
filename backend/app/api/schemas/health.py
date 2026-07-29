from enum import StrEnum

from pydantic import BaseModel, Field


class DependencyStatus(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    UNCONFIGURED = "UNCONFIGURED"
    UNKNOWN = "UNKNOWN"


class DependencyCheck(BaseModel):
    name: str
    status: DependencyStatus
    detail: str = Field(description="Sanitized dependency status detail.")


class LiveHealthResponse(BaseModel):
    status: DependencyStatus = DependencyStatus.HEALTHY
    service: str = "api"


class ReadyHealthResponse(BaseModel):
    status: DependencyStatus
    dependencies: list[DependencyCheck]


class DependenciesHealthResponse(BaseModel):
    dependencies: list[DependencyCheck]


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
    request_id: str
