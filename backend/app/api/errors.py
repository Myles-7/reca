from typing import Any

from pydantic import BaseModel, Field


class ContractError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
        field_errors: list[dict[str, Any]] | None = None,
        retryable: bool = False,
        suggested_action: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}
        self.field_errors = field_errors or []
        self.retryable = retryable
        self.suggested_action = suggested_action


class ContractErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    field_errors: list[dict[str, Any]] = Field(default_factory=list)
    request_id: str
    retryable: bool = False
    suggested_action: str | None = None


class ContractErrorResponse(BaseModel):
    error: ContractErrorDetail
