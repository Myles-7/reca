from __future__ import annotations

import uuid
from typing import Any, cast

import pytest
from sqlmodel import Session

from app.exports.collector import enumerate_candidates
from app.exports.schemas import ReproPackageCreate
from app.models import (
    Artifact,
    ArtifactStatus,
    ArtifactType,
    ExportItemIncludeStatus,
)

pytestmark = pytest.mark.no_database


class _Result:
    def __init__(self, values: list[Any]) -> None:
        self.values = values

    def all(self) -> list[Any]:
        return self.values


class _Session:
    def __init__(self, artifacts: list[Artifact]) -> None:
        self.artifacts = artifacts

    def exec(self, statement: Any) -> _Result:
        entity = statement.column_descriptions[0].get("entity")
        return _Result(self.artifacts if entity is Artifact else [])


def _artifact(
    *,
    project_id: uuid.UUID,
    artifact_type: ArtifactType,
    status: ArtifactStatus = ArtifactStatus.AVAILABLE,
    metadata: dict[str, Any] | None = None,
) -> Artifact:
    artifact_id = uuid.uuid4()
    return Artifact(
        id=artifact_id,
        project_id=project_id,
        artifact_type=artifact_type,
        filename=f"{artifact_id}.bin",
        storage_key=f"projects/{project_id}/{artifact_id}",
        mime_type="application/octet-stream",
        size_bytes=1,
        sha256="a" * 64,
        is_original=False,
        status=status,
        artifact_metadata=metadata,
    )


def test_readiness_downgrades_unknown_and_unverified_content() -> None:
    project_id = uuid.uuid4()
    pdf = _artifact(project_id=project_id, artifact_type=ArtifactType.PDF_DOCUMENT)
    model_output = _artifact(
        project_id=project_id, artifact_type=ArtifactType.MODEL_OUTPUT
    )
    missing = _artifact(
        project_id=project_id,
        artifact_type=ArtifactType.OTHER,
        status=ArtifactStatus.FAILED,
    )
    session = cast(Session, _Session([pdf, model_output, missing]))

    candidates, blocking, warnings, _limitations = enumerate_candidates(
        session,
        project_id=project_id,
        request=ReproPackageCreate(
            include_original_literature_files=True,
            include_model_output_artifacts=True,
        ),
    )
    by_id = {item.artifact_id: item for item in candidates}

    assert by_id[pdf.id].include_status == ExportItemIncludeStatus.METADATA_ONLY
    assert (
        by_id[model_output.id].include_status == ExportItemIncludeStatus.METADATA_ONLY
    )
    assert by_id[missing.id].include_status == ExportItemIncludeStatus.MISSING
    assert {item["code"] for item in blocking} == {"ARTIFACT_NOT_AVAILABLE"}
    assert {item["code"] for item in warnings} == {
        "LITERATURE_LICENSE_UNKNOWN",
        "MODEL_OUTPUT_REDACTION_UNVERIFIED",
    }


def test_sensitive_content_is_excluded_or_requires_formal_confirmation() -> None:
    project_id = uuid.uuid4()
    sensitive = _artifact(
        project_id=project_id,
        artifact_type=ArtifactType.OTHER,
        metadata={"sensitive": True},
    )
    session = cast(Session, _Session([sensitive]))

    excluded, _, warnings, _ = enumerate_candidates(
        session, project_id=project_id, request=ReproPackageCreate()
    )
    assert excluded[0].include_status == ExportItemIncludeStatus.EXCLUDED
    assert warnings == []

    included, _, warnings, _ = enumerate_candidates(
        session,
        project_id=project_id,
        request=ReproPackageCreate(include_sensitive_data=True),
    )
    assert included[0].include_status == ExportItemIncludeStatus.INCLUDED
    assert [item["code"] for item in warnings] == [
        "SENSITIVE_DATA_CONFIRMATION_REQUIRED"
    ]
