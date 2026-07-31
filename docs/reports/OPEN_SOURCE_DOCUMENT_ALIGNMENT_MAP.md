# RECA Open-Source Document Alignment Map

> Status: Phase 6 planning artifact
>
> Documentation status: Conditional Approval
>
> Root license: `PENDING_GOVERNANCE_DECISION`
> Authority: this file plans later documentation alignment; it does not change product, architecture, data, API, AI, Tool, test, security, or milestone contracts.

## 1. Scope and rules

This map translates the decisions in [Open-Source Integration Master Plan](../source-research/OPEN_SOURCE_INTEGRATION_MASTER_PLAN.md) into file-level follow-up work. A listed change is not evidence that an integration exists. Implementation status remains governed by the repository, milestone acceptance, and third-party records.

Alignment must preserve all Requirement IDs, Acceptance IDs, API paths, error codes, Schema names, Agent Tool names, enum values, Milestone IDs, ADR IDs, and M0 Issue IDs. New prose may name an upstream project or integration mode, but must not create a new business contract implicitly.

Risk scale:

- `LOW`: navigation, attribution, or implementation guidance only.
- `MEDIUM`: affects architecture, milestone scope, fallback, or acceptance wording but not stable identifiers.
- `HIGH`: touches evidence truth, business state, approval, data lineage, deterministic results, license isolation, or Agent authority.

## 2. Repository entry and governance files

| File | Required change | Old rule | New rule | Stable identifier impact | Risk |
| --- | --- | --- | --- | --- | --- |
| `README.md` | Add a short link to the master plan and state that listed projects are researched or planned, not necessarily implemented. | Open-source reuse is described generally. | Point readers to the six approved candidate stacks and implementation-status evidence. | None; no Requirement or milestone change. | LOW |
| `AGENTS.md` | Add the master plan to the reading matrix for dependency, service, Vendor, citation, PDF, data, and Agent integration tasks. | Agents read governance and project records separately. | Require master plan plus the relevant project record and milestone before integration work. | None; repository workflow only. | MEDIUM |
| `THIRD_PARTY_NOTICES.md` | Keep the registration template and add records only in the PR that actually adopts content or a runtime dependency. | Research records can be mistaken for adopted notices. | Research alone creates no attribution claim; adoption records pinned source, license, paths, and modifications. | None. | HIGH |

## 3. Formal entry documents

| File | Required change | Old rule | New rule | Stable identifier impact | Risk |
| --- | --- | --- | --- | --- | --- |
| `docs/PRODUCT_REQUIREMENTS.md` | Map stack benefits to existing requirements and Competition scope without naming new requirements. | Capabilities are mostly implementation-neutral. | PaperQA2, ASReview, CSL, ARS-Codex, and UX references enhance existing requirements only. | Preserve every Requirement ID and priority. | HIGH |
| `docs/ARCHITECTURE.md` | Add the six stacks, normalized integration modes, source-of-truth boundaries, and fallbacks. | Integrations are described project by project or generically. | Distinguish direct dependency, provider, service, selective Vendor, resource snapshot, and reference modes. | Preserve ADR references and architecture invariants. | HIGH |
| `docs/DATA_MODEL_AND_WORKFLOW.md` | Add explicit candidate-versus-authority notes for PaperQA2, ASReview, DVC, GX, SDK, and ARS outputs. | External state boundaries are distributed. | RECA objects and state machines remain authoritative; no upstream object becomes business truth. | No field, enum, unique constraint, FK, or state change. | HIGH |
| `docs/API_AI_TOOL_CONTRACTS.md` | Add implementation-provider notes and fallback semantics without changing contract identifiers. | Contracts do not consistently name candidate providers. | Provider choice is behind existing APIs, Schemas, and Tool contracts. | Zero API path, error, Schema, Tool, or enum changes. | HIGH |
| `docs/TEST_AND_ACCEPTANCE.md` | Add a cross-stack acceptance summary covering licenses, pinned versions, fallback, deterministic output, and authority boundaries. | Open-source acceptance is spread across test documents. | Every adopted integration needs contract, attribution, fallback, and golden-path evidence. | Preserve every Acceptance ID and M0 gate. | HIGH |
| `docs/SECURITY_AND_OPEN_SOURCE.md` | Link the master plan and clarify special-license isolation for Vendor/resource/service modes. | Reuse modes are generic. | Per-project plan selects a mode but adoption still requires license verification and attribution. | No security-level or approval-status change. | HIGH |
| `docs/IMPLEMENTATION_ROADMAP.md` | Summarize M1-M9 adoption order and validation spikes from the master plan. | Milestones mention capabilities without a unified integration sequence. | Integrate only within existing milestone boundaries; research is not implementation. | Preserve all Milestone IDs, entry gates, and P0 scope. | HIGH |

