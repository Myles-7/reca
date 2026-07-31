# Open-Source Integration Master Plan

Document version: `1.0.0`

Document status: `Conditional Approval`

Last updated: 2026-07-31

Document alignment: [Open-source document alignment map](../reports/OPEN_SOURCE_DOCUMENT_ALIGNMENT_MAP.md)

## 1. Scope

This plan consolidates RECA open-source research Phases 0-5 into one project-level
integration decision. It selects integration modes, capability stacks, authority
boundaries, fallbacks, milestone placement and acceptance expectations for all
26 researched repositories.

It does not install a dependency, change a container image, copy upstream code or
assets, create a Vendor/Submodule/Fork, amend a formal contract, create an ADR,
or claim that a researched capability is implemented.

The plan preserves:

- M0 `COMPLETED` and M1 Entry `ALLOWED`;
- documentation status `Conditional Approval`;
- root license `PENDING_GOVERNANCE_DECISION`;
- immutable original PDF, dataset and DOCX Artifacts;
- database-owned project, version, approval and audit state;
- deterministic formal statistics and rendering inputs;
- validated EvidenceSpan rather than generated evidence;
- one controlled `ResearchOrchestrator` at M8;
- Git-managed Prompt manifests established from M1;
- existing Requirement, Acceptance, API, Error, Schema, Tool, Enum, Milestone,
  ADR and M0 Issue identifiers.

## 2. Decision vocabulary

The `Recommended mode` column uses only the following project-level modes:

```text
ALREADY_INTERNALIZED_BASELINE
DIRECT_DEPENDENCY
DIRECT_DEPENDENCY_WITH_PROVIDER
ADAPTER_INTEGRATION
INDEPENDENT_SERVICE
ISOLATED_SERVICE
SELECTIVE_VENDOR
FULL_VENDOR
FORK
GIT_SUBMODULE
RESOURCE_SNAPSHOT
DESIGN_REFERENCE
DEVELOPMENT_ONLY
DEFERRED
DO_NOT_USE
```

`DIRECT_DEPENDENCY_WITH_PROVIDER` means the package is used directly inside a
narrow RECA-owned provider/repository boundary. `SELECTIVE_VENDOR` means exact
upstream paths may be copied only after license, attribution, modification and
golden-test review. `RESOURCE_SNAPSHOT` is for pinned non-code resources such as
selected CSL files. These labels are research governance terms, not new domain
Enums or API values.

## 3. Project decision matrix

