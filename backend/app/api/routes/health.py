from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.adapters.health import HealthService
from app.api.schemas.health import (
    DependenciesHealthResponse,
    DependencyStatus,
    ErrorResponse,
    LiveHealthResponse,
    ReadyHealthResponse,
)

router = APIRouter(prefix="/health", tags=["health"])
health_service = HealthService()


@router.get("/live", response_model=LiveHealthResponse, responses={500: {"model": ErrorResponse}})
async def live_health() -> LiveHealthResponse:
    """Process-only liveness endpoint; intentionally performs no dependency probe."""
    return LiveHealthResponse()


@router.get(
    "/ready",
    response_model=ReadyHealthResponse,
    responses={500: {"model": ErrorResponse}, 503: {"model": ReadyHealthResponse}},
)
async def ready_health() -> ReadyHealthResponse | JSONResponse:
    dependencies = await health_service.core_dependencies()
    status = (
        DependencyStatus.HEALTHY
        if all(item.status == DependencyStatus.HEALTHY for item in dependencies)
        else DependencyStatus.UNAVAILABLE
    )
    response = ReadyHealthResponse(status=status, dependencies=dependencies)
    if status == DependencyStatus.HEALTHY:
        return response
    return JSONResponse(status_code=503, content=response.model_dump(mode="json"))


@router.get(
    "/dependencies",
    response_model=DependenciesHealthResponse,
    responses={500: {"model": ErrorResponse}},
)
async def dependencies_health() -> DependenciesHealthResponse:
    return DependenciesHealthResponse(dependencies=await health_service.all_dependencies())