## 4. Product requirement documents

| File | Required change | Old rule | New rule | Stable identifier impact | Risk |
| --- | --- | --- | --- | --- | --- |
| `docs/product/PROJECT_AND_RESEARCH_REQUIREMENTS.md` | Map ARS scoping/checkpoints and SDK orchestration to existing RQ and project requirements. | Workflow support is implementation-neutral. | Reused assets produce candidates and prompts; RECA project/version/approval state remains authoritative. | No new or renamed Requirement IDs. | HIGH |
| `docs/product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md` | Map PyAlex, GROBID, PDF.js, PaperQA2, ASReview, pgvector, and Zotero compatibility to existing literature requirements. | The literature loop is specified without a final provider stack. | Use the researched chain while preserving user decisions and verified EvidenceSpan formation. | No new requirements; EvidenceSpan semantics unchanged. | HIGH |
| `docs/product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md` | Map Pandera, SciPy, statsmodels, Matplotlib, GX reference, and DVC reference to existing data requirements. | Deterministic implementation choices are not consolidated. | Pandera validates, SciPy/statsmodels compute, Matplotlib renders; RECA versions/results stay authoritative. | No metric, priority, or Requirement ID change. | HIGH |
| `docs/product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md` | Map python-docx, CSL resources, citation processor decision, React Flow, SDK, and ARS assets to existing manuscript/Agent requirements. | Citation and Agent implementation options are fragmented. | Preserve citation verification, single Orchestrator, Tool whitelist, and M8 boundary. | No Requirement ID or MANU-P0-018 change. | HIGH |
| `docs/product/UX_NONFUNCTIONAL_AND_TRACEABILITY.md` | Reference TanStack Table, React Flow, PDF.js, and Zotero UX as implementation choices with accessibility/performance acceptance. | UX requirements do not identify researched component candidates. | Components serve existing traceability and workbench requirements; upstream UX is not copied by default. | No NFR, traceability, or acceptance identifier change. | MEDIUM |

## 5. Architecture documents

| File | Required change | Old rule | New rule | Stable identifier impact | Risk |
| --- | --- | --- | --- | --- | --- |
| `docs/architecture/SYSTEM_COMPONENTS_AND_MODULES.md` | Place all six stacks in existing modules and identify direct, provider, service, Vendor, resource, and reference boundaries. | Components list generic technologies and adapters. | Each upstream has one owning RECA module and one declared runtime status. | No module contract or ADR ID change. | HIGH |
| `docs/architecture/DATA_FLOWS_AND_ADAPTERS.md` | Add the literature chain and data/statistics flow; record where providers/adapters are required and where direct integration is allowed. | Adapter decisions are not fully tied to researched projects. | PyAlex uses a lightweight provider; GROBID is a service; PaperQA2 is candidate-only; stable libraries may integrate directly. | No API, Schema, Tool, or object-name change. | HIGH |
| `docs/architecture/AGENT_ASYNC_AND_DEGRADATION.md` | Map Celery/Valkey and Agents SDK/ARS to existing Job, AgentRun, ModelInvocation, ToolCall, approval, and degradation rules. | Runtime mechanics and business authority are described independently. | Celery/SDK states are operational only; RECA records remain authoritative and fallbacks stay visible. | No status enum or Tool name change. | HIGH |
| `docs/architecture/OPERATIONS_DEPLOYMENT_AND_ADRS.md` | Add deployment implications, pinned-version rules, and proposed ADR-002 through ADR-008. | Only existing ADR and general deployment rules are listed. | Later ADRs capture stack decisions; Phase 6 creates none. | Existing ADR IDs unchanged; proposed IDs are planning labels only. | MEDIUM |

## 6. Data model documents

