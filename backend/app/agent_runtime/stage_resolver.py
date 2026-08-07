from __future__ import annotations

from app.models import ProjectStage

from .registry import TOOL_REGISTRY
from .schemas import ProjectContextSnapshot, StageResolution

_STAGE_TOOLS: dict[ProjectStage, tuple[str, ...]] = {
    ProjectStage.INTENT: ("get_project_state", "parse_research_question"),
    ProjectStage.LITERATURE: (
        "generate_query_plan",
        "search_literature",
        "list_project_literature",
    ),
    ProjectStage.REVIEW: (
        "get_literature_matrix",
        "retrieve_evidence",
        "extract_literature_fields",
        "summarize_evidence_set",
    ),
    ProjectStage.TOPIC: ("generate_topic_candidates", "get_research_question"),
    ProjectStage.DATA: (
        "get_dataset_version",
        "profile_dataset",
        "suggest_cleaning_plan",
    ),
    ProjectStage.ANALYSIS: (
        "get_analysis_plan",
        "validate_analysis_assumptions",
        "run_descriptive_statistics",
    ),
    ProjectStage.FIGURE: ("get_figure", "recommend_figure", "render_figure"),
    ProjectStage.MANUSCRIPT: ("get_manuscript_issues", "check_manuscript"),
    ProjectStage.EVIDENCE: (
        "get_claim_evidence_graph",
        "retrieve_evidence",
        "audit_claim",
    ),
    ProjectStage.EXPORT: ("get_export_readiness", "export_repro_package"),
}


def resolve_stage(
    snapshot: ProjectContextSnapshot, *, expected_hash: str | None = None
) -> StageResolution:
    reasons: list[str] = []
    fail_closed = False
    if expected_hash is not None and snapshot.canonical_hash != expected_hash:
        reasons.append("SNAPSHOT_HASH_MISMATCH")
        fail_closed = True
    if snapshot.degraded:
        reasons.append("CONTEXT_DEGRADED")
        fail_closed = True
    if not snapshot.permissions or "project.read" not in snapshot.permissions:
        reasons.append("PROJECT_READ_DENIED")
        fail_closed = True
    if snapshot.project_status != "ACTIVE":
        reasons.append("PROJECT_NOT_ACTIVE")
        fail_closed = True
    if snapshot.blocking_issues:
        reasons.append("BLOCKING_ISSUES_PRESENT")
    if snapshot.pending_approval_ids:
        reasons.append("PENDING_APPROVALS_PRESENT")
    candidates = (
        []
        if fail_closed
        else [
            name
            for name in (
                "get_project_state",
                *(("get_pending_approvals",) if snapshot.pending_approval_ids else ()),
                *(
                    ("apply_approved_transformations",)
                    if snapshot.pending_approval_ids
                    and snapshot.project_stage == ProjectStage.DATA
                    else ()
                ),
                *_STAGE_TOOLS.get(snapshot.project_stage, ()),
            )
            if name in TOOL_REGISTRY
            and TOOL_REGISTRY[name].enabled
            and TOOL_REGISTRY[name].required_project_action in snapshot.permissions
        ]
    )
    return StageResolution(
        project_id=snapshot.project_id,
        current_stage=None if fail_closed else snapshot.project_stage,
        blockers=snapshot.blocking_issues,
        pending_approval_ids=snapshot.pending_approval_ids,
        allowed_next_actions=[] if fail_closed else snapshot.allowed_next_actions,
        candidate_tools=candidates,
        reason_codes=reasons or ["STAGE_RESOLVED"],
        source_object_versions=snapshot.source_object_versions,
        fail_closed=fail_closed,
    )
