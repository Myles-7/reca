# Open-Source Alignment Phase 9: Data Models and Contracts

Document version: `1.0.0`

Document status: `Conditional Approval`

Last updated: 2026-07-31

## 1. Scope

Phase 9 aligns the data-model and API/AI/Tool contract authorities with the
researched open-source capability stacks. It modifies only:

- `docs/DATA_MODEL_AND_WORKFLOW.md` and `docs/data-model/`;
- `docs/API_AI_TOOL_CONTRACTS.md` and `docs/contracts/`;
- this report.

No code, migration, dependency, lockfile, Compose, CI, test, security, product,
architecture, or roadmap file is changed.

## 2. Existing expression capability

The existing model already covered most reproducibility metadata:

| Required meaning | Existing authority |
| --- | --- |
| engine name/version | `ProcessingRun.engine`, `ProcessingRun.engine_version`, AnalysisRun engine fields |
| configuration hash | `ProcessingRun.parameters_hash`, controlled parameter/resource hashes |
| rule-set version | `DataQualityRun.rule_set_version` |
| Prompt version | Prompt manifest and ModelInvocation Prompt fields |
| Schema version | AI/DTO fields, ModelInvocation and versioned manifests |
| upstream output artifacts | Artifact metadata and ProcessingRun output links |
| model provider/version | ModelInvocation |
| tool wrapper/version | ToolCall |
| statistical environment | AnalysisRun environment snapshot |
| exported dependency inventory | ReproPackage manifest Artifact |

No project-specific table is required for PyAlex, GROBID, PaperQA, ASReview,
Pandera, SciPy, statsmodels, Matplotlib, a citation processor, Agents SDK, or
ARS-Codex.

## 3. Intentional additive data changes

### ProcessingRun implementation metadata

One optional compatible field is proposed:

```text
ProcessingRun.implementation_metadata: JSONB | null
```

It separates implementation provenance from business parameters and is a
strict versioned object covering engine, upstream project/Commit, adopted
release or digest, configuration hash, ruleset, Prompt, Schema, and integration
mode. Existing ToolCall, AgentRun, and domain runs reference this record rather
than duplicating upstream-specific fields.

### Non-persistent normalized payloads

The following are semantic payloads, not new tables or registered AI Schemas:

- `CandidateEvidence`: transported through existing `EvidenceCandidateDTO` and
  stored in ProcessingRun/ToolCall/Artifact outputs until EvidenceSpan validation;
- `ScreeningRecommendation`: advisory rank/score/rationale tied to confirmed
  decisions, never a LiteratureDecision;
- `CitationRenderResult`: rendered citation/bibliography plus style, locale,
  engine and limitation metadata, never source-validity evidence.

### Compatible response and manifest fields

Evidence-search candidates retain the existing nullable `evidence_span_id` and
add candidate ID, Chunk, source hash, retrieval run, and limitations. A value is
only populated after RECA Service validation.

The existing ReproPackage manifest gains versioned sections for runtime
dependencies, service image digests, upstream projects, Vendored assets, Prompt
versions, ruleset versions, statistical engines, citation styles, configuration
hashes, source versions, and Artifact hashes.

## 4. Domain mapping

| Third-party result | RECA authority |
| --- | --- |
| OpenAlex Work | LiteratureRecord candidate/import result |
| GROBID TEI | immutable parsed-document intermediate Artifact + ProcessingRun |
| PaperQA Evidence | CandidateEvidence semantics via EvidenceCandidateDTO |
| ASReview Rank | ScreeningRecommendation payload |
| Pandera Failure | DataQualityIssue |
| SciPy/statsmodels output | AnalysisResult after deterministic normalization |
| Matplotlib output | Figure plus immutable Artifacts |
| citation processor output | CitationRenderResult payload |
| Agents SDK run | implementation mechanics inside AgentRun |
| ARS workflow state | Prompt/Workflow input mapped to existing state and approval objects |

Prohibited substitutions remain explicit: candidate evidence is not
EvidenceSpan, ranking is not LiteratureDecision, textual statsmodels Summary is
not AnalysisResult, citation text is not verified source evidence, SDK
Session/Trace are not project/audit authority, and ARS state is not business
state.

## 5. Provider-neutral API alignment

No API path is added, removed, or renamed. Public resources remain domain-named:
search literature, parse documents, retrieve evidence, run quality checks,
execute analysis, render figures, check manuscripts, and export reproduction
packages.

Existing `provider` and `preferred_parser` request fields remain only as optional
compatibility hints for administrator/test use. Normal clients and models omit
them; Service policy selects the implementation and records actual engine
metadata. No `/run-paperqa`, `/run-asreview`, `/run-grobid-client`, or
`/run-citeproc` endpoint is introduced.

