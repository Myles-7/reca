# Open-Source Research Integration Baseline

Document version: `1.0.0`

Document status: `Conditional Approval`

Last updated: 2026-07-31

## 1. Scope

This report freezes the research, Git, stable-contract and document-impact
baseline for the planned evaluation of 26 mature open-source projects. It does
not select final integrations and does not state that a planned or researched
project is already implemented.

Phase 0 created only this report and the linked evidence directory. It changed
no formal specification, product scope, code, dependency, Compose service, CI
workflow, migration, lock file or third-party content.

Evidence files:

- [Repository catalog](../evidence/open-source-research-evidence/repository-catalog.csv)
- [Document impact map](../evidence/open-source-research-evidence/document-impact-map.csv)
- [Current integration status](../evidence/open-source-research-evidence/current-integration-status.csv)
- [Stable identifiers before research](../evidence/open-source-research-evidence/stable-identifiers-before.txt)
- [Current third-party records](../evidence/open-source-research-evidence/current-third-party-records.txt)
- [Current architecture decisions](../evidence/open-source-research-evidence/current-architecture-decisions.txt)
- [Current roadmap integrations](../evidence/open-source-research-evidence/current-roadmap-integrations.txt)

## 2. Git and governance baseline

| Fact | Value | Result |
| --- | --- | --- |
| Current branch | `docs/document-split-compression` | Recorded |
| Starting HEAD | `849a6972d16ba076becfd8a306717cf222969c4c` | Recorded |
| `main` HEAD | `79825914c7c975e8be256a5a89abe812f486769e` | Matches M0 commit |
| `m0-complete` annotated tag object | `a91f9278db450ef3e52bfbff7af83d866f5feb75` | Recorded |
| `m0-complete^{commit}` | `79825914c7c975e8be256a5a89abe812f486769e` | Matches M0 commit |
| Working tree before Phase 0 | clean | Verified |
| M0 status | `COMPLETED` | Verified |
| M1 Entry | `ALLOWED` | Verified |
| Documentation status | `Conditional Approval` | Preserved |
| Root license | `PENDING_GOVERNANCE_DECISION` | Preserved |

The annotated tag's object ID differs from its peeled commit by design. No tag,
approval status or root-license decision is changed by this phase.

## 3. Current open-source policy

RECA 0.1 is oriented toward personal use and school-competition demonstration.
The current policy is effect-first reuse with minimum safeguards: a mature
project may be used through dependency, independent service, Fork, Vendor,
Submodule, selective copy, research reference or optional clean-room work when
the exact license and source permit it.

Before incorporation, RECA must verify the actual license, fix the upstream
Commit or Tag, retain attribution and required notices, record copied and
modified paths, keep special-license content distinguishable from the future
root license, and re-review when use or distribution changes. A public
repository or ability to Fork is not itself permission. No-license or
unknown-source content must not be copied.

Reuse cannot override RECA's research-trust boundaries: original artifacts are
immutable, formal statistics are deterministic, EvidenceSpan and citations may
not be fabricated, high-risk writes require the applicable confirmation, and
Agents cannot self-approve or execute arbitrary Shell, SQL or Python.

## 4. Repository inventory

The catalog contains all 26 requested repositories.

### 4.1 Actually present in the current repository or runtime foundation

| Project | Current state | Current mode | Important limit |
| --- | --- | --- | --- |
| `fastapi/full-stack-fastapi-template` | Selected files incorporated at fixed Commit | `SELECTIVE_COPY` | Existing provenance and MIT license must remain |
| `grobidOrg/grobid` | Compose service and health evidence | `INDEPENDENT_SERVICE` | M0 healthcheck only; no PDF business parsing |
| `TanStack/table` | Package present | `DIRECT_DEPENDENCY` | M3 matrix feature remains planned |
| `pgvector/pgvector` | Compose image, extension and smoke | `INDEPENDENT_SERVICE` | No completed semantic-search workflow |
| `celery/celery` | Direct dependency and sole worker runtime | `DIRECT_DEPENDENCY` | M0 exposes only `reca.health_ping` |
| `valkey-io/valkey` | Compose broker/cache foundation | `INDEPENDENT_SERVICE` | Infrastructure presence is not business capability |

### 4.2 Planned or explicitly researched, but not implemented

| Project | Current position | Planned boundary |
| --- | --- | --- |
| `openai/openai-agents-python` | One brief architecture row | `PLANNED_M8`; no integration decision yet |
| `J535D165/pyalex` | Named OpenAlex client/source | M2 literature retrieval |
| `mozilla/pdf.js` | Planned rendering/highlighting | M2-M3; cannot determine EvidenceSpan truth |
| `Future-House/paper-qa` | Accepted design reference only | Retrieval-chain research under DEC-006 |
| `unionai-oss/pandera` | Planned deterministic validation | M4 |
| `scipy/scipy` | Planned deterministic statistics | M5 |
| `statsmodels/statsmodels` | Planned deterministic statistics | M5 |
| `matplotlib/matplotlib` | Planned deterministic figures | M5 |
| `python-openxml/python-docx` | Planned DOCX/OOXML processing | M6 |
| `citation-style-language/styles` | Complete CSL remains P1 | No P0 promotion |
| `xyflow/xyflow` | React Flow visualization planned | M7 evidence graph UI |
| `Imbad0202/academic-research-skills-codex` | Conditional research reference | No content copied; runtime requires separate decision |