| Project | Fixed Commit | License | RECA capability | Recommended mode | Milestone | Runtime | Source of Truth | Fallback | Acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Full Stack FastAPI Template | `546f18469c30fb1748da21f044189f2f83639ea6` research; RECA import `c9e70d65c74f7adda417fc8de0757207ff77514c` | MIT | FastAPI/SQLModel/Alembic, React shell, auth, generated client and test foundation | `ALREADY_INTERNALIZED_BASELINE` | M0 maintenance | Already selectively internalized | RECA repository, migrations and accepted M0 behavior | Keep current specialized tree; selectively backport small upstream fixes | No whole-tree overwrite; six required CI and clean-room pass; provenance retained |
| Celery | `7c5d9a62d90c685bd0e1ae002d66ae40980b2847` | BSD-3-Clause code; CC BY-SA 4.0 docs | Sole asynchronous Worker runtime, retry and dispatch mechanics | `DIRECT_DEPENDENCY` | M0 foundation; M1-M8 tasks | Existing `5.5.3`; later behavior planned | PostgreSQL `Job` and `ProcessingRun` | Synchronous/degraded execution for bounded flows; database redispatch | Idempotent duplicate delivery, crash/retry/cancel tests; Celery states never become business state |
| Valkey | `0bf28b2dab6d21ea278fbaf1517b45e55d9b9c6f` | BSD-3-Clause root plus file-level licenses | Celery broker/result support, regenerable cache, bounded lock and ephemeral event hints | `INDEPENDENT_SERVICE` | M0 foundation; M1+ support | Existing stable Compose service | PostgreSQL and immutable Artifacts | Cache miss/recompute; database-based task recovery | Restart/AOF, TTL, namespace, memory pressure and Celery compatibility tests |
| pgvector | `4f3d17f6f74fe98adf54df4d016de241eeaae9af` | PostgreSQL License | Project-scoped exact vector retrieval and later measured ANN | `INDEPENDENT_SERVICE` | M0 smoke; M2-M3 retrieval | Existing PostgreSQL extension; business tables planned | PostgreSQL objects, source versions and embedding lineage | Exact SQL/text filtering; no separate vector database | Migration, exact ranking, dimension/model lineage and cross-project negative tests |
| pgvector-python | `60739dfd6cb9d674f32afa4184d43e6aff9dfbcf` | MIT | SQLModel/SQLAlchemy vector type and distance expressions | `DIRECT_DEPENDENCY` | M2 introduction; M3 query use | Planned | RECA repositories and PostgreSQL | Raw reviewed SQL/driver registration inside repository layer | Alembic, Python/SQLModel/Psycopg/server compatibility and no contract leakage |
| PyAlex | `875c708cbb6e449feebc46d2a7a26af8ed8b2fdd` | MIT | OpenAlex search, filtering, cursor pagination and raw provenance | `DIRECT_DEPENDENCY_WITH_PROVIDER` | M2 | Planned | RECA `QueryPlan`, search run and normalized `LiteratureRecord` candidates | Direct recorded HTTP provider or offline fixture replay | Recorded/offline tests, bounded retry, DOI/author normalization and no PyAlex objects outside provider |
| GROBID | `c3229a4b9ba1e9eb8ec8327c2ec9eed1581d410c` | Apache-2.0 | Scholarly PDF header/full-text/reference TEI parsing | `INDEPENDENT_SERVICE` | M2 parsing; M3 evidence validation | M0 health only; formal parsing planned | Immutable PDF/TEI Artifacts and RECA converter objects | Explicit pypdf degraded parser path | Pinned image/digest, resource/error corpus, raw TEI retention, page validation and visible degradation |
| grobid-client-python | `161e0f45189c8592b2e2c58e9638cc6218bc75fb` | Apache-2.0 | GROBID transport, request options, bounded concurrency and `503` handling | `SELECTIVE_VENDOR` | M2 | Not present | RECA Worker Job, Artifact and client interface | Small RECA-owned `httpx` client | Client versus direct transport spike; no filesystem/batch ownership; license/path ledger |
| PDF.js | `a80897dc9a2eb80c474717b683a4153f5b628ac7` | Apache-2.0 | PDF display, TextLayer, AnnotationLayer, navigation and highlight interaction | `DIRECT_DEPENDENCY` | M2 viewer; M3 validated selection | Planned | Backend Document/Evidence APIs and immutable PDF | Basic page image/text display with reduced interaction | Package/worker pairing, authorized range loading, coordinate round-trip and stale-version rejection |
| PaperQA2 | `d7675d7b7eddeb3535e8c260399c5bbeeb818c50` | Apache-2.0 | Evidence ranking, summary, packing, citation constraints and no-evidence tests | `SELECTIVE_VENDOR` | M3 evidence enhancement; selected Prompt use at M8 | No full runtime | RECA DocumentChunk, pgvector, evidence validator and user workflow | Native retrieval plus bounded deterministic packing | Every candidate resolves to exact page text; no/conflict evidence cases; no duplicate index/project/Agent state |
| ASReview | `d3e863c94e1945ace7848b6ca5bcf2fb1eecbdb5` | Apache-2.0 | Read-only active-learning literature prioritization | `DIRECT_DEPENDENCY_WITH_PROVIDER` | M3 spike; optional post-M3 enhancement | Planned only if spike passes | User-confirmed `LiteratureDecision` | Manual/simple deterministic screening order | Train only on confirmed labels; reproducible seed/model; zero write path to decisions |
| Pandera | `85cc2a16b2110d4c4b8cc7f956aab94bc53716f6` | MIT | Sole P0 dataframe schema and quality validation runtime | `DIRECT_DEPENDENCY` | M4 | Planned | RECA rule set, DatasetVersion, DataQualityRun and issues | RECA preflight checks with explicit degraded report | Lazy failure normalization, bounded samples, performance and immutable-input tests |
| SciPy | `420a778219f6db170f0fda8dcda4add8a32fd1d6` | BSD-3-Clause plus bundled licenses | Correlation, comparison and assumption checks | `DIRECT_DEPENDENCY` | M5 | Planned | Approved AnalysisPlan and immutable AnalysisResult | Explicit unsupported-method or validation failure; no model calculation | Independent golden values, NaN/effective-N/warning policies and exact Worker compatibility |
| statsmodels | `d3187f844d196de1760829820a7c872a6d6ebb1d` | BSD-3-Clause | Simple linear regression and selected diagnostics | `DIRECT_DEPENDENCY` | M5 P0-Full | Planned | Approved AnalysisPlan and normalized AnalysisResult | Defer regression while retaining descriptive/correlation flow | Golden coefficients/CI/rows, explicit missing policy and no Summary parsing |
| Matplotlib | `faf5d100aed23d3271245c2e800ea47f86dd858b` | Matplotlib license plus bundled licenses/fonts | Deterministic fixed-template PNG/SVG/PDF rendering | `DIRECT_DEPENDENCY` | M5 | Planned | AnalysisResult, Figure manifest and generated Artifacts | Data table plus downloadable results without figure | Five template goldens, headless rendering, CJK font/license, metadata/hash and value equality |
| DVC | `f74c1c0e709de61f571905802bc0c75035dc6ef2` | Apache-2.0 | Optional curated demo/golden dataset provenance and design ideas | `DEVELOPMENT_ONLY` | Optional M4-M5 fixtures; M7 provenance inspiration | Not application runtime | RECA DatasetVersion, Artifact lineage and ReproPackage | Git/object-storage fixture process without DVC | Only adopt after measured fixture need; DVC loss/removal cannot affect RECA lineage |
| Great Expectations | `33614cd70a407f8b9589fa2cf5f1cb1d7d0723aa` | Apache-2.0 | Validation taxonomy, report UX, wording and test design | `DESIGN_REFERENCE` | M4 | No runtime | Pandera-backed RECA DataQualityRun | RECA-owned report design | Demonstrate report value without GX runtime; no second validation authority |
| python-docx | `e45454602b53e8e572b179ccf1c91093ec9f4ed7` | MIT | DOCX traversal, common editing, styles, relationships, comments and derived files | `DIRECT_DEPENDENCY` | M6; M7 lineage | Planned | Immutable DOCX Artifact, ManuscriptVersion and approval | Read-only inspection or export without automated fix | Golden OOXML corpus, original hash unchanged, derived version lineage and office-reader round-trip |
| CSL Styles | `1de508b010b2643c8b13b082947f1054bc33357f` | CC BY-SA 3.0 per repository/selected `<rights>` | Pinned GB/T/APA style resources for validation and later rendering | `RESOURCE_SNAPSHOT` | M3/M6; broader P1 | No files copied yet | RECA normalized reference metadata and citation manifest | Simple deterministic basic GB/T template | Per-file Commit/hash/rights/authors, locale compatibility and golden render |
| citeproc-js | `cc9153c45293af878de08cafddbefe6ea150c380` | CPAL-1.0 or AGPL-3.0-or-later text; package identifier conflict unresolved | Full CSL citation/bibliography processor | `DEFERRED` | P1 processor decision | Not present | RECA references, style/locale/processor manifest | Simple deterministic P0 formatter; research permissive alternatives | No adoption before license/alternative ADR; full citation goldens and source/attribution plan |
| TanStack Table | `d66b39f01e23eeb4e2befc7777194104967212d3` research; stable v8 selected | MIT | Dense literature, quality, analysis, manuscript and approval workbenches | `DIRECT_DEPENDENCY` | M2-M7 | Stable v8 planned/present according to baseline; feature use planned | Backend APIs and durable domain objects | Simple paginated lists | Stable row IDs, server sort/filter/page, accessibility, failure state and no selection-as-decision |
| xyflow / React Flow | `360f5b13e2bc6899ea06b4be1a49b068d86926cf` | MIT | Evidence graph visualization and navigation | `DIRECT_DEPENDENCY` | M7 | Planned | Backend evidence graph and ClaimEvidenceLink | Table/tree evidence-chain view | Authorized projection, stale/denied edges, large-graph and no client-edge authority tests |
| Zotero | `4ec5ba9c279841b09231db82a61e30bd9e7dc6ef` | AGPL-3.0 plus third-party notices | Bibliographic exchange and mature library UX concepts | `DESIGN_REFERENCE` | Optional M2-M3 enhancement | No runtime/source copy | RECA LiteratureRecord, Artifact and project workflow | RIS/BibTeX/CSL JSON import/export without Zotero runtime | Licensed round-trip fixtures, deterministic normalization and no Zotero IDs/state in contracts |
| Zotero Web Library | `556d0bf6b1b48fa8402a91afa62b15533b713013` | AGPL-3.0 | Collection/list/detail and responsive workbench UX reference | `DESIGN_REFERENCE` | M2-M3 UX | No source/assets copied | RECA frontend plus backend APIs | RECA-native table/detail layout | Independent implementation, desktop/mobile/accessibility tests and no AGPL source/asset copy |
| OpenAI Agents SDK | `0ffa36840cb812488738f6fc5be3d3a1f51397b7` | MIT | Controlled Agent Runner, Function Tools, structured output, HITL and usage | `DIRECT_DEPENDENCY` | M8 | Planned | RECA Project, StageResolver, Prompt manifest, Tool contracts and audit records | Existing direct model/provider tasks; manual workflow | One Orchestrator, no P0 handoff/shell, approval resume, trace minimization and AgentRun/ToolCall/ModelInvocation audit |
| ARS-Codex | `f8d6b061efe98564a3f554c917fce66dcef6ca54` | CC BY-NC 4.0; file/upstream review required | Scoping, research, claim verification, revision, Prompt and golden-test assets | `SELECTIVE_VENDOR` | M1+ assets; M2-M8 feature mapping | Research reference only until exact paths approved | RECA database/project/evidence/approval/Tool state | RECA-native Prompts/workflows; clean-room remains optional | `NONCOMMERCIAL_INTENT_DECLARED`, path-level license/attribution, quality delta, no free multi-Agent or state takeover |

