from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.models import ModelDataAccessLevel, ProjectStage

from .schemas import (
    ApplyApprovedTransformationsInput,
    ProfileDatasetInput,
    StrictModel,
    ToolInput,
    ToolOutput,
)


class ToolCategory(StrEnum):
    READ_ONLY = "READ_ONLY"
    SUGGESTION = "SUGGESTION"
    SIDE_EFFECT = "SIDE_EFFECT"


class Confirmation(StrEnum):
    NONE = "NONE"
    LIGHT_CONFIRMATION = "LIGHT_CONFIRMATION"
    FORMAL_APPROVAL = "FORMAL_APPROVAL"
    PROHIBITED = "PROHIBITED"


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    version: str
    category: ToolCategory
    confirmation: Confirmation
    required_project_action: str
    data_access_ceiling: ModelDataAccessLevel
    allowed_stages: frozenset[ProjectStage]
    preconditions: tuple[str, ...]
    timeout_seconds: int
    max_calls: int
    idempotent: bool
    handler_reference: str | None
    output_semantics: str
    description: str
    enabled: bool
    disabled_reason_code: str | None
    input_schema: type[StrictModel] = ToolInput
    output_schema: type[ToolOutput] = ToolOutput


READ_ONLY = (
    "get_project_state",
    "get_pending_approvals",
    "get_research_question",
    "list_project_literature",
    "get_literature_record",
    "get_literature_matrix",
    "retrieve_evidence",
    "get_dataset_profile",
    "get_dataset_version",
    "get_analysis_plan",
    "get_analysis_result",
    "get_figure",
    "get_manuscript_issues",
    "get_claim_evidence_graph",
    "get_export_readiness",
)
SUGGESTIONS = (
    "parse_research_question",
    "generate_query_plan",
    "suggest_literature_decision",
    "extract_literature_fields",
    "summarize_evidence_set",
    "generate_topic_candidates",
    "suggest_cleaning_plan",
    "suggest_analysis_plan",
    "recommend_figure",
    "suggest_manuscript_issues",
    "audit_claim",
)
SIDE_EFFECTS = (
    "search_literature",
    "verify_literature_record",
    "parse_document",
    "profile_dataset",
    "preview_cleaning_plan",
    "apply_approved_transformations",
    "validate_analysis_assumptions",
    "run_descriptive_statistics",
    "run_group_comparison",
    "run_correlation",
    "run_simple_linear_regression",
    "render_figure",
    "check_manuscript",
    "export_repro_package",
)
FORMAL_APPROVAL_TOOLS = frozenset(
    {"apply_approved_transformations", "export_repro_package"}
)
PRODUCTION_WRAPPERS = frozenset(
    {
        "get_project_state",
        "get_pending_approvals",
        "retrieve_evidence",
        "profile_dataset",
        "apply_approved_transformations",
    }
)
ALL_STAGES = frozenset(ProjectStage)
HANDLER_REFERENCES = {
    "get_project_state": "app.agent_runtime.snapshot.build_project_context_snapshot",
    "get_pending_approvals": "app.approvals.service.list_approvals",
    "get_research_question": "app.research_questions.service.get_current_for_project",
    "parse_research_question": "app.research_questions.scoping.request_scoping_job",
    "generate_query_plan": "app.query_plans.generation.request_generation_job",
    "list_project_literature": "app.literature.service.list_literature",
    "get_literature_record": "app.literature.service.get_literature",
    "search_literature": "app.literature.service.request_search_job",
    "parse_document": "app.documents.service.request_parse",
    "extract_literature_fields": "app.evidence.extraction.request_extraction_job",
    "get_literature_matrix": "app.evidence.review.list_matrix",
    "retrieve_evidence": "app.evidence.retrieval.search_evidence",
    "summarize_evidence_set": "app.evidence.analysis.request_summary_job",
    "generate_topic_candidates": "app.evidence.analysis.request_topic_job",
    "get_dataset_profile": "app.datasets.service.get_version",
    "get_dataset_version": "app.datasets.service.get_version",
    "profile_dataset": "app.data_quality.service.request_quality_run",
    "suggest_cleaning_plan": "app.cleaning.suggestion.suggest_plan",
    "preview_cleaning_plan": "app.cleaning.service.preview_plan",
    "apply_approved_transformations": "app.cleaning.service.execute_plan",
    "get_analysis_plan": "app.analysis.service.get_plan",
    "get_analysis_result": "app.analysis.service.get_results",
    "validate_analysis_assumptions": "app.analysis.service.validate_plan",
    "run_descriptive_statistics": "app.analysis.service.create_run",
    "run_group_comparison": "app.analysis.service.create_run",
    "run_correlation": "app.analysis.service.create_run",
    "run_simple_linear_regression": "app.analysis.service.create_run",
    "get_figure": "app.figures.service.get_figure",
    "recommend_figure": "app.figures.service.recommendation",
    "render_figure": "app.figures.service.create_render_run",
    "get_manuscript_issues": "app.manuscripts.service.list_issues",
    "check_manuscript": "app.manuscripts.service.create_check_run",
    "get_claim_evidence_graph": "app.evidence_graph.projector.project_graph",
    "audit_claim": "app.evidence_graph.auditors.request_claim_audit",
    "get_export_readiness": "app.exports.service.readiness_check",
    "export_repro_package": "app.exports.service.create_repro_package_export",
}


