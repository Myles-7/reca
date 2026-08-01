# Open-Source Integration Document Consistency Review

Document version: `1.0.0`

Document status: `Conditional Approval`

Review date: 2026-07-31

Review baseline: `b42e4b8b1d0ed93e207611dd7e57d4bd140506ac`

Root license: `PENDING_GOVERNANCE_DECISION`

## 1. Scope and result

Phase 11 reviewed the nine entry documents, all formal specification subdocuments,
all source-research records, all ADRs, all reports, `THIRD_PARTY_NOTICES.md`, and
all backend, frontend, and test module READMEs.

Result: `PASS`.

The review found no active-policy conflict, unexpected stable-identifier removal
or rename, broken relative link, case-mismatched target, invalid explicit anchor,
or orphaned active document. Two documentation consistency defects were repaired:

| Severity | Count | Finding | Resolution |
| --- | ---: | --- | --- |
| `BLOCKER` | 0 | None | No action required |
| `HIGH` | 0 | None | No action required |
| `MEDIUM` | 1 | Research, delivery, runtime, and Notices statuses could be read as one state machine | Added an explicit status-axis crosswalk to the master plan and clarified repository-wide ARS absence statements |
| `LOW` | 1 | Module READMEs, test READMEs, source records, and historical reports were not fully reachable from navigation indexes | Added entry/module/source/report navigation links |
| `INFO` | 3 | Historical absolute paths, the pre-existing enum extraction mismatch, and repository-wide absence of copied ARS content | Preserved or documented without changing current contracts |

No integration design was changed. The repairs make existing decisions easier to
trace and do not promote a researched or planned project to an implemented state.

## 2. Material reviewed

The complete read covered 164 unique files:

| Group | Files | Lines |
| --- | ---: | ---: |
| Nine entry documents | 9 | 4,447 |
| Formal specification subdocuments | 48 | 25,973 |
| Source research | 27 | 5,794 |
| ADRs | 8 | 674 |
| Reports and evidence | 36 | 6,857 |
| Third-party notices | 1 | Included in the review |
| Module READMEs | 35 | 3,223 |

The review distinguishes current authority from historical evidence. Dated
baselines and superseded ADR sections are not treated as current policy.

## 3. Status-axis consistency

The following axes are intentionally different:

| Axis | Meaning |
| --- | --- |
| Research status | Maturity of a project recommendation: `RESEARCHED`, `RECOMMENDED`, `EXPERIMENT_REQUIRED`, `PLANNED`, `ALREADY_INTEGRATED`, or `REJECTED` |
| Delivery status | Current product/architecture delivery state: `IMPLEMENTED`, `PLANNED`, `RESEARCHED`, or `EXPERIMENT_REQUIRED` |
| Runtime status | Repository evidence for an installed package, service, health-only foundation, planned capability, development-only tool, or absent integration |
| Notices status | Evidence-backed incorporation category; `RESEARCHED` and `PLANNED` do not claim copied or installed content |

A project can therefore be `RECOMMENDED` in research while remaining
`RESEARCHED` in Notices and absent at runtime. Actual repository evidence, not
recommendation maturity, controls incorporation claims.

## 4. Project consistency matrix

The following matrix reconciles the master plan, individual research records,
ADRs, roadmap, testing, security, Notices, README, and AGENTS guidance. Commit,
tag, detailed fallback, and test cases remain authoritative in each linked
research record and the
[master plan](../../source-research/OPEN_SOURCE_INTEGRATION_MASTER_PLAN.md).