## 4. Engineering Foundation Stack

```text
Full Stack FastAPI Template specialized baseline
-> FastAPI / SQLModel / Alembic / React foundation

PostgreSQL + pgvector
-> authoritative relational state + exact project-scoped vector retrieval

pgvector-python
-> infrastructure-only ORM/vector expressions

Celery
-> asynchronous execution mechanics

Valkey
-> broker, short-lived result/cache/lock support
```

Decisions:

- do not regenerate RECA from the template;
- keep one Celery App and database-owned Job/ProcessingRun;
- keep one internal stable Valkey service, never business truth;
- keep pgvector inside PostgreSQL rather than add a vector microservice;
- use exact search first and add HNSW only after a measured threshold;
- keep pgvector-python objects below repository boundaries.

## 5. Literature and Evidence Stack

```text
QueryPlan
-> PyAlex/OpenAlex provider
-> LiteratureRecord candidates
-> immutable PDF Artifact
-> GROBID service
-> raw TEI Artifact
-> RECA TEI converter
-> DocumentPage / DocumentChunk / LiteratureReference candidates
-> pgvector exact project-scoped retrieval
-> selected PaperQA evidence ranking/packing
-> candidate evidence
-> deterministic page/text/version validation
-> EvidenceSpan or explicit absence
-> optional ASReview ranking
-> user LiteratureDecision
```

