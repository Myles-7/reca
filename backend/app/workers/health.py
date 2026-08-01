from app.core.celery import celery_app


def _health_ping() -> dict[str, str]:
    """Return a stable broker/worker probe result without touching user data."""
    return {"status": "ok", "service": "reca-worker"}


health_ping = celery_app.task(
    name="reca.health_ping",
    ignore_result=False,
    soft_time_limit=5,
    time_limit=10,
)(_health_ping)