### 4.3 Not currently named or integrated

The current formal corpus contains no project-specific integration decision for:

- `grobidOrg/grobid-client-python`;
- `asreview/asreview` (active learning exists only as a generic P1 capability);
- `Juris-M/citeproc-js`;
- `pgvector/pgvector-python`;
- `iterative/dvc`;
- `great-expectations/great_expectations`;
- `zotero/zotero`;
- `zotero/web-library`.

Absence is not a rejection. It means a later research phase must establish the
license, fit, integration mode, maintenance cost and contract impact before any
implementation claim.

## 5. Document mention and impact summary

The detailed per-project map is in
[document-impact-map.csv](../evidence/open-source-research-evidence/document-impact-map.csv).
Current mentions cluster as follows:

| Area | Principal documents | Main contract sensitivity |
| --- | --- | --- |
| Engineering foundation | `README.md`, `AGENTS.md`, Architecture, M0 reports, notices | M0 As-Built, unique Celery App, infrastructure status |
| Literature and PDF | Product, Architecture, M2-M3 roadmap, literature API/models | ResearchQuestion, LiteratureRecord, Document, EvidenceSpan, Job |
| Data and statistics | Product, Architecture, M4-M5 roadmap, analysis contracts | DatasetVersion, AnalysisPlan, deterministic results, Figure |
| Manuscript and citation | Product, M6 roadmap, manuscript contracts | ClaimEvidenceLink, MANU-P0-018, Export, citation scope |
| Frontend and UX | Architecture components, frontend rules, M3/M7 | Generated client boundary, evidence visualization only |
| Agent and workflow | Architecture, M8, AI Schema, Tool contracts, ADR-001 | Single orchestrator, Tool names, data access, approvals |

## 6. Conflicts and unclear points

### 6.1 PaperQA restriction versus effect-first policy

DEC-006 currently says PaperQA is researched for retrieval-chain ideas and is
not integrated wholesale as a runtime dependency. The newer governance policy
allows effect-first reuse when license, coupling and maintenance support it.
This is not an immediate contradiction because DEC-006 is a project-specific
accepted architecture decision, but later research should re-evaluate it rather
than treating the old restriction as permanent or silently overriding it.

### 6.2 ASReview remains unnamed and P1-only in substance

Active-learning literature screening remains P1. ASReview is not named in the
current formal corpus. Evaluation must not promote the capability into P0 or
change existing requirement IDs.

### 6.3 Citation stack lacks an isolation decision

Complete CSL and multiple citation formats remain P1. CSL styles are mentioned
conceptually, while `citeproc-js` is absent. Later research must distinguish
style data, citation processor runtime, JavaScript execution boundary, license
obligations and packaging. No legal or architecture conclusion is made here.

### 6.4 OpenAI Agents SDK is under-specified

The SDK currently has only a `PLANNED_M8` architecture mention. There is no
fixed version, license record, dependency/service/Adapter choice, Tool mapping,
ProjectContextSnapshot boundary, offline behavior or degradation decision.
Adoption cannot be inferred from the stack row.

### 6.5 ARS-Codex is conditionally reusable but not selected for incorporation

ADR-001 and the source record already identify reusable Prompt, workflow,
schema, script and test categories. The unresolved gap is more concrete: no
actual copied paths, Fork/Vendor selection, incorporation PR, runtime component
or implementation milestone has been chosen. Current mode remains
`RESEARCH_REFERENCE`, and this task copies no ARS-Codex content.

### 6.6 Pandera and Great Expectations could duplicate runtime truth

Pandera is planned for M4; Great Expectations is absent. Running both without a
clear division could create duplicate validation rules, conflicting reports and
two maintenance surfaces. Research must select complementary roles or one
runtime authority while retaining RECA's DataQualityRun and issue contracts.

### 6.7 DVC must not replace RECA domain versioning

DVC is absent. It may be researched for development data or reproducibility,
but it cannot silently replace `DatasetVersion`, Artifact relations, approval,
project isolation or database-owned lineage.

### 6.8 Zotero source reuse needs a license boundary

Zotero and Zotero Web Library are absent. Any Fork, Vendor or selective source
copy requires exact upstream and file-level license review and an explicit
distribution boundary. This report does not infer a legal result from public
availability or commonly associated project licenses.

### 6.9 Adapter wording needs project-specific review

The current global policy no longer requires every third-party capability to use
a complex Adapter. Some child documents still prescribe adapters for specific
capabilities, including OpenAlex/GROBID/pypdf, Matplotlib and object storage.
Those may be valid boundaries for object conversion, mocking, security or
testing; they are not evidence of a remaining global absolute rule. Later
research should keep only adapters with a concrete benefit.

## 7. Potential stable-contract impact

No stable contract changes are authorized in Phase 0. Later research must treat
the following as impact zones, not invitations to rename contracts:

