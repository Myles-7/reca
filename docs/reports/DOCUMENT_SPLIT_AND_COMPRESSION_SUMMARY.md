# Documentation Split and Compression Summary

> Report date: 2026-07-31
> Branch: `docs/document-split-compression`
> Documentation status: `Conditional Approval`
> Result: `PASS`
> This report records verification results. It does not approve M1 development, select a root license, create a tag, or change security policy.

## 1. Scope

This work split and compressed the nine formal RECA entry documents while preserving their authority, stable identifiers and development constraints:

- `README.md`;
- `AGENTS.md`;
- `docs/PRODUCT_REQUIREMENTS.md`;
- `docs/ARCHITECTURE.md`;
- `docs/DATA_MODEL_AND_WORKFLOW.md`;
- `docs/API_AI_TOOL_CONTRACTS.md`;
- `docs/TEST_AND_ACCEPTANCE.md`;
- `docs/SECURITY_AND_OPEN_SOURCE.md`;
- `docs/IMPLEMENTATION_ROADMAP.md`.

The work created 44 focused subordinate documents for product, architecture, data model, contracts, testing, roadmap, development and security. It also created a machine-comparable Phase 0 baseline, a section migration map, an ARS-Codex source/ADR record and this final verification report.

## 2. Non-goals

This work did not:

- change backend, frontend, Compose, CI, migrations, generated clients or dependency locks;
- add, remove, upgrade or downgrade P0/P1 requirements;
- change API, Schema, Tool, enum, error-code or acceptance semantics;
- introduce a runtime ARS-Codex dependency or free multi-Agent system;
- move formal Agent runtime earlier than M8;
- optimize or relax security controls;
- decide the root project license;
- change documentation to `APPROVED FOR M1 DEVELOPMENT`;
- create `docs-m1-approved` or any other approval tag.

## 3. Modified files

Tracked documentation files modified by the complete repair and split work are:

- `README.md` and `AGENTS.md`;
- the seven `docs/*` formal domain entry documents;
- `docs/reports/M0_DEVELOPMENT_SUMMARY.md`;
- `tests/golden/README.md`.

The M0 summary and golden-set README changes are documentation consistency changes only. No executable test fixture, application source or generated artifact was changed.

## 4. Added files

The final worktree adds 62 documentation or machine-readable documentation-baseline files, including this report:

| Group | Count | Content |
| --- | ---: | --- |
| Product | 5 | Workflow-specific product requirements |
| Architecture | 4 | Components, flows, Agent/async and operations |
| Data model | 5 | Domain groups plus state machines and invariants |
| Contracts | 6 | Common/API, AI Schema and Agent Tool contracts |
| Testing | 5 | M0 baseline, strategy, metrics, integration/security and E2E gates |
| Roadmap | 11 | M1-M9 milestone files plus delivery and risk/release rules |
| Development | 4 | Codex, backend, frontend and test/Git rules |
| Security | 4 | Controls, file/model/Agent, operations and open-source governance |
| ADR and source research | 2 | ARS-Codex source record and ADR-001 |
| Reports and baseline lists | 16 | Inventory, migration/repair/final reports and 11 sorted identifier lists |

The complete added-file list remains visible through Git and the directory navigation in each formal entry document; this report groups it to avoid duplicating the authoritative navigation indexes.

## 5. Archived files

One non-authoritative historical file was created:

| File | Lines | Status | Purpose |
| --- | ---: | --- | --- |
| `docs/archive/README_PRE_M1_LONGFORM.md` | 78 | Historical, non-authoritative | Preserves unique pre-M1 README history that does not belong in the project entry document |

Pure duplication was not copied into the archive. `docs/archive/` is excluded from Codex authority and task-reading matrices.

## 6. Before/after metrics

Line counts use the same line-oriented method as the Phase 0 inventory. “Subordinate lines” counts the completed children owned by that entry document; archived and report files are excluded. Compression is the reduction of the entry document itself.