PDF.js provides display, navigation and interaction over authorized bytes. It is
not part of evidence truth. The grobid-client choice is deliberately narrow:
selectively Vendor only the transport/concurrency behavior if it beats a small
RECA-owned HTTP client in the M2 spike.

PaperQA2 is not installed wholesale. Its selected Prompts, packing helpers and
tests improve existing retrieval, consensus, disagreement and insufficient-
evidence behavior. ASReview is optional read-only prioritization trained only on
confirmed decisions.

## 6. Data and Statistics Stack

```text
immutable DatasetVersion
-> RECA versioned quality rules
-> Pandera
-> DataQualityRun / DataQualityIssue
-> approved CleaningPlan
-> new DatasetVersion
-> approved AnalysisPlan
-> SciPy / statsmodels deterministic computation
-> AnalysisResult
-> Matplotlib fixed template
-> Figure code + rendered Artifacts
```

Great Expectations remains a report/test design reference and cannot operate as
a second P0 validation authority. DVC remains optional development tooling and
provenance inspiration; it never participates in application state transitions.

## 7. Manuscript and Citation Stack

```text
immutable DOCX Artifact
-> python-docx high-level model
-> lxml-backed controlled OOXML enhancement where necessary
-> ManuscriptIssue / MANU-P0-018 checks
-> approved transformation on a working copy
-> new DOCX Artifact + ManuscriptVersion

normalized references
-> simple deterministic P0 GB/T formatter
-> selected CSL style/locale resource snapshots for validation and P1
-> full CSL processor only after separate processor/license decision
```

