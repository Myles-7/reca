import pytest

from app.models import JobTaskType
from app.workers import jobs

pytestmark = pytest.mark.no_database


def test_agent_worker_handler_is_explicitly_registered() -> None:
    assert JobTaskType.AGENT_ORCHESTRATION in jobs._handlers
    assert jobs._handlers[JobTaskType.AGENT_ORCHESTRATION].__name__ == (
        "_execute_agent_orchestration"
    )
