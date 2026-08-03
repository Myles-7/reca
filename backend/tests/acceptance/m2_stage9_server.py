"""Deterministic M2 browser-acceptance server using recorded external inputs."""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import uvicorn

from app.adapters.documents import GrobidResult
from app.adapters.literature import PyAlexOpenAlexProvider, RecordedOpenAlexTransport
from app.api.routes import documents as document_routes
from app.api.routes import literature as literature_routes
from app.api.routes import query_plans as query_plan_routes
from app.api.routes import research_questions as research_question_routes
from app.documents import service as document_service
from app.literature import service as literature_service
from app.main import app
from app.workers import jobs as worker_jobs
from tests.documents.test_parsing import TEI

_OPENALEX_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "openalex"
    / "works_recorded.json"
)


class AcceptanceWorkerDispatcher:
    """Dispatch the registered Worker lifecycle after the request commits QUEUED."""

    def dispatch(self, *, job_id: object, task_id: str) -> None:
        assert task_id
        worker = threading.Thread(
            target=self._execute,
            args=(str(job_id),),
            daemon=True,
        )
        worker.start()

    @staticmethod
    def _execute(job_id: str) -> None:
        time.sleep(0.1)
        worker_jobs._execute_job(
            SimpleNamespace(request=SimpleNamespace(hostname="m2-stage9-worker")),
            job_id,
        )


class RecordedGrobid:
    def parse(self, pdf_path: Path, *, extract_coordinates: bool) -> GrobidResult:
        assert isinstance(extract_coordinates, bool)
        assert pdf_path.read_bytes().startswith(b"%PDF")
        return GrobidResult(
            tei=TEI,
            version="0.8.2",
            revision="recorded-m2-stage9",
        )


def configure_recorded_acceptance() -> None:
    recorded = json.loads(_OPENALEX_FIXTURE.read_text(encoding="utf-8"))
    provider = PyAlexOpenAlexProvider(
        transport=RecordedOpenAlexTransport(recorded["recordings"])
    )
    dispatcher = AcceptanceWorkerDispatcher()

    literature_service.PyAlexOpenAlexProvider = lambda: provider  # type: ignore[misc]
    document_service.GrobidAdapter = RecordedGrobid  # type: ignore[misc]
    research_question_routes.dispatcher = dispatcher
    query_plan_routes.dispatcher = dispatcher
    literature_routes.dispatcher = dispatcher
    document_routes.dispatcher = dispatcher


def main() -> None:
    configure_recorded_acceptance()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")


if __name__ == "__main__":
    main()
