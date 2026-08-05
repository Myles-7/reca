import uuid
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, func, select

from app.artifacts import service as artifact_service
from app.figures import renderer
from app.jobs import service as job_service
from app.models import (
    Artifact,
    CodeArtifact,
    Figure,
    FigureRenderRun,
    FigureRenderRunStatus,
    FigureStatus,
    Job,
    JobStatus,
)
from app.workers import jobs as worker_jobs
from tests.api.routes.test_analysis import (
    MemoryStorage,
    RecordingDispatcher,
    _analysis_inputs,
    _project,
    _user_headers,
)


@pytest.fixture
def figure_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[MemoryStorage, RecordingDispatcher]:
    from app.api.routes import figures as figure_routes

    storage = MemoryStorage()
    dispatcher = RecordingDispatcher()
    monkeypatch.setattr(artifact_service, "storage", storage)
    monkeypatch.setattr(figure_routes, "dispatcher", dispatcher)
    monkeypatch.setattr(renderer, "FONT_FAMILY", "DejaVu Sans")
    return storage, dispatcher


def _figure_plan(
    client: TestClient,
    headers: dict[str, str],
    project_id: str,
    version_id: str,
    columns: dict[str, str],
) -> str:
    response = client.post(
        f"/api/v1/projects/{project_id}/figure-plans",
        headers=headers,
        json={
            "dataset_version_id": version_id,
            "chart_type": "SCATTER",
            "parameters": {
                "kind": "SCATTER",
                "x_column_id": columns["x"],
                "y_column_id": columns["y"],
                "x_label": "X",
                "y_label": "Y",
                "x_unit": "points",
                "y_unit": "points",
                "dpi": 120,
            },
            "caption": "A deterministic scatter Figure.",
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["data"]["status"] == "READY"
    return response.json()["data"]["id"]


def test_figure_api_worker_artifacts_confirmation_and_atomicity(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    figure_runtime: tuple[MemoryStorage, RecordingDispatcher],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage, dispatcher = figure_runtime
    project = _project(client, normal_user_token_headers)
    _, columns = _analysis_inputs(client, db, normal_user_token_headers, project["id"])
    dataset = client.get(
        f"/api/v1/projects/{project['id']}/datasets",
        headers=normal_user_token_headers,
    ).json()["data"][0]
    version_id = dataset["current_version_id"]
    plan_id = _figure_plan(
        client,
        normal_user_token_headers,
        project["id"],
        version_id,
        columns,
    )
    key = str(uuid.uuid4())
    accepted = client.post(
        f"/api/v1/figure-plans/{plan_id}/render-runs",
        headers={**normal_user_token_headers, "Idempotency-Key": key},
        json={"reason": "Publication render"},
    )
    replay = client.post(
        f"/api/v1/figure-plans/{plan_id}/render-runs",
        headers={**normal_user_token_headers, "Idempotency-Key": key},
        json={"reason": "Publication render"},
    )
    assert accepted.status_code == replay.status_code == 202
    assert replay.json()["meta"]["idempotency_replayed"] is True
    assert len(dispatcher.calls) == 1
    object_count_before_render = len(storage.objects)
    run_id = uuid.UUID(accepted.json()["data"]["figure_render_run"]["id"])
    job_id = uuid.UUID(accepted.json()["data"]["job"]["id"])
    assert worker_jobs._execute_job(object(), str(job_id))["completed"] is True
    db.expire_all()
    render_run = db.get(FigureRenderRun, run_id)
    job = db.get(Job, job_id)
    figure = db.exec(select(Figure).where(Figure.figure_render_run_id == run_id)).one()
    assert (
        render_run is not None and render_run.status == FigureRenderRunStatus.COMPLETED
    )
    assert job is not None and job.status == JobStatus.COMPLETED
    assert figure.status == FigureStatus.READY
    assert len(storage.objects) == object_count_before_render + 4
    assert db.get(CodeArtifact, figure.code_artifact_id) is not None
    assert db.exec(select(func.count()).select_from(Artifact)).one() >= 4

    stale_request = client.post(
        f"/api/v1/figure-plans/{plan_id}/render-runs",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"reason": "worker loss reconciliation"},
    )
    assert stale_request.status_code == 202, stale_request.text
    stale_run_id = uuid.UUID(stale_request.json()["data"]["figure_render_run"]["id"])
    stale_job_id = uuid.UUID(stale_request.json()["data"]["job"]["id"])
    claim = job_service.claim_job(
        db,
        job_id=stale_job_id,
        worker_id="lost-figure-worker",
        engine="figure-renderer",
        engine_version="1.0.0",
    )
    assert claim is not None
    claimed_job = db.get(Job, stale_job_id)
    assert claimed_job is not None and claimed_job.last_heartbeat_at is not None
    assert (
        job_service.fail_stale_running_jobs(
            db,
            heartbeat_before=claimed_job.last_heartbeat_at + timedelta(seconds=1),
        )
        == 1
    )
    db.expire_all()
    stale_run = db.get(FigureRenderRun, stale_run_id)
    assert stale_run is not None and stale_run.status == FigureRenderRunStatus.FAILED
    assert stale_run.error_code == "JOB_TIMEOUT"
    assert (
        db.exec(
            select(Figure).where(Figure.figure_render_run_id == stale_run_id)
        ).first()
        is None
    )
    assert (
        db.exec(
            select(CodeArtifact).where(
                CodeArtifact.figure_render_run_id == stale_run_id
            )
        ).first()
        is None
    )

    detail = client.get(
        f"/api/v1/figures/{figure.id}", headers=normal_user_token_headers
    )
    assert detail.status_code == 200
    assert {item["format"] for item in detail.json()["data"]["artifacts"]} == {
        "PNG",
        "SVG",
        "PDF",
        "CODE",
    }
    for format_name in ("png", "svg", "pdf", "code"):
        download = client.get(
            f"/api/v1/figures/{figure.id}/downloads/{format_name}",
            headers=normal_user_token_headers,
        )
        assert download.status_code == 200, download.text

    _, outsider_headers = _user_headers(client, db)
    assert (
        client.get(f"/api/v1/figures/{figure.id}", headers=outsider_headers).status_code
        == 404
    )
    confirmation = client.post(
        f"/api/v1/figures/{figure.id}/approval-requests",
        headers=normal_user_token_headers,
    )
    assert confirmation.status_code == 201, confirmation.text
    approval_id = confirmation.json()["data"]["approval_id"]
    approved = client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        headers={**normal_user_token_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"decision_reason": "Figure reviewed.", "item_decisions": []},
    )
    assert approved.status_code == 200, approved.text
    db.expire_all()
    assert db.get(Figure, figure.id).status == FigureStatus.CONFIRMED

    second_plan_id = _figure_plan(
        client,
        normal_user_token_headers,
        project["id"],
        version_id,
        columns,
    )
    second = client.post(
        f"/api/v1/figure-plans/{second_plan_id}/render-runs",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={},
    )
    second_run_id = uuid.UUID(second.json()["data"]["figure_render_run"]["id"])
    second_job_id = uuid.UUID(second.json()["data"]["job"]["id"])
    objects_before_failed_render = set(storage.objects)
    original_create = artifact_service.create_generated_bytes_artifact
    calls = 0

    def fail_third(*args: object, **kwargs: object) -> Artifact:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise RuntimeError("simulated finalize failure")
        return original_create(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(artifact_service, "create_generated_bytes_artifact", fail_third)
    with pytest.raises(Exception, match="Figure Artifacts could not be finalized"):
        worker_jobs._execute_job(object(), str(second_job_id))
    db.expire_all()
    failed = db.get(FigureRenderRun, second_run_id)
    assert failed is not None and failed.status == FigureRenderRunStatus.FAILED
    assert (
        db.exec(
            select(func.count())
            .select_from(Figure)
            .where(Figure.figure_render_run_id == second_run_id)
        ).one()
        == 0
    )
    assert set(storage.objects) == objects_before_failed_render