`lxml` is already a python-docx runtime dependency and may be explicitly pinned
when RECA directly uses its OOXML APIs. It is a supporting dependency, not a
separately researched project decision in this matrix.

citeproc-js remains deferred. If full CSL becomes necessary, compare a
permissively licensed alternative first. If citeproc-js is still selected, use
an isolated Node worker/service boundary, but do not claim isolation removes
CPAL/AGPL obligations.

## 8. Research Workbench Frontend Stack

```text
TanStack Table stable v8
-> dense list/matrix workbenches

@xyflow/react
-> authorized evidence-graph projection

Zotero and Zotero Web Library
-> UX/data-exchange references only
```

RECA independently implements collection/list/detail, filtering, progressive
disclosure and responsive drill-down patterns. No Zotero desktop/Web source,
SCSS, icons, reducers, fixtures or branding are copied by this plan.

## 9. Agent and Workflow Stack

```text
M1 Git-managed RECA Prompt manifest
+ existing AI Schemas
+ existing Tool contracts
+ requested/max/effective data-access policy

M2-M7 deterministic Services and evidence/state rules

M8 OpenAI Agents SDK
-> one ResearchOrchestrator
-> existing Function Tool wrappers
-> structured output, HITL and usage mechanics

selected ARS-Codex assets
-> adapted Prompt/workflow/test inputs
-> RECA Project, Approval, Evidence and Tool semantics
```

The SDK owns mechanics inside a run. RECA owns durable state, authorization,
scientific truth, approval and audit. ARS-Codex supplies selected assets, not an
alternative workflow database or free multi-Agent runtime.

## 10. Prohibited substitutions

| Prohibited substitution | Required interpretation |
| --- | --- |
| PaperQA candidate evidence `!=` EvidenceSpan | Candidate must resolve to immutable source page/text/version or remain absent |
| ASReview ranking `!=` LiteratureDecision | Ranking is advisory; only the user/RECA workflow creates the decision |
| DVC state `!=` DatasetVersion | DVC may assist development; database and Artifact lineage own formal versions |
| Great Expectations result `!=` RECA DataQualityRun | GX is design reference; Pandera result is normalized into RECA-owned runs/issues |
| statsmodels Summary `!=` AnalysisResult | Persist documented numerical attributes and provenance, never parse summary text |
| citeproc output `!=` verified citation source | Processor formats supplied metadata; it does not prove source truth or evidence |
| React Flow graph `!=` evidence graph authority | Backend ClaimEvidenceLink graph is authoritative; UI nodes/edges are projections |
| Agents SDK Session `!=` ResearchProject | Session is conversation continuity only |
| Agents SDK Trace `!=` AuditLog | Trace is telemetry; RECA audit records remain authoritative |
| ARS workflow state `!=` RECA business state | Material Passport/checkpoints/roles must map to database state and policy |

Additional boundaries:

- Celery state `!=` Job/ProcessingRun state;
- Valkey cache/result `!=` durable business result;
- GROBID TEI `!=` validated Document/Evidence truth;
- PDF.js DOM coordinates `!=` EvidenceSpan coordinates;
- pgvector similarity `!=` evidence validity;
- Pandera objects `!=` API/database contracts;
- Matplotlib output `!=` an independent statistical calculation;
- TanStack selection `!=` approval or literature decision;
- Zotero related item `!=` ClaimEvidenceLink.