| Project | Research status | Recommended mode | Milestone / runtime | License and attribution | Authority, fallback, and test boundary |
| --- | --- | --- | --- | --- | --- |
| Full Stack FastAPI Template | `ALREADY_INTEGRATED` | `ALREADY_INTERNALIZED_BASELINE` | M0 maintenance / selectively internalized | MIT snapshot and upstream Commit retained | RECA tree and M0 behavior are authoritative; no whole-tree overwrite; six required CI plus provenance checks |
| Celery | `ALREADY_INTEGRATED` | `DIRECT_DEPENDENCY` | M0 foundation, M1-M8 tasks / installed | BSD-3-Clause code; documentation license recorded | `Job` and `ProcessingRun` remain authoritative; bounded synchronous/database recovery; retry and idempotency tests |
| Valkey | `ALREADY_INTEGRATED` | `INDEPENDENT_SERVICE` | M0 foundation, M1+ support / Compose service | BSD-3-Clause root plus file-level review | PostgreSQL remains authoritative; recompute/database recovery fallback; restart, TTL, and pressure tests |
| pgvector | `ALREADY_INTEGRATED` | `INDEPENDENT_SERVICE` | M0 extension, M2-M3 retrieval / extension present | PostgreSQL License and version record | PostgreSQL objects and embedding lineage remain authoritative; exact/text fallback; isolation and ranking tests |
| pgvector-python | `PLANNED` | `DIRECT_DEPENDENCY` | M2-M3 / absent | MIT; record version on adoption | Repository boundary owns queries; reviewed SQL fallback; ORM/server compatibility tests |
| PyAlex | `PLANNED` | `DIRECT_DEPENDENCY_WITH_PROVIDER` | M2 / absent | MIT; provider provenance required | RECA search runs and records are authoritative; recorded HTTP fallback; retry and normalization tests |
| GROBID | `ALREADY_INTEGRATED` | `INDEPENDENT_SERVICE` | M0 health, M2-M3 parsing / health-only service | Apache-2.0 image/version attribution | Immutable PDF/TEI and converter objects are authoritative; pypdf degradation; corpus and page-validation tests |
| grobid-client-python | `EXPERIMENT_REQUIRED` | `SELECTIVE_VENDOR` | M2 / absent | Apache-2.0; exact copied paths and modifications required | RECA Job, Artifact, and client interface remain authoritative; small HTTP client fallback; spike and filesystem-boundary tests |
| PDF.js | `PLANNED` | `DIRECT_DEPENDENCY` | M2-M3 / absent | Apache-2.0; package/worker versions recorded | Backend evidence APIs are authoritative; reduced viewer fallback; authorization and coordinate round-trip tests |
| PaperQA2 | `EXPERIMENT_REQUIRED` | `SELECTIVE_VENDOR` | M3 and selected M8 assets / no full runtime | Apache-2.0; exact Prompt/code/test paths attributed | Output is candidate evidence only; native retrieval fallback; citation, no-evidence, conflict, and EvidenceSpan validation tests |
| ASReview | `EXPERIMENT_REQUIRED` | `DIRECT_DEPENDENCY_WITH_PROVIDER` | M3 optional enhancement / absent | Apache-2.0; version/model provenance required | Ranking is not `LiteratureDecision`; manual order fallback; seed, update, and no-write-path tests |
| Pandera | `PLANNED` | `DIRECT_DEPENDENCY` | M4 / absent | MIT; runtime/ruleset versions recorded | RECA rules and DataQuality objects are authoritative; explicit preflight degradation; FailureCase and performance tests |
| SciPy | `PLANNED` | `DIRECT_DEPENDENCY` | M5 / absent | BSD-3-Clause plus bundled licenses | Approved plan and normalized `AnalysisResult` are authoritative; unsupported-method failure; golden numeric tests |
| statsmodels | `PLANNED` | `DIRECT_DEPENDENCY` | M5 P0-Full / absent | BSD-3-Clause | Textual Summary is not `AnalysisResult`; defer regression fallback; coefficient, CI, missing-data tests |
| Matplotlib | `PLANNED` | `DIRECT_DEPENDENCY` | M5 / absent | Matplotlib license plus bundled font/library review | AnalysisResult and Figure manifest are authoritative; table-only fallback; headless, CJK, and value-equality tests |
| DVC | `RECOMMENDED` | `DEVELOPMENT_ONLY` | Optional M4-M7 / no application runtime | Apache-2.0 if adopted | Never replaces `DatasetVersion`; Git/object-storage fixture fallback; removal must not affect lineage |
| Great Expectations | `RECOMMENDED` | `DESIGN_REFERENCE` | M4 / no runtime | Apache-2.0; no copied asset claimed | Never becomes a second P0 validator or `DataQualityRun` authority; RECA report fallback; design-value test only |
| python-docx | `PLANNED` | `DIRECT_DEPENDENCY` | M6-M7 / absent | MIT; dependency/version attribution required | Immutable original DOCX and `ManuscriptVersion` are authoritative; read-only/export fallback; OOXML round-trip tests |
| CSL Styles | `PLANNED` | `RESOURCE_SNAPSHOT` | M3/M6, broader P1 / no files copied | CC BY-SA 3.0 repository baseline plus per-file rights review | RECA reference metadata remains authoritative; simple formatter fallback; per-file hash, rights, locale, and render tests |
| citeproc-js | `EXPERIMENT_REQUIRED` | `DEFERRED` | P1 decision / absent | CPAL/AGPL metadata conflict unresolved | Renderer cannot validate source truth; deterministic formatter fallback; no adoption before license/isolation ADR and goldens |
| TanStack Table | `ALREADY_INTEGRATED` | `DIRECT_DEPENDENCY` | M2-M7 / dependency present, features planned | MIT and package version recorded | Backend APIs remain authoritative; simple lists fallback; server-state, accessibility, and no-decision tests |
| xyflow / React Flow | `PLANNED` | `DIRECT_DEPENDENCY` | M7 / absent | MIT | Backend graph and `ClaimEvidenceLink` remain authoritative; table/tree fallback; authorization and stale-edge tests |
| Zotero | `RECOMMENDED` | `DESIGN_REFERENCE` | Optional M2-M3 / no runtime or source copy | AGPL-3.0; no source/assets copied | RECA records and workflow remain authoritative; standard exchange fallback; round-trip and independent-implementation tests |
| Zotero Web Library | `RECOMMENDED` | `DESIGN_REFERENCE` | M2-M3 UX / no source or asset copy | AGPL-3.0; no source/assets copied | RECA frontend/backend remain authoritative; native layout fallback; accessibility and no-copy review |
| OpenAI Agents SDK | `PLANNED` | `DIRECT_DEPENDENCY` | M8 / absent | MIT; runtime version and usage metadata required | SDK Session/Trace never replace Project/Audit records; direct provider/manual fallback; approval, redaction, and audit tests |
| ARS-Codex | `EXPERIMENT_REQUIRED` | `SELECTIVE_VENDOR` conditionally | M1+ mapping, M2-M8 assets / no copied or runtime content | CC BY-NC 4.0, fixed Commit, attribution, isolation, and commercialization re-review | ARS state never becomes RECA state; RECA-native workflows fallback; path-level license, quality, schema, and single-Orchestrator tests |

