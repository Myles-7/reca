# Open-Source Research and Decisions Summary

Document version: `1.0.0`

Document status: `Conditional Approval`

Last updated: 2026-07-31

## 1. Scope

Phase 7 formalizes the Phase 0-6 research results into unique source records,
accepted ADRs, and a fact-based third-party registration structure.

Modified scope is limited to:

- `docs/source-research/`;
- `docs/decisions/`;
- `THIRD_PARTY_NOTICES.md`;
- this report and the Phase 6 alignment report.

No product, architecture, data-model, API/AI/Tool contract, test, or roadmap
authority document is modified. No code, dependency, Compose, CI, migration,
lockfile, Vendor source, Submodule, Fork, Prompt, script, test asset, or third-party
resource is added.

## 2. Source-research structure

The source-research index remains the
[Open-Source Integration Master Plan](../source-research/OPEN_SOURCE_INTEGRATION_MASTER_PLAN.md).
Project records use the existing `docs/source-research/projects/` directory.

Two records retain their earlier authoritative paths to avoid duplicate synonyms
and broken historical links:

- [Full Stack FastAPI Template](../source-research/full-stack-fastapi-template.md);
- [Academic Research Skills Codex](../source-research/academic-research-skills-codex.md).

The repository contains 26 project records for 26 distinct primary upstream
repositories. No repository has two project research records.

## 3. Research status model

[ADR-008](../decisions/ADR-008-IMPLEMENTATION-METADATA.md) formalizes the only
allowed source-research statuses:

```text
RESEARCHED
RECOMMENDED
EXPERIMENT_REQUIRED
PLANNED
ALREADY_INTEGRATED
REJECTED
```

Current distribution:

| Status | Count | Meaning in this repository |
| --- | ---: | --- |
| `ALREADY_INTEGRATED` | 6 | A package, service, or imported source baseline has repository evidence; full business capability is not implied |
| `PLANNED` | 11 | Direction and milestone are selected, but no current incorporation evidence exists |
| `EXPERIMENT_REQUIRED` | 5 | Quality, compatibility, license, isolation, or exact-asset spike must pass before adoption |
| `RECOMMENDED` | 4 | Design/development reference is recommended without current runtime adoption |
| `RESEARCHED` | 0 | Available for neutral completed research when no stronger disposition applies |
| `REJECTED` | 0 | No project is rejected outright by the current master plan |

Projects marked `ALREADY_INTEGRATED`:

| Project | Actual repository evidence | Limit |
| --- | --- | --- |
| Full Stack FastAPI Template | Controlled imported source and preserved MIT license | Specialized RECA tree must not be replaced wholesale |
| Celery | Backend manifest, lockfile, Worker entrypoint | Only M0 `reca.health_ping`; Celery state is not business state |
| Valkey | Fixed Compose service | Broker/cache foundation, never business truth |
| pgvector | Fixed PostgreSQL image and extension initialization | M0 extension foundation, not a complete evidence-retrieval implementation |
| GROBID | Fixed Compose service and health integration | M0 health path only, not formal PDF parsing workflow |
| TanStack Table | Frontend manifest and lockfile | Dependency presence does not prove all planned workbench features |

No other record is marked `ALREADY_INTEGRATED`.

## 4. Accepted ADRs

All seven Phase 6 proposals have independent reversal cost, ownership, and
source-of-truth consequences, so none was merged into a generic empty ADR.

| ADR | Decision |
| --- | --- |
| [ADR-002](../decisions/ADR-002-OPEN-SOURCE-INTEGRATION-MODES.md) | Normalized project integration modes and direct-versus-adapter boundary |
| [ADR-003](../decisions/ADR-003-LITERATURE-EVIDENCE-STACK.md) | Candidate-first PyAlex/GROBID/PDF.js/pgvector/PaperQA2/ASReview chain |
| [ADR-004](../decisions/ADR-004-DATA-STATISTICS-STACK.md) | Pandera as the planned P0 validator; deterministic SciPy/statsmodels/Matplotlib; GX/DVC non-authority roles |
| [ADR-005](../decisions/ADR-005-MANUSCRIPT-CITATION-STACK.md) | Immutable DOCX processing, selected CSL resources, deferred full citation processor |
| [ADR-006](../decisions/ADR-006-RESEARCH-WORKBENCH-UX.md) | Headless table/graph/PDF components over authoritative RECA APIs; Zotero as reference |
| [ADR-007](../decisions/ADR-007-AGENT-WORKFLOW-STACK.md) | One M8 RECA Orchestrator, SDK mechanics, conditional ARS assets, no upstream state authority |
| [ADR-008](../decisions/ADR-008-IMPLEMENTATION-METADATA.md) | Required adoption, provenance, license, fallback, and acceptance metadata |