## 11. Competition scope mapping

No new Requirement ID is introduced. The integrations implement or enhance
existing requirements through the following classifications.

| Capability slice | Classification | Existing-scope interpretation |
| --- | --- | --- |
| Specialized M0 FastAPI/React/auth/generated-client foundation | `COMPETITION_CORE` | Existing M0 baseline, not a new product capability |
| Database-owned Celery jobs and Valkey-backed delivery support | `COMPETITION_CORE` | Required execution support for existing milestone workflows |
| Exact project-scoped pgvector retrieval | `COMPETITION_CORE` | Existing evidence retrieval/search behavior |
| PyAlex OpenAlex search and normalization | `COMPETITION_CORE` | Existing literature retrieval requirement |
| GROBID parsing plus explicit fallback | `COMPETITION_CORE` | Existing PDF parsing/extraction requirement |
| PDF.js viewer and validated highlight interaction | `COMPETITION_CORE` | Existing PDF/evidence workbench requirement |
| PaperQA selected evidence packing and no/conflict-evidence handling | `P0_FULL` | Enhances existing retrieval, consensus, dispute and insufficiency requirements |
| ASReview active-learning prioritization | `OPTIONAL_ENHANCEMENT` | Enhances existing REVIEW-P0 recommendation/screening behavior; manual fallback remains |
| Pandera quality validation | `COMPETITION_CORE` | Existing data-quality requirement |
| SciPy Pearson/Spearman | `COMPETITION_CORE` | Existing P0-Must deterministic analysis |
| SciPy comparisons and statsmodels regression | `P0_FULL` | Existing P0-Full method coverage |
| Matplotlib scatter/group templates | `COMPETITION_CORE` | Existing P0-Must figure output |
| Matplotlib histogram/box/correlation matrix | `P0_FULL` | Existing P0-Full figure coverage |
| Great Expectations report/test ideas | `OPTIONAL_ENHANCEMENT` | Implementation/UX quality only; no runtime authority |
| DVC development provenance | `OPTIONAL_ENHANCEMENT` | Development and reproducibility inspiration only |
| python-docx and controlled OOXML checks | `COMPETITION_CORE` | Existing manuscript checks and MANU-P0-018 inputs |
| Simple deterministic GB/T citation path | `COMPETITION_CORE` | Existing citation export/check requirement |
| Selected CSL styles and broader rendering | `P0_FULL` | Existing citation-format depth; does not add a new requirement |
| citeproc-js/full CSL processor | `DEFERRED` | P1 processor/license decision |
| TanStack research workbenches | `COMPETITION_CORE` | Existing dense list/matrix UX |
| React Flow evidence visualization | `COMPETITION_CORE` | Existing evidence graph view; backend remains authority |
| Zotero exchange/UX patterns | `OPTIONAL_ENHANCEMENT` | Format compatibility and UX only |
| OpenAI Agents SDK single Orchestrator | `COMPETITION_CORE` | Existing M8 Agent requirement |
| ARS Scoping, claim verification and selected golden assets | `P0_FULL` | Enhances existing RQ, AGENT and AGOV requirements without new IDs |
| ARS full workflow snapshot/runtime | `DEFERRED` | Requires measured benefit, license review and separate architecture decision |

## 12. Milestone integration sequence

### M1

- preserve the specialized foundation and implement database-owned Job behavior;
- establish Prompt manifest, ModelInvocation and model data-access governance;
- define package/image/resource/source metadata records used by all later PRs;
- do not deploy the formal Agent runtime.

### M2

- PyAlex provider and recorded/offline normalization;
- pinned GROBID service, selected transport and RECA TEI converter;
- PDF.js authorized viewer;
- pgvector-python introduction only when embedding persistence starts;
- first ARS Scoping asset spike as a PromptContract candidate, not an Agent.

### M3

- exact project-scoped vector retrieval;
- EvidenceSpan validation and PDF highlight round-trip;
- selected PaperQA evidence packing/golden cases;
- optional ASReview ranking spike under existing screening scope;
- TanStack literature/evidence workbench.

### M4

- Pandera as the sole runtime validation engine;
- GX-inspired report structure without GX runtime;
- optional DVC evaluation only if fixture management has a measured problem.

