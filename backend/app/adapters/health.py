from __future__ import annotations

import asyncio
from urllib.parse import urlparse

import httpx
from sqlalchemy import text

from app.api.schemas.health import DependencyCheck, DependencyStatus
from app.core.config import settings
from app.core.db import engine


class HealthProbe:
    """Small, bounded infrastructure probes with sanitized results."""

    @property
    def timeout_seconds(self) -> float:
        return min(settings.CONNECT_TIMEOUT_SECONDS, 5.0)

    async def postgres(self) -> DependencyCheck:
        return await self._database_probe("postgres", "SELECT 1")

    async def pgvector(self) -> DependencyCheck:
        return await self._database_probe(
            "pgvector", "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
        )

    async def _database_probe(self, name: str, statement: str) -> DependencyCheck:
        try:
            found = await asyncio.wait_for(
                asyncio.to_thread(self._execute_database_probe, statement),
                timeout=self.timeout_seconds,
            )
        except Exception:
            return DependencyCheck(
                name=name,
                status=DependencyStatus.UNAVAILABLE,
                detail=f"{name} is unavailable",
            )
        if name == "pgvector" and not found:
            return DependencyCheck(
                name=name,
                status=DependencyStatus.UNAVAILABLE,
                detail="pgvector extension is unavailable",
            )
        return DependencyCheck(name=name, status=DependencyStatus.HEALTHY, detail="available")

    @staticmethod
    def _execute_database_probe(statement: str) -> bool:
        with engine.connect() as connection:
            result = connection.execute(text(statement))
            return result.first() is not None

    async def valkey(self) -> DependencyCheck:
        parsed = urlparse(settings.VALKEY_URL)
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(parsed.hostname, parsed.port or 6379),
                timeout=self.timeout_seconds,
            )
            writer.write(b"PING\r\n")
            await writer.drain()
            response = await asyncio.wait_for(reader.readline(), timeout=self.timeout_seconds)
            writer.close()
            await writer.wait_closed()
        except (OSError, TimeoutError, ValueError):
            return DependencyCheck(
                name="valkey",
                status=DependencyStatus.UNAVAILABLE,
                detail="valkey is unavailable",
            )
        if response != b"+PONG\r\n":
            return DependencyCheck(
                name="valkey",
                status=DependencyStatus.UNAVAILABLE,
                detail="valkey returned an unexpected response",
            )
        return DependencyCheck(name="valkey", status=DependencyStatus.HEALTHY, detail="available")

    async def minio(self) -> DependencyCheck:
        return await self._http_probe(
            "minio", f"{str(settings.MINIO_ENDPOINT).rstrip('/')}/minio/health/live"
        )

    async def grobid(self) -> DependencyCheck:
        result = await self._http_probe(
            "grobid", f"{str(settings.GROBID_URL).rstrip('/')}/api/isalive"
        )
        if result.status == DependencyStatus.UNAVAILABLE:
            return result.model_copy(update={"status": DependencyStatus.DEGRADED})
        return result

    async def _http_probe(self, name: str, url: str) -> DependencyCheck:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(url)
            response.raise_for_status()
        except httpx.HTTPError:
            return DependencyCheck(
                name=name,
                status=DependencyStatus.UNAVAILABLE,
                detail=f"{name} is unavailable",
            )
        return DependencyCheck(name=name, status=DependencyStatus.HEALTHY, detail="available")


class HealthService:
    def __init__(self, probe: HealthProbe | None = None) -> None:
        self.probe = probe or HealthProbe()

    async def core_dependencies(self) -> list[DependencyCheck]:
        return list(
            await asyncio.gather(
                self.probe.postgres(),
                self.probe.pgvector(),
                self.probe.valkey(),
                self.probe.minio(),
            )
        )

    async def all_dependencies(self) -> list[DependencyCheck]:
        core, grobid = await asyncio.gather(
            self.core_dependencies(), self.probe.grobid()
        )
        return [
            DependencyCheck(name="api", status=DependencyStatus.HEALTHY, detail="available"),
            *core,
            grobid,
            DependencyCheck(
                name="model",
                status=(
                    DependencyStatus.UNKNOWN
                    if settings.model_status == "CONFIGURED"
                    else DependencyStatus.UNCONFIGURED
                ),
                detail=(
                    "provider is configured; no health call was made"
                    if settings.model_status == "CONFIGURED"
                    else "provider is not configured"
                ),
            ),
            DependencyCheck(
                name="openalex",
                status=(
                    DependencyStatus.UNKNOWN
                    if settings.openalex_status == "CONFIGURED"
                    else DependencyStatus.UNCONFIGURED
                ),
                detail=(
                    "provider is configured; no health call was made"
                    if settings.openalex_status == "CONFIGURED"
                    else "provider is not configured"
                ),
            ),
        ]