| File | Required change | Old rule | New rule | Stable identifier impact | Risk |
| --- | --- | --- | --- | --- | --- |
| `docs/data-model/FOUNDATION_AND_PROJECT_MODELS.md` | State that SDK Session and ARS workflow state cannot replace ResearchProject, ProjectContextSnapshot, ApprovalRecord, or AuditLog. | External orchestration state is not exhaustively named. | Imported orchestration metadata is supplementary and minimized. | No field, constraint, enum, or relationship change. | HIGH |
| `docs/data-model/LITERATURE_AND_EVIDENCE_MODELS.md` | Document PyAlex raw/provider mapping, GROBID conversion, embedding versioning, CandidateEvidence, ASReview ranking, and EvidenceSpan validation boundaries. | Provider-specific candidate states are not consolidated. | Upstream outputs remain candidates until RECA validation/user decision. | EvidenceSpan absence semantics and all states remain unchanged. | HIGH |
| `docs/data-model/DATA_ANALYSIS_AND_FIGURE_MODELS.md` | Map Pandera failures, deterministic library results, Matplotlib artifacts, DVC/GX references, and provenance metadata. | Library return objects are not explicitly separated from RECA records. | FailureCase, statsmodels Summary, DVC state, and GX results are inputs, never business truth. | No fields/enums/unique constraints added in this phase. | HIGH |
| `docs/data-model/MANUSCRIPT_AGENT_AND_EXPORT_MODELS.md` | Map DOCX/citation artifacts and SDK/ARS runtime metadata to existing manuscript and Agent records. | Implementation metadata sources are generic. | Preserve immutable source DOCX, citation verification, Prompt manifest, ModelInvocation access levels, and audit records. | No MANU-P0-018, Prompt, ToolCall, or export model change. | HIGH |
| `docs/data-model/STATE_MACHINES_AND_INVARIANTS.md` | Add external-state non-substitution invariants and fallback behavior. | Non-substitution rules are spread across research files. | External job, ranking, trace, workflow, and rendering states cannot advance formal RECA states. | No status, transition, approval, or invalidation change. | HIGH |

## 7. API, AI Schema, and Agent Tool contracts

| File | Required change | Old rule | New rule | Stable identifier impact | Risk |
| --- | --- | --- | --- | --- | --- |
| `docs/contracts/COMMON_API_JOB_AND_SSE_CONTRACTS.md` | Clarify that Celery/Valkey events are translated into existing Job/SSE contracts and that fallback remains observable. | Broker/worker implementation is abstract. | Operational backend may change without leaking Celery states into public contracts. | Zero path, error, DTO, or enum changes. | HIGH |
| `docs/contracts/PROJECT_RESEARCH_AND_LITERATURE_API.md` | Add provider notes for PyAlex, GROBID, PDF.js, PaperQA2, ASReview, and pgvector behind existing endpoints. | Endpoint behavior is provider-neutral. | Provider output is normalized before API exposure; candidate and decision boundaries remain explicit. | Zero API path, error, Schema, or status change. | HIGH |
| `docs/contracts/DATA_ANALYSIS_AND_FIGURE_API.md` | Identify Pandera/SciPy/statsmodels/Matplotlib as implementations behind existing endpoints. | Deterministic engines are not consistently named. | Library warnings/results are normalized to existing RECA contracts and artifacts. | Zero API path, error, Schema, or enum change. | HIGH |
| `docs/contracts/MANUSCRIPT_EVIDENCE_AND_EXPORT_API.md` | Add DOCX/CSL/citation processor and React Flow visualization boundaries. | Export and graph contracts are implementation-neutral. | Citation/rendering output requires RECA verification; graph UI is not graph authority. | Zero path, error, Schema, or MANU-P0-018 change. | HIGH |
| `docs/contracts/AI_SCHEMA_CONTRACTS.md` | Map PaperQA2 and ARS prompt/output candidates into existing envelopes and degradation rules. | Candidate upstream schemas are not named. | Upstream structures are converted; no upstream Schema becomes a public contract. | Zero Schema name or enum change. | HIGH |
| `docs/contracts/AGENT_TOOL_CONTRACTS.md` | Map SDK Function Tools to the existing whitelist and preserve approval/data-access/audit rules. | SDK is described only at a high level. | SDK registration is an implementation of existing Tools; Hosted/MCP/handoff require separate decisions. | Zero Tool name, parameter, permission, or approval change. | HIGH |

## 8. Testing and acceptance documents

| File | Required change | Old rule | New rule | Stable identifier impact | Risk |
| --- | --- | --- | --- | --- | --- |
| `docs/testing/M0_REGRESSION_BASELINE.md` | Add no runtime project-specific checks unless adoption changes M0 surfaces; preserve all six required CI jobs and two LOW risks. | M0 baseline predates these research decisions. | New integrations cannot weaken or bypass the frozen baseline. | No M0 Issue ID, job name, or gate change. | HIGH |
| `docs/testing/TEST_STRATEGY_AND_ENVIRONMENTS.md` | Define recorded/provider/service/resource/Vendor test layers and pinned-version fixtures. | Mock/recorded/live modes are generic. | Each adopted upstream declares offline, fallback, and upgrade-test strategy. | No acceptance or environment identifier change. | MEDIUM |
| `docs/testing/GOLDEN_SETS_AND_METRICS.md` | Add golden cases for TEI conversion, candidate evidence, ranking, data validation, statistics, charts, citations, DOCX, and Agent workflows. | Metrics exist by domain without a unified upstream matrix. | Compare normalized RECA outputs, not raw upstream snapshots alone. | Preserve all thresholds and Acceptance IDs. | HIGH |
| `docs/testing/CONTRACT_INTEGRATION_AND_SECURITY_TESTS.md` | Add license/attribution checks, service/provider contract tests, path isolation, sensitive tracing checks, and source-of-truth negative tests. | Security and adapter tests do not cover every researched mode. | Adopted integrations must prove isolation, fallback, normalization, and no authority substitution. | No path, error, Schema, Tool, or security-gate weakening. | HIGH |
| `docs/testing/E2E_ACCEPTANCE_AND_RELEASE_GATES.md` | Add milestone-specific stack acceptance and fallback demos while preserving current ACs. | E2E flows do not name the final researched combination. | Competition Core may use the stack only after deterministic, attributed, recoverable E2E evidence. | No AC added, removed, renamed, or weakened. | HIGH |