| Document | Original lines | New lines | Subordinate lines | Compression |
| --- | ---: | ---: | ---: | ---: |
| `README.md` | 2,168 | 346 | 0 | 84.0% |
| `AGENTS.md` | 2,968 | 406 | 788 | 86.3% |
| `docs/PRODUCT_REQUIREMENTS.md` | 3,584 | 468 | 3,108 | 86.9% |
| `docs/ARCHITECTURE.md` | 3,398 | 606 | 2,881 | 82.2% |
| `docs/DATA_MODEL_AND_WORKFLOW.md` | 4,223 | 603 | 3,722 | 85.7% |
| `docs/API_AI_TOOL_CONTRACTS.md` | 5,104 | 450 | 4,959 | 91.2% |
| `docs/TEST_AND_ACCEPTANCE.md` | 3,804 | 474 | 3,642 | 87.5% |
| `docs/SECURITY_AND_OPEN_SOURCE.md` | 4,091 | 364 | 3,911 | 91.1% |
| `docs/IMPLEMENTATION_ROADMAP.md` | 4,166 | 475 | 3,924 | 88.6% |

Aggregate metrics:

| Metric | Before | After | Change |
| --- | ---: | ---: | ---: |
| Nine entry documents | 33,506 | 4,192 | -29,314 lines / 87.5% |
| Formal split scope: entries plus 44 children | 33,506 | 31,127 | -2,379 lines / 7.1% |
| Subordinate documents | 0 | 26,935 | +44 focused documents |
| Archive | 0 | 78 | +1 historical file |

After accounting for 26,935 migrated subordinate lines and 78 archived lines, the conservative net estimate of removed duplicate material is 2,301 lines. This estimate understates deduplication because new navigation headers, authority declarations, return links and explicit anchors add lines that did not exist in the baseline.

The largest formal subordinate document is `docs/data-model/STATE_MACHINES_AND_INVARIANTS.md` at 1,446 lines.

Files over 1,200 lines:

| File | Lines | Retention reason |
| --- | ---: | --- |
| `docs/data-model/STATE_MACHINES_AND_INVARIANTS.md` | 1,446 | Holds the unique complete state, transition, constraint, project-isolation, invalidation and data-access invariants; further splitting would raise cross-file consistency risk. |
| `docs/testing/E2E_ACCEPTANCE_AND_RELEASE_GATES.md` | 1,412 | Holds all stable Acceptance IDs, E2E flows, MANU-P0-018, release gates and report templates in one acceptance authority. |

## 7. Section migration map

The authoritative migration record is [`DOCUMENT_SECTION_MIGRATION_MAP.md`](./DOCUMENT_SECTION_MIGRATION_MAP.md).

| Phase | Result |
| --- | --- |
| 0 | Baseline inventory and sorted identifier lists created without changing formal text |
| 1 | Target directories, document skeletons and navigation contract created |
| 2 | README and AGENTS compressed; detailed rules moved; README history archived |
| 3 | Product requirements split by research workflow with stable requirement anchors |
| 4 | Architecture split into components, flows, Agent/async and operations |
| 5 | Roadmap split into M1-M9 and shared delivery/risk files |
| 6 | Data models split by domain; all invariants consolidated without simplification |
| 7 | API, AI Schema and Agent Tool contracts split without stable-string loss |
| 8 | Testing, metrics and acceptance gates split with stable AC anchors |
| 9 | Security and open-source governance structurally split without optimization |
| 10 | Global authority, navigation, explicit anchors and migration completion normalized |

All 44 subordinate documents now state `Migration status: COMPLETE`.

## 8. Deduplication authority map

