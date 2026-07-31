# Final Open-Source Research and Document Alignment Review

Document version: `1.0.0`

Audit date: 2026-07-31

Audit baseline: `8b748e1d47084b47cb1a493142f9ee373f21c7fb`

Documentation status: `Conditional Approval`

Root license: `PENDING_GOVERNANCE_DECISION`

Final audit status: `PASS`

Approval recommendation: `READY FOR PROJECT OWNER APPROVAL`

## 1. Executive Summary

RECA completed repository-level research and cross-document alignment for 26
primary upstream projects. Every project has one unique research record, a fixed
research Commit, a license finding, a recommended integration mode, a milestone,
a runtime truth statement, a source-of-truth boundary, a fallback, and an
acceptance expectation.

| Decision group | Count | Interpretation |
| --- | ---: | --- |
| Direct runtime packages | 13 | 11 `DIRECT_DEPENDENCY` plus 2 `DIRECT_DEPENDENCY_WITH_PROVIDER` recommendations |
| Independent services | 3 | Valkey, pgvector, and GROBID |
| Selective Vendor | 3 | grobid-client-python, PaperQA2, and ARS-Codex, all subject to pre-adoption review |
| Resource snapshots | 1 | Selected CSL styles/locales only; no resource has yet been copied |
| Design references only | 3 | Great Expectations, Zotero, and Zotero Web Library |
| Development-only reference | 1 | DVC |
| Deferred | 1 | citeproc-js pending license/isolation or alternative selection |
| Already internalized baseline | 1 | Full Stack FastAPI Template; preserve the specialized RECA tree |

Research status distribution is 6 `ALREADY_INTEGRATED`, 11 `PLANNED`, 5
`EXPERIMENT_REQUIRED`, and 4 `RECOMMENDED`. An integrated foundation does not
claim that its later milestone business behavior is complete.

The product, architecture, domain, contracts, testing, security, roadmap,
development rules, source research, ADRs, Notices, and module navigation are
aligned. There are zero active `BLOCKER` or `HIGH` findings, zero unexpected
stable-contract removals or renames, zero broken documentation links, and zero
code/dependency changes. The documentation is ready to enter the project owner
approval process.

This recommendation does not change `Conditional Approval`, grant
`APPROVED FOR M1 DEVELOPMENT`, create a tag or branch, approve any unresolved
license, or authorize an actual dependency/Vendor integration.

Evidence index:

- [Repository pins](./final-open-source-review-evidence/repository-pins.csv)
- [License matrix](./final-open-source-review-evidence/license-matrix.csv)
- [Integration matrix](./final-open-source-review-evidence/integration-matrix.csv)
- [Document change list](./final-open-source-review-evidence/document-change-list.txt)
- [Stable identifier diff](./final-open-source-review-evidence/stable-identifiers-diff.txt)
- [Markdown link validation](./final-open-source-review-evidence/markdown-links.txt)
- [Third-party status check](./final-open-source-review-evidence/third-party-status-check.txt)
- [Source-research completeness](./final-open-source-review-evidence/source-research-completeness.txt)
- [ADR completeness](./final-open-source-review-evidence/adr-completeness.txt)
- [No-code-change check](./final-open-source-review-evidence/no-code-change-check.txt)
- [M0 baseline check](./final-open-source-review-evidence/m0-baseline-check.txt)

## 2. Repository Research Scope

All research was fixed and reviewed on 2026-07-31. The Commit is a research
baseline, not an instruction to install that revision without a milestone Spike.