## 9. Security and open-source governance documents

| File | Required change | Old rule | New rule | Stable identifier impact | Risk |
| --- | --- | --- | --- | --- | --- |
| `docs/security/SECURITY_CONTROLS.md` | Add deployment notes for Valkey, GROBID, pgvector, citation workers, and model tracing. | Controls are technology-neutral. | Services remain private by default; secrets and trace payloads follow existing Competition safeguards. | No security classification change. | HIGH |
| `docs/security/FILE_MODEL_AND_AGENT_SECURITY.md` | Add GROBID/PDF.js/DOCX/Vendor/SDK boundaries, untrusted-file handling, and trace minimization. | File and Agent rules do not enumerate the selected stack. | Display, parsing, generation, and orchestration cannot bypass immutable originals or Tool controls. | No approval, access-level, or Agent prohibition change. | HIGH |
| `docs/security/OPERATIONS_DATA_AND_INCIDENTS.md` | Add service recovery/fallback expectations and pinned resource restoration for the six stacks. | Recovery guidance is service-generic. | Competition recovery includes known-good versions and visible degraded modes for adopted services. | No release-blocker or incident-level change. | MEDIUM |
| `docs/security/OPEN_SOURCE_GOVERNANCE.md` | Add mode-specific minimum records for direct dependency, service, selective Vendor, resource snapshot, development-only, deferred, and design reference decisions. | Integration modes are defined but not tied to this project matrix. | Adoption follows the master plan plus fresh license verification; research commits are not automatic implementation pins. | Root license remains pending; no legal conclusion added. | HIGH |

## 10. Roadmap documents

| File | Required change | Old rule | New rule | Stable identifier impact | Risk |
| --- | --- | --- | --- | --- | --- |
| `docs/roadmap/DELIVERY_WORKFLOW.md` | Add a lightweight integration gate: pin, license review, spike, contract mapping, attribution, fallback, acceptance. | Delivery workflow has general third-party review. | Every adoption PR records implementation metadata with the code change. | No milestone or approval-state change. | MEDIUM |
| `docs/roadmap/RISK_SCOPE_AND_RELEASE.md` | Add stack-specific license, service, fallback, determinism, and authority-substitution risks. | Risks are domain-level. | Deferred projects stay out of release scope until their decision gates pass. | No P0/P1 or release-gate change. | HIGH |
| `docs/roadmap/milestones/M1_FOUNDATION.md` | Add spikes for Celery, Valkey, pgvector, pgvector-python, Prompt manifest groundwork, and source metadata. | M1 foundation names platform capabilities generically. | Adopt foundation stack without replacing RECA Job, project, or audit authority. | M1 ID and Entry `ALLOWED` unchanged. | HIGH |
| `docs/roadmap/milestones/M2_RESEARCH_AND_LITERATURE.md` | Add PyAlex provider, GROBID service/client conversion, PDF.js baseline, and ARS scoping/deep-research asset evaluation. | M2 does not consolidate these upstream choices. | Use existing RQ/literature requirements; no imported workflow state becomes authoritative. | M2 and Requirement IDs unchanged. | HIGH |
| `docs/roadmap/milestones/M3_EVIDENCE_MATRIX.md` | Add pgvector retrieval, PaperQA2 candidate evidence, ASReview recommendation, PDF coordinate validation, and table UX. | M3 evidence work is provider-neutral. | Candidate evidence must be verified into EvidenceSpan; ranking requires user LiteratureDecision. | M3, ACs, and EvidenceSpan rules unchanged. | HIGH |
| `docs/roadmap/milestones/M4_DATA_QUALITY.md` | Add Pandera runtime adoption and GX design-reference review. | Data-quality engine choice is not final. | Pandera is P0 runtime; GX is not a second runtime authority. | M4 and data-quality identifiers unchanged. | HIGH |
| `docs/roadmap/milestones/M5_ANALYSIS_AND_FIGURES.md` | Add SciPy, statsmodels, Matplotlib, chart artifact metadata, and DVC development reference. | Statistical/rendering implementation is not consolidated. | Deterministic libraries implement existing analyses; RECA results and dataset versions remain truth. | M5, metrics, and AnalysisResult contract unchanged. | HIGH |
| `docs/roadmap/milestones/M6_MANUSCRIPT_AND_CLAIMS.md` | Add python-docx, controlled OOXML, CSL snapshot, citation decision spike, and evidence graph UI. | Manuscript stack choices are fragmented. | Original DOCX remains immutable; citation output and UI are not evidence authority. | M6 and manuscript identifiers unchanged. | HIGH |
| `docs/roadmap/milestones/M7_EVIDENCE_AND_EXPORT.md` | Add citation/export verification, resource attribution, reproducibility metadata, and ARS claim-verification asset adaptation. | Export stack does not consolidate these sources. | Existing audit/export boundaries remain authoritative, including MANU-P0-018. | M7 and MANU-P0-018 unchanged. | HIGH |
| `docs/roadmap/milestones/M8_AGENT.md` | Add Agents SDK runtime spike, selective ARS Vendor gate, Function Tool mapping, tracing minimization, and approval tests. | SDK and ARS are high-level candidates. | One RECA Orchestrator uses existing Tools; Session/Trace/ARS state remain non-authoritative. | M8, Tool names, Agent statuses, and approvals unchanged. | HIGH |
| `docs/roadmap/milestones/M9_DEMO_AND_RELEASE.md` | Add six-stack fallback rehearsal, license/attribution inventory, pinned-resource restoration, and no-implementation-misstatement check. | Demo gate lacks a unified integration inventory. | Release proves adopted components only; deferred/reference projects are labelled accurately. | M9, ACs, M0 baseline, and release status unchanged. | HIGH |