| Topic | Unique complete authority |
| --- | --- |
| Project positioning | `README.md` |
| AI advice, deterministic computation and user confirmation | `docs/PRODUCT_REQUIREMENTS.md` |
| Original-object immutability | `docs/data-model/STATE_MACHINES_AND_INVARIANTS.md` |
| ApprovalRecord | `docs/data-model/FOUNDATION_AND_PROJECT_MODELS.md` |
| Modular monolith | `docs/ARCHITECTURE.md` |
| Single orchestrator Agent | `docs/architecture/AGENT_ASYNC_AND_DEGRADATION.md` |
| M0 As-Built evidence | `docs/reports/M0_DEVELOPMENT_SUMMARY.md` |
| M0 Regression Baseline | `docs/testing/M0_REGRESSION_BASELINE.md` |
| Root license status | `docs/security/OPEN_SOURCE_GOVERNANCE.md` |
| ARS-Codex decision | `docs/decisions/ADR-001-ARS-CODEX-USAGE.md` |
| ProjectContextSnapshot | `docs/data-model/MANUSCRIPT_AGENT_AND_EXPORT_MODELS.md` |
| Prompt manifest and ModelInvocation contract | `docs/contracts/AI_SCHEMA_CONTRACTS.md` |
| requested/max/effective data access invariant | `docs/data-model/STATE_MACHINES_AND_INVARIANTS.md` |
| EvidenceSpan | `docs/data-model/LITERATURE_AND_EVIDENCE_MODELS.md` |
| MANU-P0-018 requirement | `docs/product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md` |

Necessary repetition is limited to README summaries, AGENTS redlines, entry-document summaries and prominent M0 regression warnings. Detailed fields, states, endpoints, tests and governance rules remain in their single authorities.

## 9. Stable identifier verification

The current formal-document authority scope was compared with the sorted Phase 0 files in [`document-split-baseline/`](./document-split-baseline/). The error-code and enum lists remain conservative candidate sets as documented in the baseline inventory.

| Type | Baseline | Current | Removed | Added | Renamed | Result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Requirement IDs | 181 | 181 | 0 | 0 | 0 | PASS |
| Acceptance IDs | 16 | 16 | 0 | 0 | 0 | PASS |
| API paths | 236 | 236 | 0 | 0 | 0 | PASS |
| Error-code candidates | 87 | 87 | 0 | 0 | 0 | PASS |
| Schema names | 16 | 16 | 0 | 0 | 0 | PASS |
| Agent Tool names | 51 | 51 | 0 | 0 | 0 | PASS |
| Enum/value candidates | 401 | 401 | 0 | 0 | 0 | PASS |
| Milestone IDs/tokens | 20 | 20 | 0 | 0 | 0 | PASS |
| ADR IDs | 1 | 1 | 0 | 0 | 0 | PASS |
| M0 Issue IDs | 4 | 4 | 0 | 0 | 0 | PASS |

No new business contract identifier was introduced. New identifiers are explicit HTML anchors, navigation targets and document/report identifiers only. There are 302 explicit anchors and no duplicate anchor ID.

`M0-01` through `M0-08` remain historical execution stages, `M0-FIX` remains a repair-stage token and `M0-ISSUE` remains an issue prefix; none was reclassified as an M1-M9 milestone.

## 10. Link validation

Final Markdown validation covers README, AGENTS and all Markdown files under `docs/`:

- missing relative files: 0;
- missing referenced fragments: 0;
- orphan completed subordinate documents: 0;
- subordinate documents without an entry return link: 0;
- duplicate explicit anchors: 0;
- authoritative links using absolute local disk paths: 0.

Twenty-five duplicate-heading groups remain. They are local structural headings such as “字段”, “状态”, “步骤” and “预期”, plus historical M0 review headings. Stable references use explicit anchors and do not depend on these ambiguous generated slugs, so the headings were not mechanically renamed.

## 11. Approval status

Documentation remains `Conditional Approval` across all nine entry documents and all completed subordinate documents.

This split does not grant `APPROVED FOR M1 DEVELOPMENT`. That status requires a separate project-owner review and decision. No approval tag was created.

## 12. Deferred security optimization

Security policy classification and P0/P1 optimization are explicitly deferred to a separate task. Phase 9 and this final phase only moved, deduplicated and verified existing requirements. No MUST was weakened, no blocker became advisory, and no project-isolation, file-validation, model-data, prompt-injection, Tool, approval or license-review rule was removed.

## 13. Critical manual verification