No row conflicts with its source record, ADR, roadmap placement, security
classification, test boundary, or Notices incorporation status.

## 5. Focused conflict scan

Current authority consistently states:

- PaperQA2 may provide selected candidate retrieval/packing assets, but does not
  take over the RECA literature runtime and never creates `EvidenceSpan` directly;
- ASReview is an optional ranking implementation for existing review behavior,
  not a P1-only product requirement and not a writer of `LiteratureDecision`;
- selected CSL resources support Competition/P0 citation behavior, while an
  arbitrary full processor remains deferred;
- Adapter use is benefit- and boundary-driven, not mandatory for every library;
- Zotero and Zotero Web Library are UX/exchange references only;
- citeproc-js is not approved for direct frontend integration;
- ARS-Codex clean-room-only restrictions are superseded, conditional reuse is
  allowed, and no ARS content or runtime is currently integrated;
- Agents SDK Session and Trace do not replace `ResearchProject` or audit records;
- DVC is not a user-data source and never replaces `DatasetVersion`;
- Great Expectations is not a second P0 runtime validator.

Old wording remains only where needed to preserve historical reports or an ADR
previous-decision section, with the current decision identified as superseding it.

## 6. Stable identifiers

The Phase 11 literal comparison used the ten lists under
[`document-split-baseline/`](../evidence/document-split-baseline/) and the Phase 0 capture
[`stable-identifiers-before.txt`](../evidence/open-source-research-evidence/stable-identifiers-before.txt).

| Identifier type | Baseline | Present | Unexpected removed | Unexpected renamed | Intentional additive change |
| --- | ---: | ---: | ---: | ---: | --- |
| Requirement IDs | 181 | 181 | 0 | 0 | None |
| Acceptance IDs | 16 | 16 | 0 | 0 | None |
| API paths | 236 | 236 | 0 | 0 | None |
| Error codes | 87 | 89 | 0 | 0 | `EXTERNAL_CAPABILITY_UNAVAILABLE`, `EXTERNAL_OUTPUT_INVALID` |
| Schema names | 16 | 16 | 0 | 0 | None |
| Agent Tool names | 51 | 51 | 0 | 0 | None |
| Enum/value candidates | 401 | 378 | 0 | 0 | None |
| Milestone IDs/tokens | 20 | 20 | 0 | 0 | None |
| ADR IDs | 1 | 8 | 0 | 0 | `ADR-002` through `ADR-008` |
| M0 Issue IDs | 4 | 4 | 0 | 0 | None |

The 23 absent enum/value candidates were already absent at the Phase 0 starting
HEAD. They are mainly environment and governance extraction candidates, and are
not removals made during Phases 0-11. No Requirement, Acceptance, API, Schema,
Tool, Enum, Milestone, ADR-001, or M0 Issue identifier was unexpectedly removed
or renamed.

## 7. Links, anchors, navigation, and paths

After the repairs, repository-wide Markdown validation reports:

```text
broken relative links: 0
case-mismatched targets: 0
invalid explicit anchors: 0
active formal/source/ADR/module README orphans: 0
report orphans: 0
```