## 11. Development and implementation guidance

| File | Required change | Old rule | New rule | Stable identifier impact | Risk |
| --- | --- | --- | --- | --- | --- |
| `docs/development/CODEX_TASK_WORKFLOW.md` | Add a research-to-adoption checklist using the master plan and project records. | Dependency work follows general task workflow. | Confirm mode, current upstream, license, pin, owner, fallback, tests, and notices before editing code. | None. | MEDIUM |
| `docs/development/BACKEND_DATA_AND_ASYNC_RULES.md` | Add placement rules for providers, services, Celery tasks, pgvector queries, deterministic engines, and citation workers. | Backend boundaries are generic. | Third-party types remain outside domain models; Services own normalization and business transitions. | No API/model/enum change. | HIGH |
| `docs/development/FRONTEND_API_AND_ARTIFACT_RULES.md` | Add PDF.js, TanStack Table, React Flow, and citation UI placement rules. | Frontend vendor integration guidance is general. | UI libraries consume generated clients/domain view models and never become authority. | No API or generated-client change. | HIGH |
| `docs/development/TEST_GIT_AND_DELIVERY_RULES.md` | Add pinned-source, license, attribution, fallback, golden, and upgrade evidence to integration PR expectations. | Third-party checks are general. | Source metadata and tests land with each actual adoption. | M0 required CI remains unchanged. | MEDIUM |
| `docs/development/M0_CONTINUOUS_EXECUTION.md` | State that integration research cannot alter the completed M0 baseline or overwrite internalized template code. | M0 execution rules do not reference the new plan. | Foundation adoption is additive and gated; no upstream template rebase over M0. | M0 `COMPLETED`, commit, tag, issues, and gates unchanged. | HIGH |

## 12. Backend, frontend, and test READMEs