def _definition(name: str, category: ToolCategory) -> ToolDefinition:
    confirmation = Confirmation.NONE
    if category == ToolCategory.SUGGESTION:
        confirmation = Confirmation.LIGHT_CONFIRMATION
    if name in FORMAL_APPROVAL_TOOLS:
        confirmation = Confirmation.FORMAL_APPROVAL
    enabled = name in PRODUCTION_WRAPPERS
    required_action = (
        "dataset.quality.run"
        if name == "profile_dataset"
        else "dataset.cleaning.execute"
        if name == "apply_approved_transformations"
        else "project.read"
        if category == ToolCategory.READ_ONLY
        else "project.update"
    )
    input_schema = (
        ProfileDatasetInput
        if name == "profile_dataset"
        else ApplyApprovedTransformationsInput
        if name == "apply_approved_transformations"
        else ToolInput
    )
    return ToolDefinition(
        name=name,
        version="1.0",
        category=category,
        confirmation=confirmation,
        required_project_action=required_action,
        data_access_ceiling=(
            ModelDataAccessLevel.VERIFIED_EVIDENCE_ONLY
            if name in {"retrieve_evidence", "summarize_evidence_set", "audit_claim"}
            else ModelDataAccessLevel.REDACTED_CONTENT
        ),
        allowed_stages=ALL_STAGES,
        preconditions=(
            "CURRENT_PROJECT",
            "CURRENT_SNAPSHOT",
            "AUTHORIZED_SOURCE_HASHES",
        ),
        timeout_seconds=30 if category == ToolCategory.READ_ONLY else 120,
        max_calls=5 if category == ToolCategory.READ_ONLY else 2,
        idempotent=category != ToolCategory.SUGGESTION or name.startswith("suggest_"),
        handler_reference=HANDLER_REFERENCES.get(name),
        output_semantics="READ_PROJECTION"
        if category == ToolCategory.READ_ONLY
        else "CANDIDATE_OR_GOVERNED_RESULT",
        description=name.replace("_", " "),
        enabled=enabled,
        disabled_reason_code=None if enabled else "TOOL_WRAPPER_UNAVAILABLE",
        input_schema=input_schema,
    )


TOOL_REGISTRY = {
    item.name: item
    for item in (
        *(_definition(name, ToolCategory.READ_ONLY) for name in READ_ONLY),
        *(_definition(name, ToolCategory.SUGGESTION) for name in SUGGESTIONS),
        *(_definition(name, ToolCategory.SIDE_EFFECT) for name in SIDE_EFFECTS),
    )
}

PROHIBITED_NAMES = frozenset(
    {
        "execute_shell",
        "execute_python",
        "execute_sql",
        "run_arbitrary_code",
        "delete_original_file",
        "overwrite_dataset",
        "modify_analysis_result",
        "approve_on_behalf_of_user",
        "download_paid_fulltext",
        "generate_complete_thesis",
        "bypass_permission",
        "apply_patch",
        "generic_http",
        "mcp_discovery",
        "hosted_tool",
    }
)


def get_tool(name: str, version: str = "1.0") -> ToolDefinition | None:
    definition = TOOL_REGISTRY.get(name)
    if definition is None or definition.version != version:
        return None
    return definition
