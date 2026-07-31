# Open Source Alignment Phase 10: Test, Security, Roadmap, and Development Rules

- Date: 2026-07-31
- Status: Conditional Approval
- Scope: documentation only
- Root license: `PENDING_GOVERNANCE_DECISION`

## 1. Outcome

Phase 10 aligned the testing, security, milestone, development, and third-party notice documents with the researched open-source capability stack. No source code, dependency manifest, lockfile, Compose file, CI workflow, migration, generated client, Vendor content, or third-party asset was changed.

The governing implementation sequence is now:

```text
Research
→ Spike
→ Decision
→ Integration
```

Research and recommendation records remain evidence for a future decision, not proof that a package, service, Vendor snapshot, Prompt, script, test, style, or other asset has been incorporated.

## 2. Third-party acceptance matrix

Every actually incorporated project must verify:

1. Pinned version;
2. License and attribution;
3. Runtime and protocol compatibility;
4. Main demo effect;
5. Failure behavior and visible degradation;
6. Resource usage;
7. Offline or Recorded behavior;
8. Provider-neutral output Schema conversion;
9. Project isolation;
10. Reproducibility and implementation metadata.

Project-specific acceptance now covers GROBID, PaperQA2, ASReview, Pandera, SciPy/statsmodels, Matplotlib, the citation stack, OpenAI Agents SDK, and ARS-Codex. Upstream tests may be adapted only with fixed source, license, path, modification, and attribution records.

## 3. Security and license alignment

[OPEN_SOURCE_GOVERNANCE.md](../../security/OPEN_SOURCE_GOVERNANCE.md) now contains the complete researched-project classification matrix. Important decisions remain:

- PostgreSQL/pgvector uses the PostgreSQL License classification recorded for the pinned project/version.
- Matplotlib requires review of its custom license and bundled libraries/fonts.
- CSL styles require per-file `<rights>`, author, locale, Commit, hash, and modification review.
- citeproc-js remains deferred until its CPAL/AGPL metadata conflict and isolation/alternative decision are resolved.
- Zotero and Zotero Web Library remain `DESIGN_REFERENCE`; no AGPL source or assets were copied.
- ARS-Codex remains `NONCOMMERCIAL_INTENT_DECLARED`, requires CC BY-NC 4.0 attribution/isolation and commercialization review, and has not been copied.
- PaperQA2 and ASReview may be selectively reused only after the exact paths, dependencies, license obligations, output boundaries, and tests are approved.
- `NO_LICENSE_DO_NOT_COPY` and unknown-source content remain prohibited.

## 4. Roadmap alignment

M1-M9 now include milestone-specific Research, Spike, Decision, and Integration steps:

| Milestone | Open-source alignment |
| --- | --- |
| M1 | Source ledger, Vendor rules, implementation metadata, Prompt manifest, ARS asset mapping preparation |
| M2 | PyAlex, GROBID, grobid-client-python, PDF.js |
| M3 | PaperQA2 Spike, ASReview Spike, pgvector, literature matrix |
| M4 | Pandera runtime, GX design reference, DVC provenance ideas |
| M5 | SciPy, statsmodels, Matplotlib |
| M6 | python-docx, controlled OOXML, CSL resources, citation engine Spike, Zotero compatibility |
| M7 | React Flow visualization, ReproPackage dependency and upstream metadata |
| M8 | OpenAI Agents SDK, ARS Prompt/Workflow/Test adaptation, PaperQA/ASReview Tool wrappers |
| M9 | Version freeze, cache/offline behavior, degradation, Notices, licenses, and demo performance |

The formal single-Orchestrator Agent runtime boundary remains M8. M1 Prompt governance and ARS mapping do not create an earlier Agent runtime.

## 5. Development rules

The four development rule documents now require each open-source task to:

```text
Read research record
Verify pinned commit
Verify license
Run minimal spike
Compare with fallback
Choose boundary
Implement
Run upstream-adapted tests
Update attribution
Record limitations
```

Existing Service, project isolation, approval, Artifact immutability, Bun, generated-client, Alembic, Celery, and clean-room rules were preserved.

## 6. Third-party notices

[THIRD_PARTY_NOTICES.md](../../../THIRD_PARTY_NOTICES.md) restricts record status to:

```text
ALREADY_INTEGRATED
RESEARCHED
PLANNED
VENDORED
SELECTIVELY_COPIED
DIRECT_DEPENDENCY
INDEPENDENT_SERVICE
```

Repository evidence still supports `ALREADY_INTEGRATED` for the selectively internalized Full Stack FastAPI Template baseline, Celery, Valkey, pgvector, GROBID health infrastructure, and TanStack Table dependency. These entries do not claim that later milestone business capabilities are complete. All other researched projects remain `RESEARCHED` or `PLANNED`; no new dependency or copied content was declared.

## 7. M0 regression baseline

The following remain unchanged:

```text
M0 commit: 79825914c7c975e8be256a5a89abe812f486769e
tag: m0-complete
M0 status: COMPLETED
M1 Entry: ALLOWED
```

Required CI remains:

```text
backend-quality
frontend-quality
migration-test
compose-smoke
security-supply-chain
e2e-smoke
```

Infrastructure clean-room acceptance remains mandatory. `M0-ISSUE-0006` and `M0-ISSUE-0009` remain disclosed non-blocking LOW risks.

## 8. Stable contract preservation

This phase changed no Requirement ID, Acceptance ID, API path, Error Code, Schema name, Tool name, Enum value, Milestone ID, ADR ID, or M0 Issue ID. It added only normative testing, governance, workflow, and milestone implementation guidance.

## 9. Modified documents

- `docs/TEST_AND_ACCEPTANCE.md` and selected `docs/testing/` authorities;
- `docs/SECURITY_AND_OPEN_SOURCE.md` and `docs/security/OPEN_SOURCE_GOVERNANCE.md`;
- `docs/IMPLEMENTATION_ROADMAP.md`, `docs/roadmap/DELIVERY_WORKFLOW.md`, and M1-M9 milestone files;
- four `docs/development/` rule documents;
- `tests/unit/README.md`, `tests/integration/README.md`, `tests/e2e/README.md`, and `tests/golden/README.md`;
- `THIRD_PARTY_NOTICES.md`;
- this report.

## 10. Deferred

- Actual installation, service configuration, Fork, Vendor, Submodule, selective copy, Prompt/test reuse, or resource snapshot;
- actual project Spikes and runtime decisions;
- citeproc-js or alternative processor selection;
- ARS-Codex content selection and copying;
- root project license decision;
- any approval beyond `Conditional Approval`.

## 11. No-code-change confirmation

No code, dependency, infrastructure, CI, migration, lockfile, generated file, or third-party content was modified or added in Phase 10.