No standalone citation endpoint is added while the full processor and license
decision remains deferred.

## 6. AI Schema coverage

| Needed capability | Existing contract used |
| --- | --- |
| evidence candidate | EvidenceCandidateDTO through `retrieve_evidence` Tool output |
| evidence insufficiency | empty candidates, evidence gaps, missing information, limitations, human review |
| conflicting evidence | controversy items, contradicting literature IDs, counterexamples |
| screening recommendation | strict existing Tool output; not an AI business object |
| ARS Scoping | ResearchQuestionScopingInput/Output |
| Checkpoint | ProjectContextSnapshot + pending approvals/blockers/allowed actions |
| Claim verification | AuditResult |
| workflow mode | current project stage + task type + PromptContract |
| third-party degradation | DegradationRecord |

No registered AI Schema name is added or renamed. Third-party free JSON must be
converted through existing strict output contracts before persistence or Tool
return.

## 7. Tool and approval alignment

All 51 existing Tool names remain unchanged. The contracts now state:

- PaperQA-like implementations only populate evidence candidates;
- ASReview-like implementations only populate ranking recommendations;
- a citation renderer has no source-validity authority and receives no new Tool;
- Agents SDK Function Tools must pass existing wrappers and RECA Services;
- ARS Workflow assets cannot create business state directly.

Approval semantics remain normative and unchanged:

```text
AUTO_ALLOWED
LIGHT_CONFIRMATION
FORMAL_APPROVAL
PROHIBITED
```

Read-only and candidate generation are auto-allowed; adopting low-risk
recommendations uses light confirmation; modifying scientific data or formal
results retains formal ApprovalRecord requirements; prohibited tools stay out
of the whitelist.

## 8. Error and degradation decision

Existing codes cover literature/model Provider failures, parse failure or low
confidence, evidence-location failure, analysis/figure failures, and model
Schema/source failures. Evidence insufficiency and optional screening
unavailability are normally structured successful/degraded outcomes, not
errors.

Two provider-neutral codes are intentionally added because the old set could
not accurately describe citation/Vendor/isolated-service failures or invalid
non-model third-party output:

```text
EXTERNAL_CAPABILITY_UNAVAILABLE
EXTERNAL_OUTPUT_INVALID
```

License-restricted capability availability uses the first code plus a public
DegradationRecord and governance-review flag; it does not expose speculative
legal conclusions. No project-specific error code is added.

## 9. Stable identifier verification

| Type | Baseline | Current | Removed by phase | Added | Renamed | Result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Requirement IDs | 181 | 181 | 0 | 0 | 0 | PASS |
| API paths | 236 | 236 | 0 | 0 | 0 | PASS |
| Error-code candidates | 87 | 89 | 0 | 2 intentional | 0 | PASS |
| Schema names | 16 | 16 | 0 | 0 | 0 | PASS |
| Agent Tool names | 51 | 51 | 0 | 0 | 0 | PASS |
| Enum/value candidates | 401 baseline candidates | 378 present | 0 | 0 | 0 | PASS with pre-existing baseline note |

The 23 enum/value candidates absent from current Markdown are the same
pre-existing conservative-extraction mismatch recorded in the open-source
research baseline. Phase 9 does not delete or rename an enum.

Unexpected removed: `0`

Unexpected renamed: `0`

## 10. Modified files

- `docs/DATA_MODEL_AND_WORKFLOW.md`
- `docs/data-model/FOUNDATION_AND_PROJECT_MODELS.md`
- `docs/data-model/LITERATURE_AND_EVIDENCE_MODELS.md`
- `docs/data-model/DATA_ANALYSIS_AND_FIGURE_MODELS.md`
- `docs/data-model/MANUSCRIPT_AGENT_AND_EXPORT_MODELS.md`
- `docs/data-model/STATE_MACHINES_AND_INVARIANTS.md`
- `docs/API_AI_TOOL_CONTRACTS.md`
- `docs/contracts/COMMON_API_JOB_AND_SSE_CONTRACTS.md`
- `docs/contracts/PROJECT_RESEARCH_AND_LITERATURE_API.md`
- `docs/contracts/DATA_ANALYSIS_AND_FIGURE_API.md`
- `docs/contracts/MANUSCRIPT_EVIDENCE_AND_EXPORT_API.md`
- `docs/contracts/AI_SCHEMA_CONTRACTS.md`
- `docs/contracts/AGENT_TOOL_CONTRACTS.md`
- this report

## 11. No-code-change confirmation

This phase changes Markdown documentation only. It does not implement the
optional field, create a migration, alter OpenAPI, copy third-party content,
install a dependency, create a Vendor directory, modify generated clients, or
claim that a researched integration is already running.