The root README now links the backend, frontend, test module documentation,
source-research master plan, and this review. Backend/frontend README indexes and
the test entry index expose their module READMEs. The master plan exposes every
project record.

Three historical M0 acceptance documents contain absolute temporary-directory
paths. They record the environment used for those historical runs and are
retained as evidence rather than rewritten as current navigation.

## 8. Report index

Current and historical reports remain reachable here without changing their
authority status:

- [Document section migration map](../document-restructure/DOCUMENT_SECTION_MIGRATION_MAP.md)
- [Document split and compression summary](../document-restructure/DOCUMENT_SPLIT_AND_COMPRESSION_SUMMARY.md)
- [Document split baseline inventory](../document-restructure/DOCUMENT_SPLIT_BASELINE_INVENTORY.md)
- [Documentation consistency repair summary](../document-restructure/DOCUMENTATION_CONSISTENCY_REPAIR_SUMMARY.md)
- [M0 development summary](../../reports/M0_DEVELOPMENT_SUMMARY.md)
- [Security and reuse optimization baseline](../security-policy/SECURITY_AND_REUSE_OPTIMIZATION_BASELINE.md)
- [Security and open-source optimization summary](../security-policy/SECURITY_AND_OPEN_SOURCE_OPTIMIZATION_SUMMARY.md)
- [Open-source research baseline](./OPEN_SOURCE_RESEARCH_BASELINE.md)
- [Open-source research Phase 1: foundation](./OPEN_SOURCE_RESEARCH_PHASE_1_FOUNDATION.md)
- [Open-source research Phase 2: literature](./OPEN_SOURCE_RESEARCH_PHASE_2_LITERATURE.md)
- [Open-source research Phase 3: data](./OPEN_SOURCE_RESEARCH_PHASE_3_DATA.md)
- [Open-source research Phase 4: manuscript and frontend](./OPEN_SOURCE_RESEARCH_PHASE_4_MANUSCRIPT_FRONTEND.md)
- [Open-source research Phase 5: Agent](./OPEN_SOURCE_RESEARCH_PHASE_5_AGENT.md)
- [Open-source document alignment map](./OPEN_SOURCE_DOCUMENT_ALIGNMENT_MAP.md)
- [Open-source research and decisions summary](./OPEN_SOURCE_RESEARCH_AND_DECISIONS_SUMMARY.md)
- [Open-source alignment Phase 8: product and architecture](./OPEN_SOURCE_ALIGNMENT_PHASE_8_PRODUCT_ARCHITECTURE.md)
- [Open-source alignment Phase 9: data and contracts](./OPEN_SOURCE_ALIGNMENT_PHASE_9_DATA_CONTRACTS.md)
- [Open-source alignment Phase 10: test, security, and roadmap](./OPEN_SOURCE_ALIGNMENT_PHASE_10_TEST_SECURITY_ROADMAP.md)
- [Final open-source research and document alignment review](../../reports/FINAL_OPEN_SOURCE_RESEARCH_AND_DOCUMENT_ALIGNMENT_REVIEW.md)

## 9. Status and historical integrity

Current formal documentation remains `Conditional Approval`. No document was
promoted to an M1 development approval state and no tag was created. The root
project license remains `PENDING_GOVERNANCE_DECISION`; third-party file and
project licenses remain independent of that future choice.

Historical reports were not rewritten into current policy. ADR-001 preserves its
previous clean-room decision as history while its current section records the
conditional reuse decision.

Repository inspection at the review baseline found no copied, Vendored, Forked,
Submodule, Prompt, script, test, workflow, or runtime ARS-Codex content. Research
and conditional permission are not represented as incorporation.

## 10. No-code-change confirmation

The Phase 0 starting baseline is:

```text
849a6972d16ba076becfd8a306717cf222969c4c
```

Comparison through the Phase 10 baseline changed only Markdown and documentation
evidence CSV/TXT files. Phase 11 changes only Markdown documentation.

No backend or frontend source, dependency manifest, lockfile, Compose file, CI
workflow, migration, generated client, runtime configuration, or actual Vendor
source changed during Phases 0-11.

## 11. Final disposition

```text
unexpected removed stable identifiers: 0
unexpected renamed stable identifiers: 0
active policy conflicts: 0
broken links: 0
code or dependency changes: 0
documentation status: Conditional Approval
root license: PENDING_GOVERNANCE_DECISION
```

Phase 11 is complete. Future implementation must continue to follow the pinned
research record, accepted ADR, license/attribution review, fallback, and
project-specific acceptance matrix for each adopted capability.
