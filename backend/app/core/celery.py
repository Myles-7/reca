"""The single Celery application used by RECA workers.

Importing this module configures Celery only; it does not contact Valkey or
enqueue a task. The worker process is the only M0 component that imports it by
default.
"""

from celery import Celery  # type: ignore[import-untyped]

from app.core.config import settings

if not settings.CELERY_BROKER_URL:
    raise RuntimeError("CELERY_BROKER_URL is required to start the RECA worker")

celery_app = Celery(
    "reca",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.health", "app.workers.jobs"],
)

celery_app.conf.update(
    accept_content=["json"],
    task_serializer="json",
    result_serializer="json",
    enable_utc=True,
    timezone="UTC",
    task_track_started=False,
    task_time_limit=10,
    task_soft_time_limit=5,
    task_acks_late=False,
    worker_prefetch_multiplier=1,
    result_expires=300,
)
