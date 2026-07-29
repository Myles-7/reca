import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

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
    return error_response(
        422, "validation_error", "Request validation failed", _request
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