| Check | Verified result |
| --- | --- |
| M0 status | `COMPLETED` |
| M1 Entry | `ALLOWED` |
| M0 commit | `79825914c7c975e8be256a5a89abe812f486769e` |
| M0 tag | Annotated `m0-complete` peels to the M0 commit |
| Required CI | `backend-quality`, `frontend-quality`, `migration-test`, `compose-smoke`, `security-supply-chain`, `e2e-smoke` |
| Clean-room | Isolation, random secrets, empty/repeated migration, Worker/MinIO/API/client/security checks and scoped cleanup remain mandatory for applicable changes |
| Open LOW risks | `M0-ISSUE-0006` and `M0-ISSUE-0009` remain visible |
| Bun | `bun install --frozen-lockfile` and `bun run --cwd frontend ...` commands remain authoritative; no obsolete npm execution command was found |
| Celery | The only app construction is `backend/app/core/celery.py`; runtime path is `app.core.celery:celery_app` |
| Alembic | The authoritative migration directory is `backend/app/alembic/` |
| generated/adapter | `frontend/src/api/generated/` remains generated; handwritten compatibility remains in `frontend/src/api/adapter/` |
| Root license | `PENDING_GOVERNANCE_DECISION`; no root `LICENSE` exists |
| ARS-Codex | Research/clean-room reference only; absent from runtime and package dependencies |
| Prompt manifest | Planned Git-managed registry remains `backend/app/agents/prompts/prompt-manifest.yaml`; M1 establishes it, M8 consumes it |
| Data access | requested/max/effective three-layer semantics remain present and Service-enforced |
| Scoping | ResearchQuestionVersion domain state remains separate from model Scoping output state |
| EvidenceSpan | Failed location uses `NO_LOCATED_EVIDENCE`; no fabricated EvidenceSpan is created |
| Snapshot | Derived, hashed, versioned and minimized; AgentRun stores safe metadata rather than full sensitive state |
| MANU-P0-018 | Deterministic Competition Core and optional non-blocking P0-Full semantic review remain unchanged |
| Agent timing | Formal single-orchestrator Agent remains an M8 capability; free multi-Agent remains excluded |

## 14. Remaining questions

The following are real governance or contract decisions and were not silently resolved:

1. The project owner must select the root project license before a root `LICENSE` or distribution assertion is added.
2. The project owner must separately decide whether documentation becomes `APPROVED FOR M1 DEVELOPMENT` and whether an approval tag is created.
3. Security P0/P1 optimization and policy classification remain deferred to the next dedicated security task.
4. The original API material contains unresolved parameter-name aliases such as `{id}`, `{plan_id}` and resource-specific identifiers. They remain compatibility strings and were not merged or renamed.
5. The original contract does not define independent Project Member and generic Artifact CRUD paths. The gap remains documented; this split did not invent endpoints.

## 15. No-code-change confirmation

Git scope verification found no changes under:

- `backend/`;
- `frontend/`;
- `docker-compose.yml`;
- `.github/workflows/`;
- `backend/app/alembic/`;
- `bun.lock`;
- `uv.lock`;
- generated client files.

All worktree changes are Markdown documentation or Phase 0 sorted text baselines. `tests/golden/README.md` is documentation and contains no executable fixture change.

## 16. Final validation result

| Validation | Result |
| --- | --- |
| `git diff --check` | PASS |
| Markdown files and fragments | PASS, 0 missing |
| Absolute authoritative disk paths | PASS, 0 |
| Obsolete npm execution commands | PASS, 0 |
| Legacy Celery path | PASS, 0; one actual Celery app construction |
| Legacy migration path | PASS, 0 |
| Seed-path documentation | PASS; no obsolete documented seed command |
| Document status | PASS, `Conditional Approval` |
| Root license status | PASS, `PENDING_GOVERNANCE_DECISION` |
| Stable identifiers | PASS, unexpected removed 0, unexpected renamed 0 |
| Modified-file scope | PASS, documentation only |

Final result: `PASS`. This result certifies split/compression integrity only; it is not product, security or M1 development approval.