| Project | Repository | Fixed research Commit | License |
| --- | --- | --- | --- |
| Full Stack FastAPI Template | `fastapi/full-stack-fastapi-template` | `546f18469c30fb1748da21f044189f2f83639ea6` | MIT |
| Celery | `celery/celery` | `7c5d9a62d90c685bd0e1ae002d66ae40980b2847` | BSD-3-Clause code; CC BY-SA 4.0 docs |
| Valkey | `valkey-io/valkey` | `0bf28b2dab6d21ea278fbaf1517b45e55d9b9c6f` | BSD-3-Clause root plus file-level licenses |
| pgvector | `pgvector/pgvector` | `4f3d17f6f74fe98adf54df4d016de241eeaae9af` | PostgreSQL License |
| pgvector-python | `pgvector/pgvector-python` | `60739dfd6cb9d674f32afa4184d43e6aff9dfbcf` | MIT |
| PyAlex | `J535D165/pyalex` | `875c708cbb6e449feebc46d2a7a26af8ed8b2fdd` | MIT |
| GROBID | `grobidOrg/grobid` | `c3229a4b9ba1e9eb8ec8327c2ec9eed1581d410c` | Apache-2.0 |
| grobid-client-python | `grobidOrg/grobid-client-python` | `161e0f45189c8592b2e2c58e9638cc6218bc75fb` | Apache-2.0 |
| PDF.js | `mozilla/pdf.js` | `a80897dc9a2eb80c474717b683a4153f5b628ac7` | Apache-2.0 |
| PaperQA2 | `Future-House/paper-qa` | `d7675d7b7eddeb3535e8c260399c5bbeeb818c50` | Apache-2.0 |
| ASReview | `asreview/asreview` | `d3e863c94e1945ace7848b6ca5bcf2fb1eecbdb5` | Apache-2.0 |
| Pandera | `unionai-oss/pandera` | `85cc2a16b2110d4c4b8cc7f956aab94bc53716f6` | MIT |
| SciPy | `scipy/scipy` | `420a778219f6db170f0fda8dcda4add8a32fd1d6` | BSD-3-Clause plus bundled licenses |
| statsmodels | `statsmodels/statsmodels` | `d3187f844d196de1760829820a7c872a6d6ebb1d` | BSD-3-Clause |
| Matplotlib | `matplotlib/matplotlib` | `faf5d100aed23d3271245c2e800ea47f86dd858b` | Matplotlib license plus bundled licenses/fonts |
| DVC | `iterative/dvc` | `f74c1c0e709de61f571905802bc0c75035dc6ef2` | Apache-2.0 |
| Great Expectations | `great-expectations/great_expectations` | `33614cd70a407f8b9589fa2cf5f1cb1d7d0723aa` | Apache-2.0 |
| python-docx | `python-openxml/python-docx` | `e45454602b53e8e572b179ccf1c91093ec9f4ed7` | MIT |
| CSL Styles | `citation-style-language/styles` | `1de508b010b2643c8b13b082947f1054bc33357f` | CC BY-SA 3.0 plus selected file rights |
| citeproc-js | `Juris-M/citeproc-js` | `cc9153c45293af878de08cafddbefe6ea150c380` | CPAL/AGPL metadata conflict unresolved |
| TanStack Table | `TanStack/table` | `d66b39f01e23eeb4e2befc7777194104967212d3` | MIT |
| xyflow / React Flow | `xyflow/xyflow` | `360f5b13e2bc6899ea06b4be1a49b068d86926cf` | MIT |
| Zotero | `zotero/zotero` | `4ec5ba9c279841b09231db82a61e30bd9e7dc6ef` | AGPL-3.0 plus third-party notices |
| Zotero Web Library | `zotero/web-library` | `556d0bf6b1b48fa8402a91afa62b15533b713013` | AGPL-3.0 |
| OpenAI Agents SDK | `openai/openai-agents-python` | `0ffa36840cb812488738f6fc5be3d3a1f51397b7` | MIT |
| ARS-Codex | `Imbad0202/academic-research-skills-codex` | `f8d6b061efe98564a3f554c917fce66dcef6ca54` | CC BY-NC 4.0 plus file-level review |

## 3. Final Integration Matrix

