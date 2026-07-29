from app.core.celery import celery_app


@celery_app.task(
    name="reca.health_ping",
    ignore_result=False,
    soft_time_limit=5,
    time_limit=10,
)
def health_ping() -> dict[str, str]:
    """Return a stable broker/worker probe result without touching user data."""
    return {"status": "ok", "service": "reca-worker"}