## 5. ADR-001 ARS-Codex formalization

[ADR-001](../decisions/ADR-001-ARS-CODEX-USAGE.md) is amended to decision version
`1.2.0` and retains this fixed research/reuse baseline:

```text
repository: https://github.com/Imbad0202/academic-research-skills-codex
commit: f8d6b061efe98564a3f554c917fce66dcef6ca54
license: CC BY-NC 4.0
usage_intent: NONCOMMERCIAL_INTENT_DECLARED
```

The formal recommendation is conditional `SELECTIVE_VENDOR`; `FULL_VENDOR` is
also permitted only after a complete path-level license and packaging review.
Both require attribution, license isolation, copied/modified path records, and
commercialization or materially changed distribution re-review.

The decision does not change the M8 boundary, single RECA Orchestrator, existing
Tool contracts, approval model, or database-owned state. ADR-007 governs the
future runtime relationship.

Current ARS-Codex incorporation state remains:

```text
runtime_dependency: false
vendored_into_reca: false
fork_integrated: false
submodule_added: false
copied_content: none
```

## 6. Third-party notices

`THIRD_PARTY_NOTICES.md` now provides the required registration fields:

```text
Project
Repository
Upstream Commit/Tag
License
License file
Integration mode
Status
Copied paths
Modified paths
Modification summary
Attribution location
Special restrictions
Commercialization review
```

Changes are fact-based:

- Full Stack FastAPI Template is registered as actually integrated by controlled
  source copy. Its Commit relation is corrected from the obsolete "186 commits"
  statement to the verified one-commit relation after `0.10.0`.
- TanStack Table is registered because version `8.21.3` exists in the frontend
  manifest and lockfile.
- Celery, Valkey, pgvector, and GROBID retain their existing package/service
  evidence and are indexed as integrated foundations with explicit scope limits.
- Twenty projects without incorporation evidence are listed only as `PLANNED`
  or `RESEARCHED`; every row states that incorporation evidence is absent.
- ARS-Codex is not represented as copied or installed.

## 7. License snapshots

No new file is added under `vendor/licenses/`.

The repository already contains:

```text
vendor/licenses/full-stack-fastapi-template-LICENSE.txt
```

The Full Stack Template source record previously verified that this snapshot
matches the upstream root MIT `LICENSE` blob at the incorporated Commit. No
other researched project has current Vendor/resource-copy evidence requiring a
new snapshot in this phase. Pre-copying licenses for planned projects would
incorrectly imply incorporation.

## 8. Authority boundaries preserved

The ADR set explicitly preserves:

- PaperQA candidate evidence is not `EvidenceSpan`;
- ASReview ranking is not `LiteratureDecision`;
- DVC state is not `DatasetVersion`;
- Great Expectations output is not RECA `DataQualityRun` authority;
- statsmodels Summary is not `AnalysisResult`;
- citation output is not verified source truth;
- React Flow state is not evidence-graph authority;
- Agents SDK Session is not `ResearchProject`;
- Agents SDK Trace is not RECA audit authority;
- ARS workflow state is not RECA business state;
- Agent runtime remains M8 with one controlled Orchestrator.

No Requirement ID, Acceptance ID, API path, error code, Schema name, Agent Tool
name, enum value, Milestone ID, or M0 Issue ID is changed.

## 9. Remaining decisions

- Exact package/image/resource versions compatible with implementation runtime.
- Whether grobid-client-python, PaperQA2, and ASReview experiments justify adoption.
- Exact ARS-Codex paths and file-level license findings.
- Selected CSL files/locales and their individual rights metadata.
- citeproc-js license/isolation outcome or a selected alternative processor.
- Whether DVC solves a measured development fixture problem.
- RECA root license, which remains `PENDING_GOVERNANCE_DECISION`.

## 10. No-code-change confirmation

This phase makes documentation-governance changes only. It does not modify
backend, frontend, tests, dependency manifests, lockfiles, Compose, CI,
migrations, generated clients, source code, or runtime configuration. It does
not create Vendor content or copy third-party code, Prompt, script, test, style,
fixture, or other resource.