| Project | Mode | Milestone | Status | Core reuse | Do not reuse as | License requirement |
| --- | --- | --- | --- | --- | --- | --- |
| Full Stack Template | `ALREADY_INTERNALIZED_BASELINE` | M0 maintenance | `ALREADY_INTEGRATED` | Framework/auth/test foundation and selective fixes | Whole-tree replacement of specialized RECA | Preserve MIT snapshot and import provenance |
| Celery | `DIRECT_DEPENDENCY` | M0, M1-M8 | `ALREADY_INTEGRATED` | Worker dispatch, retry, queue mechanics | Business Job or ProcessingRun authority | Preserve BSD code attribution and separate docs terms |
| Valkey | `INDEPENDENT_SERVICE` | M0, M1+ | `ALREADY_INTEGRATED` | Broker, cache, bounded ephemeral state | Business facts or durable workflow truth | BSD plus file-level review |
| pgvector | `INDEPENDENT_SERVICE` | M0, M2-M3 | `ALREADY_INTEGRATED` | PostgreSQL vector type and measured retrieval | Separate project/data authority | PostgreSQL License attribution |
| pgvector-python | `DIRECT_DEPENDENCY` | M2-M3 | `PLANNED` | ORM vector fields and expressions | Domain or public contract object | MIT and locked runtime version |
| PyAlex | `DIRECT_DEPENDENCY_WITH_PROVIDER` | M2 | `PLANNED` | OpenAlex search/filter/page transport | Database or frontend entity | MIT and provider provenance |
| GROBID | `INDEPENDENT_SERVICE` | M2-M3 | `ALREADY_INTEGRATED` health only | PDF-to-TEI parsing | EvidenceSpan or RECA document truth | Apache image/NOTICE/version record |
| grobid-client-python | `SELECTIVE_VENDOR` | M2 | `EXPERIMENT_REQUIRED` | Transport, retry, bounded concurrency | Upstream output-directory/data ownership | Exact Apache paths and modifications |
| PDF.js | `DIRECT_DEPENDENCY` | M2-M3 | `PLANNED` | Display, navigation, Text/Annotation layers | Evidence truth source | Apache package/worker attribution |
| PaperQA2 | `SELECTIVE_VENDOR` | M3, M8 | `EXPERIMENT_REQUIRED` | Retrieval, packing, Prompt and test assets | EvidenceSpan, project, index, or Agent authority | Exact Apache paths, changes, and attribution |
| ASReview | `DIRECT_DEPENDENCY_WITH_PROVIDER` | M3 optional | `EXPERIMENT_REQUIRED` | Read-priority ranking | LiteratureDecision writer | Apache version/model provenance |
| Pandera | `DIRECT_DEPENDENCY` | M4 | `PLANNED` | P0 dataframe validation runtime | Independent business state | MIT plus ruleset/runtime version |
| SciPy | `DIRECT_DEPENDENCY` | M5 | `PLANNED` | Deterministic tests/correlations | Unnormalized formal result | BSD and bundled-license review |
| statsmodels | `DIRECT_DEPENDENCY` | M5 P0-Full | `PLANNED` | Regression and diagnostics | Textual Summary as AnalysisResult | BSD and runtime version |
| Matplotlib | `DIRECT_DEPENDENCY` | M5 | `PLANNED` | Fixed-template rendering | Figure/business result authority | Custom license and bundled font review |
| DVC | `DEVELOPMENT_ONLY` | Optional M4-M7 | `RECOMMENDED` | Fixture provenance and reproduction ideas | DatasetVersion or user data source | Apache if actually installed |
| Great Expectations | `DESIGN_REFERENCE` | M4 | `RECOMMENDED` | Taxonomy, report UX, test ideas | Second P0 runtime/DataQualityRun | Apache attribution for any adapted asset |
| python-docx | `DIRECT_DEPENDENCY` | M6-M7 | `PLANNED` | DOCX traversal and controlled derived output | Original-file mutation authority | MIT and transitive dependency record |
| CSL Styles | `RESOURCE_SNAPSHOT` | M3/M6, P1 | `PLANNED` | Selected GB/T/APA styles/locales | Whole repository snapshot | Per-file rights, authors, Commit, hash, changes |
| citeproc-js | `DEFERRED` | P1 decision | `EXPERIMENT_REQUIRED` | Nothing until decision; candidate full CSL engine | Direct frontend integration or verified source truth | Resolve CPAL/AGPL conflict and isolation/alternative |
| TanStack Table | `DIRECT_DEPENDENCY` | M2-M7 | `ALREADY_INTEGRATED` package | Dense headless workbench tables | Decision, approval, or durable state | MIT package attribution |
| xyflow / React Flow | `DIRECT_DEPENDENCY` | M7 | `PLANNED` | Evidence graph projection | Evidence graph authority | MIT package attribution |
| Zotero | `DESIGN_REFERENCE` | Optional M2-M3 | `RECOMMENDED` | Exchange formats and library UX | Copied desktop source or Zotero state | AGPL boundary; no source/assets copied |
| Zotero Web Library | `DESIGN_REFERENCE` | M2-M3 | `RECOMMENDED` | Responsive collection/list/detail UX | Copied source, assets, reducers, or branding | AGPL boundary; independent implementation |
| OpenAI Agents SDK | `DIRECT_DEPENDENCY` | M8 | `PLANNED` | Runner, Tool, guardrail, HITL, usage mechanics | ResearchProject, AuditLog, or free multi-Agent authority | MIT and tracing/data configuration record |
| ARS-Codex | `SELECTIVE_VENDOR` conditional | M1+ mapping, M2-M8 | `EXPERIMENT_REQUIRED` | Selected scoping/research/verification Prompt, workflow, test assets | Business state, unrestricted Agent runtime, or original RECA claim | CC BY-NC attribution/isolation and commercialization review |

