# Documentation Consistency Repair Summary

## 1. Modified files

`README.md`, `AGENTS.md`, `docs/PRODUCT_REQUIREMENTS.md`,
`docs/ARCHITECTURE.md`, `docs/DATA_MODEL_AND_WORKFLOW.md`,
`docs/API_AI_TOOL_CONTRACTS.md`, `docs/TEST_AND_ACCEPTANCE.md`,
`docs/SECURITY_AND_OPEN_SOURCE.md`, `docs/IMPLEMENTATION_ROADMAP.md`,
`docs/reports/M0_DEVELOPMENT_SUMMARY.md`,
`docs/source-research/academic-research-skills-codex.md` and this report.

## 2. Resolved issues

* **DOC-001 / DOC-002:** README and roadmap now record M0 as completed at
  `79825914c7c975e8be256a5a89abe812f486769e` / `m0-complete`, with required
  CI PASS, clean-room PASS and M1 entry ALLOWED. The M0 roadmap is a historical
  completed record with actual delivery, deferred work, evidence and LOW risks.
* **DOC-003 / DOC-004:** current M0 paths and commands now use Bun, the sole
  `app.core.celery:celery_app`, `backend/app/alembic/`, observability, actual
  OpenAPI client locations and only existing scripts. Current and target
  directory structures are explicitly separated.
* **DOC-005:** all formal documents now state
  `PENDING_GOVERNANCE_DECISION`; no root `LICENSE` is asserted. Third-party
  notices remain separate and were not modified because no upstream material
  was copied.
* **DOC-006 / DOC-008:** six M0 required CI jobs, clean-room triggers, two LOW
  risks and the non-applicable safety stashes are now mandatory M1+ guidance.
* **DOC-007:** architecture/API document the M0 Settings, health endpoints,
  `UNCONFIGURED` provider behavior, request logging, worker smoke boundary,
  MinIO/GROBID limits and generated-client boundary.
* **DOC-009 / DOC-010 / DOC-011:** M1 establishes a Git-managed PromptContract
  manifest before M2/M3 model use; ModelInvocation tracks prompt identity/hash
  and requested/max/effective data-access levels.
* **DOC-012 / DOC-013 / DOC-014:** ResearchQuestionVersion and AI Scoping
  states are distinct; read-scope enum is unified; an absent location is a
  LiteratureExtractionField state, not a fabricated EvidenceSpan.
* **DOC-015:** ProjectContextSnapshot and AgentRun use one derived, hashed,
  versioned, privacy-minimised contract.
* **DOC-016:** `MANU-P0-018` is in the feature table, API Job/AuditResult,
  M6 delivery, Competition Core/P0-Full boundary and `AC-MANU-P0-018`.
* **DOC-017 / DOC-018:** ARS-Codex source record/ADR are authoritative;
  a shared conflict-resolution matrix separates current facts from future
  specification authority.
* **DOC-019 to DOC-021 / DOC-023 to DOC-026:** formal-document versions and
  change records were aligned; implemented-versus-planned technology, internal
  network boundaries, traceability matrix, M0 summary spelling/history marker
  and key names/enums were normalised.

## 3. Authoritative decisions

* **Root license status:** `PENDING_GOVERNANCE_DECISION`; no root LICENSE is
  created or implied.
* **Prompt persistence:** P0 code-managed
  `backend/app/agents/prompts/prompt-manifest.yaml`, not a database-editable
  Prompt table.
* **Research scoping status:** ResearchQuestionVersion uses `DRAFT`,
  `NEEDS_INPUT`, `READY`, `CONFIRMED`, `SUPERSEDED`; model output uses
  `NEEDS_USER_INPUT`, `CANDIDATES_READY`, `INSUFFICIENT_EVIDENCE`,
  `OUT_OF_SCOPE`.
* **Evidence read scope:** `UNKNOWN`, `ABSTRACT`, `SECTIONS`,
  `FULL_TEXT_DECLARED`; parser coverage is separate.
* **Snapshot persistence:** a derived read-only DTO; AgentRun stores safe
  metadata and hashes rather than a full sensitive snapshot.
* **MANU-P0-018 scope:** deterministic Competition Core plus optional,
  non-blocking P0-Full semantic review.

## 4. M0 as-built synchronization

Verified against actual `main`, `m0-complete`, M0 acceptance materials,
`.github/workflows/m0-quality.yml`, `docker-compose.yml`, lock files and
implemented source paths. M0 remains engineering foundation only; it does not
claim M1 research-domain objects, business Jobs, Artifact workflow or PDF
business parsing.

## 5. Cross-document consistency checks

Checked M0 facts, directory/command references, root-license state, Prompt
manifest, data-access levels, ResearchQuestion states, EvidenceSpan behavior,
ProjectContextSnapshot, MANU-P0-018, source-research/ADR references, current
vs target structure and M1—M9 mapping.

## 6. Validation

* `git show` / `show-ref`: `main` and `m0-complete` resolve to the M0 completion commit.
* Read M0 summary, acceptance report, issue register and final review.
* Verified actual Compose service/network exposure, CI jobs, Bun lock, Celery,
  Alembic, observability and generated-client paths.
* Searched for obsolete npm, seed, duplicate migration and legacy enum paths.
* `git diff --check` passed.

## 7. Remaining questions

* The project owner must decide the root project license before any `LICENSE`
  file or distribution assertion is made.
* Documentation remains `CONDITIONAL APPROVAL`; the project owner must review
  this repair and explicitly set `APPROVED FOR M1 DEVELOPMENT`.
* DOC-022's optional larger-scale splitting/shortening of long historical
  documents is not performed here; new rules were moved into their relevant
  authority sections and no new post-conclusion rule block remains.

## 8. No-code-change confirmation

No backend, frontend, Compose, CI, migration or dependency-lock file was
modified. This repair changes documentation and source-research governance
records only.