| File | Required change | Old rule | New rule | Stable identifier impact | Risk |
| --- | --- | --- | --- | --- | --- |
| `backend/README.md` | Link backend implementers to foundation, literature, data, manuscript, and Agent stack records. | Backend overview lists current local structure. | Planned integrations are labelled by milestone and runtime status. | None. | LOW |
| `backend/app/domain/README.md` | Add a prohibition on upstream objects/states becoming domain truth. | Domain isolation is general. | Candidate/provider/runtime objects are normalized into existing RECA models only. | No domain object change. | HIGH |
| `backend/app/workers/README.md` | Add Celery/Valkey operating boundary and Job/ProcessingRun authority rule. | Worker entrypoint is defined without full upstream mapping. | Celery states remain operational; idempotency and recovery use RECA records. | No queue, Job status, or Celery entrypoint change. | HIGH |
| `backend/app/agents/README.md` | Add SDK/ARS implementation boundary, trace minimization, and M8-only adoption rule. | Agent shell documents current placeholder/boundary. | One Orchestrator maps Function Tools to the existing whitelist. | No Agent, Tool, or approval contract change. | HIGH |
| `backend/app/adapters/README.md` | List required providers/services and cases where direct stable-library integration is allowed. | Adapter placement is generic. | PyAlex/GROBID and replaceable boundaries use adapters/providers; stable computational libraries may stay in Services. | No architecture identifier change. | MEDIUM |
| `backend/app/tools/README.md` | Add SDK Function Tool wrapper guidance and prohibit raw third-party tool exposure. | Tool wrappers follow existing whitelist rules. | SDK registration cannot alter names, schemas, permissions, approvals, or audit. | Zero Tool-name or Schema change. | HIGH |
| `backend/app/repositories/README.md` | Add pgvector project filtering and embedding-version persistence guidance. | Repository rules cover database access generally. | Vector queries enforce project scope and version lineage through existing repositories. | No table/model/constraint change. | HIGH |
| `backend/app/services/README.md` | Add normalization ownership for provider outputs, statistics, DOCX/citations, and candidate evidence. | Services own business logic generically. | Services translate upstream results and enforce RECA truth/approval rules. | No service contract identifier change. | HIGH |
| `backend/app/shared/README.md` | Clarify that shared code must not become a dumping ground for upstream SDK types. | Shared package rules are general. | Project-specific integrations stay in their owning module/provider. | None. | LOW |
| `backend/app/modules/README.md` | Map each stack component to an owning module and milestone. | Module ownership is domain-based only. | Every runtime dependency has one owner and declared fallback. | No module or milestone ID change. | MEDIUM |
| `frontend/README.md` | Link to PDF.js, TanStack Table, React Flow, and Zotero UX research with implementation-status labels. | Frontend overview does not consolidate researched choices. | Use direct dependencies only after milestone adoption and license checks. | None. | LOW |
| `frontend/src/api/README.md` | State that provider-specific DTOs never bypass the generated RECA client boundary. | API client boundary is generic. | PDF/viewer and table/graph components consume RECA contracts only. | Zero API/Schema/generated-client change. | HIGH |
| `frontend/src/app/README.md` | Add route/provider placement notes for the research workbench stack. | App composition guidance is generic. | Global providers stay minimal; feature integrations remain milestone-scoped. | None. | LOW |
| `frontend/src/vendor-integrations/README.md` | Record planned placement, license metadata, resource snapshots, and isolation for frontend upstreams. | Vendor integration directory has generic rules. | Each adopted package/resource has a pinned source and attribution record; references are not copied. | None. | HIGH |
| `frontend/src/features/README.md` | Map PDF viewer, literature tables, quality tables, and evidence graph UI to owning features. | Feature organization is capability-based. | Components remain presentation/workflow aids over authoritative backend data. | No feature contract change. | MEDIUM |
| `frontend/src/shared/README.md` | Restrict shared wrappers to genuinely cross-feature stable UI primitives. | Shared boundary is general. | Upstream-specific domain behavior stays in feature modules. | None. | LOW |
| `tests/unit/README.md` | Add unit targets for converters, provider normalization, deterministic calculations, and authority guards. | Unit test examples are generic. | Raw upstream outputs require boundary and negative tests. | No test ID change. | MEDIUM |
| `tests/integration/README.md` | Add recorded PyAlex, GROBID, pgvector, Celery/Valkey, citation, and SDK integration suites. | Integration matrix is generic. | Tests verify pins, fallbacks, normalization, isolation, and audit behavior. | No contract identifier change. | HIGH |
| `tests/e2e/README.md` | Add six-stack E2E scenarios only as milestones adopt them. | E2E README covers current flows. | Never assert a researched/deferred project as implemented; preserve all existing ACs. | No Acceptance ID change. | HIGH |
| `tests/golden/README.md` | Add fixture provenance and golden-output update rules for upstream-dependent outputs. | Golden fixture governance is general. | Golden cases pin upstream/resource versions and compare RECA-normalized results. | No metric or acceptance threshold change. | HIGH |

## 13. ADR and source-research documents

