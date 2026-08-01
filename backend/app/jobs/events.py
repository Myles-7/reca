from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from typing import Any, Protocol

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings

EVENT_HISTORY_LIMIT = 200
EVENT_HISTORY_TTL_SECONDS = 60 * 60


class EventStoreError(RuntimeError):
    pass


class JobEventStore(Protocol):
    def publish(
        self, *, job_id: uuid.UUID, event: dict[str, Any]
    ) -> dict[str, Any]: ...

    def after(
        self, *, job_id: uuid.UUID, last_event_id: int | None
    ) -> tuple[Sequence[dict[str, Any]], bool]: ...


class RedisJobEventStore:
    def __init__(self, url: str | None = None) -> None:
        connection_url = url or settings.VALKEY_URL
        if connection_url.startswith("valkey://"):
            connection_url = f"redis://{connection_url.removeprefix('valkey://')}"
        self.client: Any = Redis.from_url(
            connection_url,
            decode_responses=True,
            socket_connect_timeout=settings.CONNECT_TIMEOUT_SECONDS,
            socket_timeout=settings.REQUEST_TIMEOUT_SECONDS,
        )

    @staticmethod
    def _events_key(job_id: uuid.UUID) -> str:
        return f"reca:job:{job_id}:events"

    @staticmethod
    def _sequence_key(job_id: uuid.UUID) -> str:
        return f"reca:job:{job_id}:event-sequence"

    def publish(self, *, job_id: uuid.UUID, event: dict[str, Any]) -> dict[str, Any]:
        try:
            sequence_key = self._sequence_key(job_id)
            event_id = int(self.client.incr(sequence_key))
            stored = {**event, "event_id": event_id}
            events_key = self._events_key(job_id)
            pipeline = self.client.pipeline()
            pipeline.rpush(events_key, json.dumps(stored, separators=(",", ":")))
            pipeline.ltrim(events_key, -EVENT_HISTORY_LIMIT, -1)
            pipeline.expire(events_key, EVENT_HISTORY_TTL_SECONDS)
            pipeline.expire(sequence_key, EVENT_HISTORY_TTL_SECONDS)
            pipeline.execute()
            return stored
        except (RedisError, TypeError, ValueError) as error:
            raise EventStoreError("Valkey could not persist the Job event") from error

    def after(
        self, *, job_id: uuid.UUID, last_event_id: int | None
    ) -> tuple[Sequence[dict[str, Any]], bool]:
        try:
            values = self.client.lrange(self._events_key(job_id), 0, -1)
            events = [json.loads(value) for value in values]
        except (RedisError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise EventStoreError("Valkey could not read Job event history") from error
        if last_event_id is None:
            return events, False
        if not events:
            return (), True
        first_id = int(events[0]["event_id"])
        latest_id = int(events[-1]["event_id"])
        if last_event_id < first_id - 1 or last_event_id > latest_id:
            return (), True
        return [
            event for event in events if int(event["event_id"]) > last_event_id
        ], False


event_store: JobEventStore = RedisJobEventStore()
