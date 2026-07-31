# Open-Source Alignment Phase 8: Product and Architecture

Document version: `1.0.0`

Document status: `Conditional Approval`

Last updated: 2026-07-31

## 1. Scope

Phase 8 aligns repository entry guidance, product requirements, architecture,
and backend/frontend module READMEs with the accepted open-source research stack
and ADR-001 through ADR-008.

The phase changes documentation only. It does not install a package, modify a
lockfile, add code, create a module, copy upstream content, add a Vendor snapshot,
change Compose/CI/migrations, or claim that planned capabilities are implemented.

## 2. README alignment

`README.md` now distinguishes mature reusable capabilities from RECA's original
domain core.

Reusable capability areas include engineering foundation, PDF processing,
literature retrieval, screening assistance, validation, statistics, figures,
DOCX, citation, task scheduling, and frontend components.

RECA-owned authority remains concentrated in:

```text
ResearchProject
EvidenceSpan
DatasetVersion
AnalysisResult
ApprovalRecord
ClaimEvidenceLink
AuditResult
ReproPackage
cross-literature-data-analysis-figure-manuscript evidence chain
```

The new milestone integration table uses only `IMPLEMENTED`, `PLANNED`,
`RESEARCHED`, and `EXPERIMENT_REQUIRED`. Existing M0 services and dependencies
are explicitly limited to their current smoke, health, or foundation scope.

## 3. AGENTS alignment

`AGENTS.md` adds task reading paths for:

- open-source project implementation;
- third-party runtime upgrades;
- Vendored asset modification;
- citation stack work;
- evidence retrieval stack work.

Repository rules now require reading the source record and applicable ADR,
running a real-effect Spike before freezing an integration boundary, and
choosing direct library, Provider/Adapter, independent/isolated service,
Selective Vendor, resource snapshot, or design reference based on measured
coupling and value.

The rules explicitly preserve:

- PaperQA candidate-only evidence;
- ASReview advisory-only ranking;
- Pandera as the planned P0 validation runtime;
- Great Expectations as non-runtime reference;
- DVC as non-authoritative provenance inspiration;
- isolated citation-engine review;
- Zotero as UX/exchange reference only;
- SDK Session/Trace non-authority;
- ADR-001 requirements for ARS-Codex;
- provenance for reused Prompt, script, test, and golden assets.

## 4. Product alignment

`PRODUCT_REQUIREMENTS.md` advances to version `1.4.0`. No Requirement ID is
added, removed, renamed, or reprioritized. The open-source projects are recorded
only as implementation enhancements for existing product requirements.

### Research question

ARS Scoping, Checkpoint, and Mode/Stage assets may support existing RQ flows.
They produce candidates and prompts; RECA Services and users still create,
version, and confirm the formal ResearchQuestionVersion.

### Literature and evidence

- PyAlex implements an OpenAlex Provider without leaking PyAlex objects.
- GROBID TEI remains an intermediate result converted by RECA.
- PDF.js provides display and navigation, not evidence truth.
- PaperQA retrieval/Evidence Packing assets may produce CandidateEvidence only.
- ASReview may provide reading priority under existing REVIEW-P0 behavior.
- Missing and conflicting evidence remain explicit; no pseudo-EvidenceSpan is created.

Basic active-learning ranking is treated as an implementation enhancement of
existing review requirements. Full experiment management, simulation, model
comparison, and a standalone screening workbench remain P1.

### Data, statistics, and figures

- Pandera is the planned P0 runtime validator.
- Great Expectations remains a report/test design reference.
- SciPy and statsmodels provide deterministic supported methods.
- statsmodels Summary is not AnalysisResult.
- Matplotlib provides deterministic rendering from approved inputs.
- DVC does not replace DatasetVersion, DataTransformation, or ReproPackage.

### Manuscript and citation

- python-docx plus controlled OOXML handles supported DOCX structures.
- original DOCX Artifacts remain immutable.
- selected CSL resources require pinned, file-level rights metadata.
- a full Citation Engine remains isolated and experiment/governance gated.
- Zotero compatibility is limited to supported exchange formats and UX ideas.

### Agent

OpenAI Agents SDK is planned for M8 runtime mechanics. Reviewed ARS Workflow,
Prompt, Policy Marker, script, test, and golden assets may be adapted without
changing the single-Orchestrator, Prompt manifest, Tool whitelist, approval,
evidence, or audit boundaries.

## 5. Architecture alignment

`ARCHITECTURE.md` advances to version `1.4.0` and formalizes four layers:

```text
RECA DOMAIN CORE
CAPABILITY INTEGRATION
VENDORED RESEARCH ASSETS
EXTERNAL SERVICES
```

It also normalizes integration modes to:

```text
DIRECT_LIBRARY_INTEGRATION
PROVIDER_OR_ADAPTER_INTEGRATION
INDEPENDENT_SERVICE
ISOLATED_SERVICE
SELECTIVE_VENDOR
RESOURCE_SNAPSHOT
DESIGN_REFERENCE
```

The architecture no longer implies that every third-party capability requires
an Adapter. Stable narrow libraries may be used within Services; external APIs,
multiple implementations, complex conversion, offline replacement, license or
security isolation receive stronger boundaries as needed.

PaperQA DEC-006 now permits deep selective reuse of retrieval, Evidence Packing,
Prompt, and tests while rejecting takeover of RECA's literature domain, project
state, vector authority, or Agent state. ASReview, Citation, Agents SDK, ARS,
CSL resources, and Zotero reference boundaries are now explicit.

## 6. Module README alignment

Backend README guidance now reflects the modular monolith rather than the
upstream template's obsolete `models.py`/`crud.py` instructions.

- `adapters/`: external APIs, multiple implementations, complex conversion,
  offline substitution, license/security isolation.
- `services/`: all business authority and upstream result normalization.
- `repositories/`: project-scoped persistence and pgvector version boundaries.
- `tools/`: deterministic tools separated from Agent Tool wrappers.
- `agents/`: M1 Prompt manifest governance and M8 runtime.
- Vendor assets: never enter ordinary modules without provenance.

Frontend guidance now requires Bun and preserves generated/adapter separation.
Feature and vendor-integration READMEs record PDF.js, TanStack Table, React Flow,
and Zotero boundaries without creating any code or empty module.

## 7. Stable contract preservation

| Contract type | Before | After | Change |
| --- | ---: | ---: | ---: |
| Unique Requirement IDs in product documents | 181 | 181 | 0 |
| API paths | Formal contract files unchanged | Formal contract files unchanged | 0 |
| Agent Tool names | Formal contract files unchanged | Formal contract files unchanged | 0 |
| Milestone IDs | Roadmap files unchanged | Roadmap files unchanged | 0 |

Data-model, API/AI/Tool contract, test, security, and roadmap authorities are not
modified. New project names and integration-mode labels are architecture prose,
not new domain enums, Schemas, API fields, or Tool names.

## 8. Status accuracy

Implemented statements are limited to repository facts such as the internalized
template baseline, Celery/Valkey/pgvector/GROBID foundations, and the existing
TanStack Table dependency. Planned scientific workflows remain labelled planned;
PaperQA2, ASReview, the full Citation Engine, and ARS asset adoption remain
experiment-required. Great Expectations, DVC, and Zotero remain researched or
reference-only.

## 9. No-code-change confirmation

No backend or frontend source file is created or modified. No dependency,
Compose, CI, migration, lockfile, generated client, test, security policy,
data-model contract, API contract, Tool contract, or roadmap file is changed.