## 4. Final RECA Stack

### Engineering

The specialized Full Stack FastAPI Template baseline remains the engineering
foundation. Celery supplies asynchronous mechanics, Valkey supplies broker/cache
support, and PostgreSQL with pgvector remains the authoritative relational and
vector platform. pgvector-python stays below repository boundaries.

### Literature

PyAlex is the planned OpenAlex provider. GROBID plus a RECA converter turns an
immutable PDF into retained TEI and RECA-owned pages, chunks, and reference
candidates. PDF.js displays authorized bytes and supports navigation.

### Evidence

Project-scoped pgvector retrieval and selected PaperQA2 assets may produce
candidate evidence. Exact page text, document version, coordinates, and source
validation are required before RECA creates `EvidenceSpan`. ASReview may rank
what to read next; only the user creates `LiteratureDecision`.

### Data

Pandera is the planned P0 runtime validator. Its failures are normalized into
RECA quality issues tied to immutable `DatasetVersion` and versioned rule sets.
Great Expectations is a report/test reference, not a second runtime.

### Statistics

SciPy and statsmodels perform deterministic calculations from approved plans.
RECA normalizes values, warnings, effective N, assumptions, parameters, and
engine metadata into `AnalysisResult`. Matplotlib renders fixed templates from
those results.

### Manuscript

python-docx handles supported high-level DOCX operations; controlled lxml/OOXML
enhancement covers narrow gaps. Original DOCX Artifacts remain immutable, and
approved changes create a new `ManuscriptVersion`.

### Citation

Competition/P0 uses a deterministic basic formatter and selected, reviewed CSL
resources. Full citeproc-js adoption is deferred. Citation rendering never
proves that the underlying source is valid.

### Frontend

TanStack Table supplies headless dense tables, PDF.js supplies document
interaction, and React Flow supplies graph visualization. Backend APIs remain
authoritative. Zotero projects inform exchange compatibility and UX only.

### Agent

M8 may use OpenAI Agents SDK inside one RECA `ResearchOrchestrator`. Function
Tools pass through RECA Services, Schema, permissions, approval, and audit.
Selected ARS-Codex assets may later enhance Prompts/workflows/tests after their
separate reuse gate.

### Reproduction

`ReproPackage` records runtime dependency and service versions, upstream and
Vendored Commits, Prompt/ruleset versions, statistical engines, citation style
identifiers, and Artifact lineage. DVC may help development fixtures but cannot
replace this business provenance.

## 5. RECA Original Value Boundary

RECA's original value is not a thin list of upstream packages. It is the domain
and evidence authority that joins mature capabilities into a trustworthy
research workflow:

```text
ResearchProject
EvidenceSpan
DatasetVersion
DataTransformation
AnalysisResult
ApprovalRecord
ClaimEvidenceLink
AuditResult
ReproPackage
Cross-domain evidence chain
```

These objects and the transitions between literature, files, evidence, data,
analysis, figures, claims, manuscript versions, approvals, audits, and exports
remain RECA-owned. No upstream session, trace, rank, summary, rendered citation,
graph state, pipeline state, or validation result replaces them.

## 6. Product Alignment

- Requirement IDs changed: 0; all 181 baseline IDs remain present.
- P0 requirement scope changed: 0.
- Success metrics removed or weakened: 0.
- Open-source capabilities are implementation strategies for existing needs,
  not new product Requirement IDs.
- Active learning remains an optional implementation of the existing review
  workflow rather than a new product promise.
- Formal approval remains limited to irreversible changes, formal research facts,
  data versions, and other high-risk effects; read-only/candidate work may run
  automatically under the documented risk level.

## 7. Architecture Alignment

The architecture now consistently supports:

```text
DIRECT_LIBRARY_INTEGRATION
PROVIDER_OR_ADAPTER_INTEGRATION
INDEPENDENT_SERVICE
ISOLATED_SERVICE
SELECTIVE_VENDOR
RESOURCE_SNAPSHOT
DESIGN_REFERENCE
```