| File | Required change | Old rule | New rule | Stable identifier impact | Risk |
| --- | --- | --- | --- | --- | --- |
| `docs/decisions/ADR-001-ARS-CODEX-USAGE.md` | Do not change in Phase 6; later link ADR-007 and the final ARS asset decision without silently superseding license conditions. | Conditional selective/full reuse is allowed after review. | Preserve `NONCOMMERCIAL_INTENT_DECLARED`, attribution, isolation, and re-review gates. | ADR-001 ID and decision status unchanged. | HIGH |
| `docs/source-research/full-stack-fastapi-template.md` | Later add a backlink to the master plan and final mode. | Existing template-specific authority records M0 internalization. | `ALREADY_INTERNALIZED_BASELINE`; no wholesale upstream overwrite. | None. | MEDIUM |
| `docs/source-research/academic-research-skills-codex.md` | Later add the selected-asset implementation gate and master-plan backlink; keep research evidence intact. | Contains detailed ARS evidence and candidate schemes. | `SELECTIVE_VENDOR` is recommended, but no content is copied and ADR-001 still governs. | No ADR, Tool, Prompt, or milestone change. | HIGH |
| `docs/source-research/OPEN_SOURCE_INTEGRATION_MASTER_PLAN.md` | Treat as the Phase 6 decision index; update only when a later ADR or verified upstream change alters a decision. | Phase 0-5 decisions were distributed across reports. | One normalized matrix, six stacks, fallbacks, truth boundaries, scope, and ADR plan. | No stable contract change; planning labels only. | HIGH |
| `docs/source-research/projects/celery.md` | Add final mode and adoption status when M1 implementation begins. | Research recommendation only. | Direct dependency; RECA Job/ProcessingRun remains truth. | No Job status or milestone change. | HIGH |
| `docs/source-research/projects/valkey.md` | Add final mode and adoption status when M1 implementation begins. | Research recommendation only. | Independent service for broker/cache/ephemeral state, never business truth. | No state or milestone change. | HIGH |
| `docs/source-research/projects/pgvector.md` | Add final mode and adoption status when M1/M3 implementation begins. | Research recommendation only. | PostgreSQL extension/service capability with project filtering and embedding versioning. | No model or milestone change. | HIGH |
| `docs/source-research/projects/pgvector-python.md` | Add final mode and adoption status when ORM integration begins. | Research recommendation only. | Direct dependency behind repository/service boundaries. | No ORM model or contract change. | MEDIUM |
| `docs/source-research/projects/pyalex.md` | Add final provider mode and adoption status when M2 starts. | Research recommendation only. | Direct dependency with lightweight provider; no PyAlex objects persist or reach clients. | No literature model/API change. | HIGH |
| `docs/source-research/projects/grobid.md` | Add final service mode, image pin, converter owner, and fallback status at adoption. | Research recommendation only. | Independent service; TEI is intermediate, RECA document objects are truth. | No document model/status change. | HIGH |
| `docs/source-research/projects/grobid-client-python.md` | Add selected paths and modification record if Vendor adoption occurs. | Selective reuse candidate. | Selective Vendor for request/batch behavior; RECA owns output layout and conversion. | No API/model change. | HIGH |
| `docs/source-research/projects/pdfjs.md` | Add final direct-dependency status and viewer integration evidence at adoption. | Research recommendation only. | Display/interaction only; EvidenceSpan truth comes from validated RECA data. | EvidenceSpan contract unchanged. | HIGH |
| `docs/source-research/projects/paperqa2.md` | Add selected assets, modifications, and candidate-only tests if Vendor adoption occurs. | Deep research recommendation only. | Selective Vendor; output is CandidateEvidence and requires source/page/text validation. | No EvidenceSpan/Schema/Tool change. | HIGH |
| `docs/source-research/projects/asreview.md` | Add provider boundary and adoption evidence if active learning enters M3. | Research recommendation only. | Direct dependency with provider; ranking never writes LiteratureDecision. | No literature decision/status change. | HIGH |
| `docs/source-research/projects/pandera.md` | Add runtime rule-set version and adoption status at M4. | Research recommendation only. | Direct dependency and primary P0 validation runtime; RECA owns rules and issues. | No DataQuality model/enum change. | HIGH |
| `docs/source-research/projects/scipy.md` | Add supported deterministic operation matrix and pin at M5. | Research recommendation only. | Direct dependency; normalize warnings, NaN handling, seeds, and results. | No AnalysisResult/enum change. | HIGH |
| `docs/source-research/projects/statsmodels.md` | Add supported regression result mapping and pin at M5. | Research recommendation only. | Direct dependency; textual Summary is never AnalysisResult. | No analysis contract change. | HIGH |
| `docs/source-research/projects/matplotlib.md` | Add renderer/font/backend pin and artifact metadata at M5. | Research recommendation only. | Direct dependency for deterministic headless rendering. | No Figure model or acceptance threshold change. | HIGH |
| `docs/source-research/projects/dvc.md` | Keep implementation status development-only and document any demo-data use separately. | Research recommendation only. | Provenance/development inspiration; never DatasetVersion authority. | No dataset model or milestone change. | MEDIUM |
| `docs/source-research/projects/great-expectations.md` | Keep implementation status design-reference unless a later ADR changes it. | Research recommendation only. | Reuse concepts/tests selectively; do not run a second P0 quality engine. | No DataQualityRun contract change. | MEDIUM |
| `docs/source-research/projects/python-docx.md` | Add direct-dependency adoption pin and OOXML exception record at M6. | Research recommendation only. | Direct dependency; controlled lxml/OOXML enhancement, immutable original DOCX. | No artifact/export contract change. | HIGH |
| `docs/source-research/projects/csl-styles.md` | Record exact selected styles, rights metadata, locale files, and snapshot hash at adoption. | Minimal snapshot is recommended. | Resource snapshot only; do not copy the full repository by default. | No citation API/Schema change. | HIGH |
| `docs/source-research/projects/citeproc-js.md` | Keep deferred until license/isolation/alternative decision is resolved. | Multiple execution options remain open. | No runtime adoption; simple deterministic fallback or alternative processor remains available. | No citation contract change. | HIGH |
| `docs/source-research/projects/tanstack-table.md` | Add direct-dependency adoption status and feature ownership when frontend work starts. | Research recommendation only. | Headless table for existing workbench views. | No API/UX requirement change. | LOW |
| `docs/source-research/projects/xyflow.md` | Add direct-dependency adoption status and graph-view boundary at M6/M7. | Research recommendation only. | Visualization only; backend evidence graph remains authority. | No evidence graph contract change. | HIGH |
| `docs/source-research/projects/zotero.md` | Keep as design/data-exchange reference and record any format compatibility work separately. | Research recommendation only. | Do not copy desktop AGPL source by default. | No literature model/API change. | HIGH |
| `docs/source-research/projects/zotero-web-library.md` | Keep as UX reference and record independently created patterns rather than copied source. | Research recommendation only. | Design reference; no AGPL source adoption implied. | No frontend contract change. | HIGH |
| `docs/source-research/projects/openai-agents-sdk.md` | Add runtime adoption status, Tool mapping, trace policy, and pin when M8 begins. | Research recommendation only. | Direct dependency for one Orchestrator; Session/Trace remain non-authoritative. | No Tool/Schema/Agent state change. | HIGH |

