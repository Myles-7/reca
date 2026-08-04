import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from app.api.errors import ContractError, ContractErrorDetail, ContractErrorResponse
from app.api.main import api_router
from app.api.schemas.health import ErrorDetail, ErrorResponse
from app.core.config import settings
from app.core.observability import (
    REQUEST_ID_HEADER,
    RequestObservabilityMiddleware,
    configure_logging,
    current_request_id,
)


def custom_generate_unique_id(route: APIRoute) -> str:
    tag = route.tags[0] if route.tags else "default"
    method = sorted(route.methods)[0].lower() if route.methods else "request"
    path = (
        route.path_format.strip("/").replace("/", "_").replace("{", "").replace("}", "")
    )
    return f"{tag}_{route.name}_{method}_{path or 'root'}"


def error_response(
    status_code: int, code: str, message: str, request: Request | None = None
) -> JSONResponse:
    request_id = (
        getattr(request.state, "request_id", current_request_id())
        if request is not None
        else current_request_id()
    )
    payload = ErrorResponse(
        error=ErrorDetail(code=code, message=message), request_id=request_id
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(),
        headers={REQUEST_ID_HEADER: request_id},
    )


def is_m1_contract_path(request: Request) -> bool:
    path = request.url.path
    prefixes = (
        f"{settings.API_V1_STR}/projects",
        f"{settings.API_V1_STR}/artifacts",
        f"{settings.API_V1_STR}/artifact-uploads",
        f"{settings.API_V1_STR}/jobs",
        f"{settings.API_V1_STR}/approvals",
        f"{settings.API_V1_STR}/research-questions",
        f"{settings.API_V1_STR}/research-question-versions",
        f"{settings.API_V1_STR}/query-plans",
        f"{settings.API_V1_STR}/literature-search-runs",
        f"{settings.API_V1_STR}/literature",
        f"{settings.API_V1_STR}/documents",
        f"{settings.API_V1_STR}/literature-extractions",
        f"{settings.API_V1_STR}/literature-extraction-fields",
        f"{settings.API_V1_STR}/evidence-spans",
        f"{settings.API_V1_STR}/evidence-set-summaries",
        f"{settings.API_V1_STR}/dataset-versions",
        f"{settings.API_V1_STR}/data-quality-runs",
        f"{settings.API_V1_STR}/data-quality-issues",
    )
    return any(path == prefix or path.startswith(f"{prefix}/") for prefix in prefixes)


def contract_error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    request: Request,
    details: dict[str, object] | None = None,
    field_errors: list[dict[str, object]] | None = None,
    retryable: bool = False,
    suggested_action: str | None = None,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", current_request_id())
    payload = ContractErrorResponse(
        error=ContractErrorDetail(
            code=code,
            message=message,
            details=details or {},
            field_errors=field_errors or [],
            request_id=request_id,
            retryable=retryable,
            suggested_action=suggested_action,
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(exclude_none=True),
        headers={REQUEST_ID_HEADER: request_id},
    )


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)
configure_logging()
app.add_middleware(RequestObservabilityMiddleware)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    _request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    if is_m1_contract_path(_request):
        code = {
            401: "AUTH_REQUIRED",
            403: "TOKEN_INVALID"
            if exc.detail == "Could not validate credentials"
            else "PERMISSION_DENIED",
            404: "RESOURCE_NOT_FOUND",
        }.get(exc.status_code, "VALIDATION_ERROR")
        return contract_error_response(
            status_code=exc.status_code,
            code=code,
            message="Request could not be completed.",
            request=_request,
        )
    messages = {
        404: ("not_found", "Resource not found"),
        405: ("method_not_allowed", "Method not allowed"),
        503: ("service_unavailable", "Service unavailable"),
    }
    code, message = messages.get(exc.status_code, ("http_error", "Request failed"))
    return error_response(exc.status_code, code, message, _request)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, _error: RequestValidationError
) -> JSONResponse:
    if is_m1_contract_path(_request):
        field_errors = [
            {
                "field": ".".join(str(part) for part in error["loc"] if part != "body"),
                "code": error["type"],
                "message": error["msg"],
            }
            for error in _error.errors()
        ]
        return contract_error_response(
            status_code=422,
            code="VALIDATION_ERROR",
            message="Request validation failed.",
            request=_request,
            field_errors=field_errors,
        )
    return error_response(
        422, "validation_error", "Request validation failed", _request
    )


@app.exception_handler(ContractError)
async def contract_exception_handler(
    request: Request, error: ContractError
) -> JSONResponse:
    return contract_error_response(
        status_code=error.status_code,
        code=error.code,
        message=error.message,
        request=request,
        details=error.details,
        field_errors=error.field_errors,
        retryable=error.retryable,
        suggested_action=error.suggested_action,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    _request: Request, _error: Exception
) -> JSONResponse:
    return error_response(500, "internal_error", "Internal server error", _request)


# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