Direct integration is allowed for stable, narrow libraries when abstraction
cost exceeds its benefit. A Provider/Adapter remains required when the external
API changes, multiple implementations are expected, third-party objects would
leak into the domain, offline Mocking is needed, or a security/license boundary
exists. Services and Vendor boundaries are selected for process, resource,
license, or failure isolation. Complex business operations always remain in
RECA Services.

## 8. Domain and Contract Alignment

Provider-neutral API paths, Schema names, Tool names, and error families are
preserved. Project names do not appear as public `/run-project-name` endpoints.

| Third-party result | RECA treatment |
| --- | --- |
| OpenAlex Work | Candidate/normalized `LiteratureRecord` input |
| GROBID TEI | Retained parsed-document intermediate input |
| PaperQA evidence | Candidate evidence requiring source validation |
| ASReview rank | Screening recommendation requiring user decision |
| Pandera FailureCase | Normalized `DataQualityIssue` |
| SciPy/statsmodels output | Normalized deterministic `AnalysisResult` |
| Matplotlib output | Figure Artifact tied to result and parameter manifest |
| Citation engine output | `CitationRenderResult`-equivalent candidate output; not source validity |
| Agents SDK run | Execution mechanism recorded through RECA Agent/Tool/Model audit objects |
| ARS workflow state | Prompt/workflow input; never business state |

The compatibility work added two provider-neutral errors,
`EXTERNAL_CAPABILITY_UNAVAILABLE` and `EXTERNAL_OUTPUT_INVALID`, without removing
or renaming baseline errors.

## 9. Testing Alignment

Every actually adopted capability must pass the third-party acceptance matrix:

1. pinned version;
2. license and attribution;
3. compatibility;
4. main demo effect;
5. failure behavior and visible degradation;
6. resource usage;
7. Offline or Recorded behavior;
8. provider-neutral Schema conversion;
9. project isolation;
10. reproducibility and implementation metadata.

Project-specific tests cover GROBID layout/failure/fallback, PaperQA evidence
recall and validation, ASReview no-write ranking, Pandera issue conversion,
SciPy/statsmodels golden numbers, Matplotlib deterministic output, citation
formats and isolation, and SDK/ARS approval, guardrail, data, tracing, Prompt,
checkpoint, and claim-verification behavior. Upstream tests may be adapted only
with source and license records.

## 10. Security and License Alignment

Before dependency, service, Fork, Vendor, Submodule, resource snapshot, or copy
adoption, RECA records the upstream repository, fixed Commit/tag/version,
license file, integration mode, copied/modified paths, modification summary,
attribution location, special restrictions, reviewer, date, and
commercialization-review condition.

Current special boundaries are:

- Matplotlib: custom license and bundled font/library review;
- CSL Styles: per-file `<rights>`, author, locale, Commit, hash, and changes;
- citeproc-js: unresolved CPAL/AGPL metadata; no adoption before decision;
- Zotero projects: AGPL design/exchange reference only;
- ARS-Codex: CC BY-NC attribution, isolation, exact paths, and commercial re-review;
- no-license or unknown-source content: do not copy.

Research records do not claim incorporation. `THIRD_PARTY_NOTICES.md` identifies
only six evidence-backed integrated foundations among the 26 projects, with
scope limits. The RECA root license remains pending and cannot override any
third-party obligation.

## 11. ARS-Codex

```text
usage_intent: NONCOMMERCIAL_INTENT_DECLARED
research_commit: f8d6b061efe98564a3f554c917fce66dcef6ca54
reuse_scope: selected or full reuse only after exact license and attribution review
vendor_recommendation: SELECTIVE_VENDOR preferred; FULL_VENDOR conditionally permitted
attribution: CC BY-NC 4.0, author/project, repository, Commit, copied paths, modifications
commercialization_review: required before commercialization, changed use, or public product deployment
actual_copied_content: none
```

ARS reuse does not change the single-Orchestrator design, advance the M8 runtime,
allow free multi-Agent execution, bypass Tool contracts, or make ARS state a
RECA business state. This documentation program copied no ARS Prompt, code,
script, test, workflow, hook, policy, or other asset.

## 12. M0 Regression

The M0 engineering baseline is preserved:

```text
M0 commit: 79825914c7c975e8be256a5a89abe812f486769e
m0-complete tag object: a91f9278db450ef3e52bfbff7af83d866f5feb75
m0-complete peeled commit: 79825914c7c975e8be256a5a89abe812f486769e
M0 status: COMPLETED
M1 Entry: ALLOWED
```

The M0 Commit is an ancestor of the audit baseline. The six required CI jobs,
infrastructure clean-room, `M0-ISSUE-0006`, and `M0-ISSUE-0009` remain intact.
No open-source recommendation moves the formal Agent runtime before M8.

## 13. Stable Identifiers

| Identifier type | Baseline | Present | Unexpected removed | Unexpected renamed | Intentional additions |
| --- | ---: | ---: | ---: | ---: | --- |
| Requirement IDs | 181 | 181 | 0 | 0 | 0 |
| Acceptance IDs | 16 | 16 | 0 | 0 | 0 |
| API paths | 236 | 236 | 0 | 0 | 0 |
| Error codes | 87 | 87 baseline | 0 | 0 | 2 provider-neutral errors |
| Schema names | 16 | 16 | 0 | 0 | 0 |
| Agent Tool names | 51 | 51 | 0 | 0 | 0 |
| Enum/value candidates | 401 | 378 | 0 | 0 | 0 |
| Milestone IDs/tokens | 20 | 20 | 0 | 0 | 0 |
| ADR IDs | 1 | 1 baseline | 0 | 0 | ADR-002 through ADR-008 |
| M0 Issue IDs | 4 | 4 | 0 | 0 | 0 |

The 23 enum/value candidates absent from current Markdown were already absent at
the Phase 0 starting HEAD. They are not Phase 0-12 deletions. The exact list is
in the [stable identifier evidence](./final-open-source-review-evidence/stable-identifiers-diff.txt).

## 14. Documentation Changes

### Entry documents

| File | Alignment result |
| --- | --- |
| `README.md` | Competition scope, original-value boundary, researched stack status, license status, and navigation aligned |
| `AGENTS.md` | Reuse workflow, project-specific boundaries, attribution, Tool and reading rules aligned |
| `docs/PRODUCT_REQUIREMENTS.md` | Existing Requirement implementation enhancements aligned; no ID/P0/success-metric change |
| `docs/ARCHITECTURE.md` | Four-layer architecture, integration modes, six stacks, and authority boundaries aligned |
| `docs/DATA_MODEL_AND_WORKFLOW.md` | Implementation metadata and third-party result mappings aligned without project-specific tables |
| `docs/API_AI_TOOL_CONTRACTS.md` | Provider-neutral APIs, Schemas, Tools, errors, approval, and degradation aligned |
| `docs/TEST_AND_ACCEPTANCE.md` | Third-party acceptance matrix and module navigation aligned |
| `docs/SECURITY_AND_OPEN_SOURCE.md` | Competition safeguards, project license classes, ARS zero-copy state, and root-license boundary aligned |
| `docs/IMPLEMENTATION_ROADMAP.md` | M1-M9 Research-Spike-Decision-Integration workflow aligned |

### Subordinate and operational documents

- Product: five requirement subdocuments aligned with existing IDs.
- Architecture: four component/data-flow/operations/Agent subdocuments aligned.
- Data model: five model/state-machine subdocuments aligned.
- Contracts: six API/AI/Tool subdocuments aligned.
- Testing: four formal test subdocuments and four test-directory READMEs aligned.
- Security: open-source governance aligned; the other three security authorities
  were reviewed and remained consistent.
- Roadmap: delivery workflow and M1-M9 milestone documents aligned.
- Development: four implementation-rule documents aligned.
- Modules: root, nine backend module, five frontend module, and test README
  navigation/boundaries aligned.

### Research, ADR, and reports

- 26 unique project research records are complete.
- One master integration plan is the research index and project decision matrix.
- ADR-001 is amended; ADR-002 through ADR-008 formalize independent decisions.
- `THIRD_PARTY_NOTICES.md` distinguishes research/planning from incorporation.
- Phase 0-11 reports preserve baselines, research evidence, alignment decisions,
  and consistency results.

The exact per-file list is the
[document change evidence](./final-open-source-review-evidence/document-change-list.txt).

## 15. Findings

