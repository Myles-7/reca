import uuid
from datetime import UTC, datetime
from typing import Any

import pytest

from app.evidence_graph.invalidation import propagate_invalidation
from app.models import (
    AuditActorType,
    AuditLog,
    Claim,
    ClaimConfidence,
    ClaimEvidenceLink,
    ClaimStatus,
    ClaimType,
    EvidenceLinkStatus,
    EvidenceLinkStrength,
    EvidenceObjectType,
    EvidenceRelationType,
)

pytestmark = pytest.mark.no_database


class _Rows:
    def __init__(self, values: list[ClaimEvidenceLink]) -> None:
        self.values = values

    def all(self) -> list[ClaimEvidenceLink]:
        return [
            value
            for value in self.values
            if value.status in {EvidenceLinkStatus.ACTIVE, EvidenceLinkStatus.SUGGESTED}
        ]


class _Session:
    def __init__(self, link: ClaimEvidenceLink, claim: Claim) -> None:
        self.link = link
        self.claim = claim
        self.added: list[Any] = []

    def exec(self, statement: object) -> _Rows:
        return _Rows([self.link])

    def get(self, model: type[object], object_id: uuid.UUID) -> object | None:
        if model is Claim and object_id == self.claim.id:
            return self.claim
        return None

    def add(self, value: object) -> None:
        self.added.append(value)

    def flush(self) -> None:
        return None


def test_invalidation_propagation_preserves_history_and_is_idempotent() -> None:
    project_id = uuid.uuid4()
    claim = Claim(
        project_id=project_id,
        claim_type=ClaimType.STATISTICAL_RESULT,
        claim_text="The registered analysis found a difference.",
        source_object_type="analysis_result",
        source_object_id=uuid.uuid4(),
        source_location={"result_key": "primary"},
        source_hash="a" * 64,
        text_hash="b" * 64,
        status=ClaimStatus.SUPPORTED,
        confidence=ClaimConfidence.HIGH,
        created_by_actor_type=AuditActorType.USER,
    )
    source_id = uuid.uuid4()
    link = ClaimEvidenceLink(
        project_id=project_id,
        claim_id=claim.id,
        evidence_object_type=EvidenceObjectType.ANALYSIS_RESULT,
        evidence_object_id=source_id,
        relation_type=EvidenceRelationType.SUPPORTED_BY,
        strength=EvidenceLinkStrength.STRONG,
        status=EvidenceLinkStatus.ACTIVE,
        source_hash="c" * 64,
        source_version={"analysis_run_id": str(uuid.uuid4())},
        created_by_actor_type=AuditActorType.USER,
        idempotency_key="stage1-invalidation",
        confirmed_at=datetime.now(UTC),
    )
    session = _Session(link, claim)

    first = propagate_invalidation(
        session,  # ty: ignore[invalid-argument-type]
        project_id=project_id,
        object_type=EvidenceObjectType.ANALYSIS_RESULT,
        object_id=source_id,
        reason="AnalysisRun was invalidated.",
        source_hash="c" * 64,
    )
    second = propagate_invalidation(
        session,  # ty: ignore[invalid-argument-type]
        project_id=project_id,
        object_type=EvidenceObjectType.ANALYSIS_RESULT,
        object_id=source_id,
        reason="AnalysisRun was invalidated.",
        source_hash="c" * 64,
    )

    assert first.invalidated_link_ids == (link.id,)
    assert first.affected_claim_ids == (claim.id,)
    assert second.invalidated_link_ids == ()
    assert link.status == EvidenceLinkStatus.INVALIDATED
    assert link.invalidation_reason == "AnalysisRun was invalidated."
    assert claim.status == ClaimStatus.NEEDS_EVIDENCE
    audit_logs = [value for value in session.added if isinstance(value, AuditLog)]
    assert len(audit_logs) == 1
    assert audit_logs[0].after_snapshot["path"][-1] == f"CLAIM:{claim.id}"