### M5

- pinned compatible SciPy/statsmodels/Matplotlib stack;
- deterministic golden values, warnings and rendering;
- no user/model-selected arbitrary Python execution.

### M6-M7

- python-docx/lxml controlled DOCX processing and immutable derived versions;
- simple deterministic citation formatter and selected CSL resource validation;
- selected ARS claim-verification/revision assets;
- TanStack issue/approval workbenches and React Flow graph projection;
- citeproc-js remains deferred unless an ADR resolves the processor choice.

### M8

- install the pinned OpenAI Agents SDK after M1-M7 gates;
- run one Orchestrator with existing Tool names and Service wrappers;
- integrate selected ARS Prompt/workflow assets only through RECA contracts;
- no P0 handoffs, arbitrary execution, Session authority or Trace authority.

### M9

- validate offline/recorded fallbacks, attribution completeness, dependency/image
  pins, degradation behavior, reproducibility and full Competition Core E2E.

## 13. Implementation metadata requirement

Every adoption PR must record, as applicable:

```text
project_name
repository
research_commit
adopted_release_or_digest
license
license_file_path
integration_mode
adopted_paths_or_package
modified_paths
modification_summary
attribution_location
special_restrictions
source_of_truth
fallback
acceptance_tests
commercialization_review_required
reviewed_by
reviewed_at
```

The research Commit is evidence, not automatically the version to install. The
implementation PR must pin a compatible released package/image/resource and
explain any difference from the research snapshot.

## 14. Proposed ADR sequence

These ADRs are proposed but are **not created or accepted by this phase**:

| Proposed ADR | Purpose | Depends on |
| --- | --- | --- |
| `ADR-002-OPEN-SOURCE-INTEGRATION-MODES.md` | Normalize package/service/provider/Vendor/resource/reference modes and metadata requirements | Master plan |
| `ADR-003-LITERATURE-EVIDENCE-STACK.md` | Select PyAlex, GROBID/client, PDF.js, pgvector, PaperQA asset and ASReview boundaries | M2/M3 spikes |
| `ADR-004-DATA-STATISTICS-STACK.md` | Select Pandera as sole validator and pin deterministic numerical/rendering boundaries | M4/M5 compatibility spikes |
| `ADR-005-MANUSCRIPT-CITATION-STACK.md` | Select python-docx/lxml, basic GB/T path, CSL resources and full processor decision | DOCX/citation goldens and license comparison |
| `ADR-006-RESEARCH-WORKBENCH-UX.md` | Select TanStack/React Flow and independent Zotero-inspired UX boundaries | Frontend prototypes |
| `ADR-007-AGENT-WORKFLOW-STACK.md` | Select OpenAI Agents SDK single-Orchestrator integration and exact ARS assets | M8 SDK and ARS quality spikes |
| `ADR-008-IMPLEMENTATION-METADATA.md` | Define machine-readable source/version/license/modification/fallback/acceptance records | ADR-002 and adoption workflow |

ADR numbering is a proposal. Before creation, verify no concurrent decision has
claimed the next ID. ADRs must preserve history rather than silently rewrite
ADR-001 or DEC-006.

## 15. Deferred decisions

- exact released package/image versions compatible with the current runtime;
- whether grobid-client-python beats a small direct client;
- whether PaperQA selective helpers show a measurable quality gain;
- whether ASReview improves the competition corpus enough to retain;
- CJK font and CSL locale resource selection;
- permissive full-CSL processor comparison and citeproc-js legal/governance path;
- whether DVC solves a real fixture-management problem;
- exact ARS copied paths and file-level/upstream license review;
- SDK tracing backend, retention and optional Session storage;
- root project license;
- formal `APPROVED FOR M1 DEVELOPMENT` decision and approval tag.

## 16. Phase 6 outcome

The unified stack favors direct mature libraries and isolated services where
they reduce implementation cost, while preserving one RECA-owned source of truth
for every scientific and workflow concept. Full upstream applications are not
adopted when they duplicate Project, database, Agent, validation or UI state.

The next documentation-alignment phase may update formal documents according to
the linked map. Until that work occurs, this master plan is a research decision
record and must not be cited as proof of implementation.