| ID | Severity | Area | Finding | Evidence | Required Action |
| --- | --- | --- | --- | --- | --- |
| `OSINT-DOC-001` | `MEDIUM` | Status consistency | Research, delivery, runtime, and Notices status axes were previously easy to conflate | Phase 11 review and master-plan crosswalk | Closed: retain the crosswalk and use repository evidence for incorporation claims |
| `OSINT-DOC-002` | `LOW` | Navigation | Module, research, and historical report navigation was incomplete | Phase 11 link/orphan scan | Closed: retain indexes and validate links on later documentation changes |
| `OSINT-DOC-003` | `INFO` | Citation license | citeproc-js license metadata remains conflicting and is intentionally excluded from adoption approval | citeproc-js research record and license matrix | Keep `DEFERRED`; choose a permissive alternative or approve an isolated obligation-compliant design before adoption |
| `OSINT-DOC-004` | `INFO` | ARS-Codex | Exact reusable paths and file-level findings are an explicit future reuse gate; intent is noncommercial but not legally confirmed | ADR-001, ARS research record, Notices | Complete path-level review and attribution package before copying; re-review commercialization/use changes |
| `OSINT-DOC-005` | `INFO` | Root governance | RECA root license remains intentionally outside this documentation program | README and security governance | Project owner makes a separate root-license decision before public distribution; do not override third-party terms |
| `OSINT-DOC-006` | `INFO` | Implementation | Planned project Spikes and runtime compatibility checks remain milestone implementation work | Roadmap and project validation-spike sections | Run the milestone Spike before freezing package/image/resource versions or adapters |
| `OSINT-DOC-007` | `INFO` | Operations | Competition-machine CPU, RAM, disk, font, and service startup budgets remain implementation-time evidence | Test matrix and roadmap M9 | Benchmark the full demo stack on the target machine and preserve fallbacks |
| `OSINT-DOC-008` | `INFO` | External services | OpenAlex/model/provider rate limits and outages remain external constraints | PyAlex/provider research and degradation contracts | Use bounded retry, cache/recorded fixtures, visible degradation, and demo preflight |

Finding totals:

```text
BLOCKER: 0
HIGH: 0
MEDIUM: 1 (closed consistency repair)
LOW: 1 (closed consistency repair)
INFO: 6 (explicit deferred, approval, implementation, and operational gates)
```

No active documentation defect blocks entry into the project owner approval
process. INFO conditions remain mandatory gates for the affected integration or
release, but they are not defects in the completed documentation alignment.

## 16. Residual Risks

1. The RECA root license remains `PENDING_GOVERNANCE_DECISION`.
2. No planned dependency/service/Vendor capability has completed its actual code
   Spike merely because research is complete.
3. Research Commits are fixed, but actual compatible package/image/resource
   versions must be frozen during implementation with lock and metadata evidence.
4. citeproc-js remains deferred pending license/isolation or alternative choice.
5. ARS-Codex remains `NONCOMMERCIAL_INTENT_DECLARED`; exact assets and future
   commercialization or changed deployment require re-review.
6. Upstream maintenance, security, licensing, API, and behavior can change after
   the research Commit; upgrades require a new diff and acceptance run.
7. GROBID, Worker, PostgreSQL/pgvector, object storage, model calls, and frontend
   rendering must fit the actual competition machine resource budget.
8. OpenAlex and other external APIs can rate-limit or fail; Recorded/offline
   fixtures and visible degradation remain necessary for demo stability.

These risks are bounded by existing roadmap, fallback, testing, provenance, and
license gates. None changes RECA domain authority or the current documentation
status.

## 17. Approval Recommendation

```text
READY FOR PROJECT OWNER APPROVAL
```

Rationale:

- `BLOCKER = 0` and `HIGH = 0`;
- unexpected stable identifier removals and renames are 0;
- entry/subdocument/source/ADR/report links pass;
- all 26 projects have unique research records, Commits, licenses, modes, and
  boundaries;
- no unlicensed or unknown-source project is recommended for copying;
- planned and researched states are not represented as implemented;
- third-party results do not replace RECA business truth;
- M0 regression remains preserved;
- Phases 0-12 changed no code, dependencies, infrastructure, Vendor source, or
  runtime configuration.

Project owner approval may accept the documentation package while retaining the
listed implementation and license gates. It must be a separate explicit action.
This report does not modify formal document status, create `docs-m1-approved`,
create an M1 branch, install a dependency, or copy third-party content.
