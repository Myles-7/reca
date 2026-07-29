import pytest

from app.core.celery import celery_app
from app.workers.health import health_ping

pytestmark = pytest.mark.no_database


def test_health_ping_is_stable_and_has_no_business_side_effects() -> None:
    assert health_ping.run() == {"status": "ok", "service": "reca-worker"}


def test_celery_uses_utc_and_safe_task_defaults() -> None:
    assert celery_app.conf.enable_utc is True
    assert celery_app.conf.timezone == "UTC"
    assert celery_app.conf.task_time_limit == 10
    assert celery_app.conf.task_soft_time_limit == 5