## 14. ADR set

Phase 6 recommended the following independent decisions. Phase 7 subsequently
created and accepted them without modifying formal product or contract text:

| ADR | Decision scope | Primary files to align after acceptance |
| --- | --- | --- |
| [ADR-002](../decisions/ADR-002-OPEN-SOURCE-INTEGRATION-MODES.md) | Normalized modes, metadata, upgrade, and attribution rules. | Architecture, security, development workflow, notices. |
| [ADR-003](../decisions/ADR-003-LITERATURE-EVIDENCE-STACK.md) | PyAlex, GROBID, PDF.js, pgvector, PaperQA2, ASReview chain and authority boundaries. | Literature requirements/models/API/tests/M2-M3. |
| [ADR-004](../decisions/ADR-004-DATA-STATISTICS-STACK.md) | Pandera, SciPy, statsmodels, Matplotlib, GX, and DVC roles. | Data requirements/models/API/tests/M4-M5. |
| [ADR-005](../decisions/ADR-005-MANUSCRIPT-CITATION-STACK.md) | DOCX, OOXML, CSL resources, processor/isolation decision. | Manuscript requirements/models/API/tests/M6-M7. |
| [ADR-006](../decisions/ADR-006-RESEARCH-WORKBENCH-UX.md) | PDF.js, TanStack Table, React Flow, and Zotero UX reference boundaries. | Frontend architecture, UX, tests/M2-M7. |
| [ADR-007](../decisions/ADR-007-AGENT-WORKFLOW-STACK.md) | Agents SDK runtime and ARS selective Vendor mapping under ADR-001. | Agent architecture, Schemas, Tools, tests/M8. |
| [ADR-008](../decisions/ADR-008-IMPLEMENTATION-METADATA.md) | Machine-readable pins, licenses, copied paths, modifications, fallbacks, and acceptance evidence. | Notices, source research, delivery workflow, release gates. |

## 15. Coverage and execution boundary

This map covers the repository entry files, all current formal child documents, development guidance, backend/frontend/test READMEs, ADR-001, and all current source-research project records. It intentionally does not prescribe edits to historical reports or baseline evidence: those files remain immutable evidence of the decision path.

Phase 6 changed only this map and the master plan. Phase 7 formalized the ADRs
and notice structure. Actual formal-spec alignment, dependency adoption, Vendor
snapshots, source copying, and code changes remain separately reviewed tasks.