| Candidate group | Potentially affected contract types |
| --- | --- |
| Literature/PDF projects | Requirement IDs, literature API paths, Document/Evidence schemas, parsing enums |
| Data/statistics projects | Dataset and Analysis schemas, deterministic-result enums, M4-M5 milestones |
| Manuscript/citation projects | Claim/Audit/Export schemas, MANU-P0-018, M6 and P1 boundaries |
| Agent/workflow projects | AI Schema names, Agent Tool names, data-access enums, M8 |
| Foundation projects | Job/SSE behavior, health contracts, M0 regression evidence |
| Frontend projects | No server contract change unless an explicit later design requires one |

Projects with the highest contract sensitivity are OpenAI Agents SDK, GROBID
and its client, PyAlex, PDF.js, PaperQA, Pandera, SciPy/statsmodels, Matplotlib,
python-docx and ARS-Codex.

## 8. Stable identifier verification

The current formal corpus was compared with the existing document-split
baseline. Details are frozen in
[stable-identifiers-before.txt](../evidence/open-source-research-evidence/stable-identifiers-before.txt).

| Type | Baseline | Present | Unexpected removed | Unexpected renamed | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| Requirement IDs | 181 | 181 | 0 | 0 | PASS |
| Acceptance IDs | 16 | 16 | 0 | 0 | PASS |
| API paths | 236 | 236 | 0 | 0 | PASS |
| Error-code candidates | 87 | 87 | 0 | 0 | PASS |
| Schema names | 16 | 16 | 0 | 0 | PASS |
| Agent Tool names | 51 | 51 | 0 | 0 | PASS |
| Milestone IDs/tokens | 20 | 20 | 0 | 0 | PASS |
| ADR IDs | 1 | 1 | 0 | 0 | PASS |
| M0 Issue IDs | 4 | 4 | 0 | 0 | PASS |
| Enum/value candidates | 401 | 378 | 0 caused by Phase 0 | 0 | CONDITIONAL |

The 23 unmatched enum/value candidates are a pre-existing conservative
extraction mismatch at the starting HEAD. They are mostly Settings, environment
or governance tokens, not a detected deletion by this phase. They remain
unresolved rather than being restored artificially into formal documents.

## 9. Core contracts that must remain unchanged

- M0 is `COMPLETED`, and M1 Entry is `ALLOWED`.
- The M0 commit is `79825914c7c975e8be256a5a89abe812f486769e`.
- The six required CI checks and clean-room gate remain mandatory.
- The two accepted M0 LOW risks remain recorded.
- Documentation remains `Conditional Approval`.
- Root license remains `PENDING_GOVERNANCE_DECISION`.
- Original PDF, dataset and DOCX artifacts remain immutable.
- Formal statistical values come only from deterministic programs.
- EvidenceSpan absence is not represented by fabricated evidence.
- ResearchQuestion and AI Scoping state semantics remain separate.
- `requested_data_access_level`, `max_allowed_data_access_level` and
  `effective_data_access_level` remain distinct.
- ProjectContextSnapshot remains minimal, read-only and regenerable.
- ApprovalRecord remains required for applicable high-risk actions, not every
  read or low-risk candidate generation.
- MANU-P0-018 retains its Competition Core/P0-Full boundary.
- The controlled single orchestrator Agent remains scheduled for M8.
- Prompt manifests remain Git-managed.
- API paths, Error Codes, Schema names, Tool names, Enums, Milestones, ADR IDs
  and M0 Issue IDs cannot be changed accidentally by integration research.

## 10. Later research stages

Phase 1 should verify repository identity, fixed Commit/Tag, actual license text,
maintenance activity, release model and reusable asset surface for each project.

Phase 2 should compare technical fit and integration modes by research group,
including direct dependency versus service versus Adapter, duplicated runtime
responsibilities, offline/demo behavior and removal cost.

Phase 3 should produce project-specific recommendations using only:
`DIRECT_DEPENDENCY`, `INDEPENDENT_SERVICE`, `ADAPTER_INTEGRATION`, `FORK`,
`VENDOR`, `GIT_SUBMODULE`, `SELECTIVE_COPY`, `DESIGN_REFERENCE`, `DEFERRED` or
`DO_NOT_USE`.

Any later implementation phase must update source research and attribution in
the same PR as actual incorporation. It must not describe a project as present
until the dependency, service or copied content exists in the repository.

## 11. Baseline outcome

Phase 0 is a `CONDITIONAL PASS`. The Git and core stable-contract baselines are
frozen, all 26 repositories are catalogued, and current implementation claims
are separated from plans. The condition is limited to unresolved future
license/integration choices and the pre-existing 23-token enum/value extraction
mismatch; neither condition was introduced by this phase.

## 12. No-code-change confirmation

No backend, frontend, test implementation, dependency, Compose configuration,
CI workflow, Alembic migration, generated client, lock file, Vendor content or
third-party source was modified or added. The allowed modification scope is
only `docs/reports/OPEN_SOURCE_RESEARCH_BASELINE.md` and
`docs/reports/open-source-research-evidence/`.
