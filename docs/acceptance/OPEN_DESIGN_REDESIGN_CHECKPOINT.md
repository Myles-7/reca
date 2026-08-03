# Open Design Redesign Checkpoint

Initialized: 2026-08-02 (Asia/Shanghai)

Purpose: preserve the in-progress M2 repository state before Open Design begins a visual rebuild. This checkpoint is WIP evidence only. It does not mark M2 complete and does not change any product behavior.

## Checkpoint identity

- Source branch: `feat/m2-research-literature`
- Source HEAD: `ac6447c081c881fedb818525871a8bd100410cb5`
- Source commit: `feat(m1): complete foundation milestone (#3)`
- Tag at source HEAD: `m1-complete`
- Source upstream: `origin/feat/m2-research-literature`
- Source upstream relation before checkpoint: ahead 0, behind 0
- Remote: `origin https://github.com/Myles-7/reca.git`
- Checkpoint branch: `checkpoint/m2-pre-open-design-redesign-20260802`
- Open Design branch: `design/m2-open-design-redesign`
- Open Design worktree: `D:\桌面\Recas\reca-open-design`
- Checkpoint commit: resolve with `git rev-parse checkpoint/m2-pre-open-design-redesign-20260802`
- Checkpoint semantics: local WIP snapshot, not an M2 completion commit or tag

The checkpoint commit is created with a temporary Git index. The source worktree and its real index remain dirty and unchanged, matching the state recorded below.

## M2 status

- Exit Gate: `FAIL`
- Milestone status: `M2 INCOMPLETE`
- `M2-ISSUE-0001` HIGH, Exit Gate blocking: prompt canonicalization lacks committed-tree/fresh-checkout evidence.
- `M2-ISSUE-0010` HIGH, Exit Gate blocking: QueryPlan, Literature, and Document have no Open Design pure UI or registered production routes.
- `M2-ISSUE-0008` LOW, non-blocking: Babel development dependency advisory.
- No M2 completion report or completion tag is authorized while these blockers remain open.

Authoritative status sources:

- `docs/acceptance/M2_EXIT_GATE_REPORT.md`
- `docs/acceptance/M2_ISSUE_REGISTER.md`

## Stage 6 validation and Stage 7 handoff refresh

Refreshed: 2026-08-03 (Asia/Shanghai)

```text
READY_FOR_CODEX_INTEGRATION=YES
UI BLOCKER=0
UI HIGH=0
```

This readiness applies to the typed Workspace integration boundary only. It
does not register production routes, close the overall M2 Exit Gate, or turn a
missing server capability into an available action.

- The unified Preview registers 70 typed fixtures: Query Plan 11, Literature
  14, Document 17, Research Question 15, and Project Workspace 13.
- The complete fixture matrix passes at 1440x900, 1024x768, and 390x844 in
  light and dark themes. Page, product-surface, and Workspace-root horizontal
  overflow checks pass for every fixture.
- Ready/loading layouts, long identifiers and metadata, pending/conflict,
  forbidden/read-only/permissions-unknown, degraded/unknown, retryability,
  Candidate/Formal Record, upload/parse, GROBID, and pypdf fallback states are
  represented by independent typed fixtures.
- Project Dialog focus trapping/restoration and Document Sheet initial focus,
  bidirectional trapping, Escape restoration, and reduced-motion behavior pass.
- Literature selection remains local. Event Log records only user intent and
  does not mutate fixture state or simulate a server success response.
- Query Plan retry is now shown only when the formal UI error projection has
  `retryable=true`; forbidden and other non-retryable errors remain closed.
- Remaining contract gaps stay fail-closed: Query Plan create capability is
  blocked by contract; Literature Job retry lacks a formal permission/action
  projection; production Route registration remains outside this handoff.

Current evidence commands: the five frontend gates pass, the full Playwright
shell reports 89 passed, and the Stage 6 matrix reports 30 passed. Five
representative passing Workspace screenshots are retained under
`frontend/test-results/` by the matrix run; failure screenshots are retained
only when Playwright reports a failure.

## Stage 7 production review and Stage 9 prerequisite

Reviewed: 2026-08-03 (Asia/Shanghai)

```text
STAGE_9_FRONTEND_PREREQUISITE=YES
M2_COMPLETE=NO
M2-ISSUE-0010=DOC_STALE_OPEN_AT_STAGE_7; RESOLVED_IN_STAGE_9
```

This section supersedes the earlier handoff statement that QueryPlan,
Literature, and Document production routes were absent. It does not rewrite the
historical checkpoint or authorize M2 completion.

- QueryPlan, Literature, and Document Open Design workspaces are injected by
  their production containers and registered as deep-linkable routes.
- QueryPlan and Research Question guards now reject Event IDs and optimistic
  versions that do not match the current server projection.
- Project Member, Artifact download, Job, and Approval Events are revalidated in
  containers against the projected target and formal actions.
- Project and Research Question queries reject cross-project response identities;
  Research Question rejects a mismatched current pointer before requesting its
  version history.
- Job SSE updates validate project/job identity, invalidate only the matching
  Project Job query, and reset the resume cursor when the active Job changes.
- Unknown Approval status remains readable but degraded and non-actionable.
- QueryPlan create remains blocked because no formal detail-workspace create
  capability is projected. Literature retry is enabled only for a matching
  failed Job with `retryable=true` and known project `job.retry` permission.
- Full frontend Playwright passes 114 tests. The five Workspace production smoke
  set passes within that run, and the five frontend gates pass on the reviewed
  worktree.
- Focused backend API tests were not runnable in this desktop environment: no
  project `uv`/virtual environment is available, global Python lacks `sqlmodel`,
  and the running API image does not contain the repository test tree. Backend
  source was not changed by this review.

## Frontend verification

Commands were run from the repository root against the exact dirty source
worktree.

| Command | Result | Evidence |
| --- | --- | --- |
| `bun run --cwd frontend format:check` | PASS | 161 files checked; no fixes applied |
| `bun run --cwd frontend lint` | PASS | 164 files checked; no fixes applied |
| `bun run --cwd frontend check:ui-boundaries` | PASS | 4/4 tests; ownership boundary clean |
| `bun run --cwd frontend check:production-mocks` | PASS | 6/6 tests; production mock guard clean |
| `bun run --cwd frontend build` | PASS | TypeScript and Vite build completed; 2262 modules transformed |
| `bun run --cwd frontend test:shell` | PASS | Playwright 48/48 passed |
| `git diff --check` | PASS | no whitespace errors; line-ending conversion warnings only |

## Baseline screenshots

Assets are stored in the external visualization bundle
`reca-m2-open-design-baseline-20260802` so the checkpoint does not add generated
binary files.

| Surface | Baseline | Current fact |
| --- | --- | --- |
| Project desktop | `project-desktop.png` | Available via typed fixture preview |
| Project mobile | `project-mobile.png` | Available via typed fixture preview |
| Research Question desktop | `research-question-desktop.png` | Available via typed fixture preview |
| Research Question mobile | `research-question-mobile.png` | Available via typed fixture preview |
| QueryPlan | `query-plan-current.png` | DOC_STALE historical baseline: route was then unregistered; Stage 9 production route is registered and vertically tested |
| Literature | `literature-current.png` | DOC_STALE historical baseline: route was then unregistered; Stage 9 production route is registered and vertically tested |
| Document | `document-current.png` | DOC_STALE historical baseline: route was then unregistered; Stage 9 production route is registered and vertically tested |

No temporary QueryPlan, Literature, or Document UI was created to obtain screenshots.

## Preview and fixture inventory

Current preview entry points:

- `/design-preview.html` -> `frontend/src/design-preview/main.tsx` -> `ProjectFixturesPreview`
- `/research-question-preview.html` -> `frontend/src/design-preview/research-question-main.tsx` -> `ResearchQuestionFixturesPreview`
- No QueryPlan, Literature, or Document preview entry exists.

Typed fixture sets:

- Project: `ready`, `loading`, `empty`, `error`, `forbidden`, `degraded`, `long-content`, `pending-approval`
- Research Question: `ready`, `loading`, `empty`, `error`, `forbidden`, `degraded`, `pending-confirmation`, `long-content`
- QueryPlan: ready, loading, degraded props; no preview entry
- Literature: ready, loading, degraded props; no preview entry
- Document: ready, loading, pypdf fallback, degraded props; no preview entry

Fixture source paths are protected and must not be replaced with API calls or untyped mock objects.

## Ownership boundary

Open Design may independently change pure visual implementation under:

- `frontend/src/features/query-plan/ui/` except `contracts.ts`
- `frontend/src/features/literature/ui/` except `contracts.ts`
- `frontend/src/features/documents/ui/` except `contracts.ts`
- Existing Project and Research Question pure UI only when the same contract boundary is preserved
- Dedicated design-preview composition files, provided production code never imports them

Codex-protected paths:

```text
frontend/src/api/**
frontend/src/routes/**
frontend/src/features/*/model.ts
frontend/src/features/*/mappers.ts
frontend/src/features/*/queries.ts
frontend/src/features/*/mutations.ts
frontend/src/features/*/containers/**
frontend/src/features/*/ui/contracts.ts
frontend/src/features/*/fixtures/**
```

Rules for Open Design:

- Inputs arrive only through typed Props/ViewModel values.
- User actions return only through Events/callback props.
- Loading, empty, error, forbidden, degraded, and unknown states remain explicit.
- Permissions come only from `allowed_actions` or the typed permission projection.
- Pure UI must not import API clients, TanStack Query, queries, mutations, containers, controllers, or fixtures.
- Unknown states render warning/degraded treatment and disable high-risk actions.

## Complete source-worktree inventory

Tracked modifications at checkpoint time:

```text
.env.example
.gitattributes
THIRD_PARTY_NOTICES.md
backend/app/adapters/README.md
backend/app/agents/prompts.py
backend/app/agents/prompts/governance-contract-test-1.0.0.txt
backend/app/agents/prompts/prompt-manifest.yaml
backend/app/agents/service.py
backend/app/api/main.py
backend/app/approvals/service.py
backend/app/artifacts/service.py
backend/app/core/config.py
backend/app/jobs/service.py
backend/app/main.py
backend/app/models.py
backend/app/projects/schemas.py
backend/app/projects/service.py
backend/app/workers/jobs.py
backend/pyproject.toml
backend/tests/agents/test_model_invocation_service.py
backend/tests/agents/test_prompt_manifest.py
backend/tests/alembic/test_migrations.py
backend/tests/approvals/test_approval_service.py
backend/tests/conftest.py
backend/tests/projects/test_service.py
docker-compose.yml
docs/contracts/AI_SCHEMA_CONTRACTS.md
docs/contracts/PROJECT_RESEARCH_AND_LITERATURE_API.md
docs/data-model/LITERATURE_AND_EVIDENCE_MODELS.md
docs/data-model/STATE_MACHINES_AND_INVARIANTS.md
docs/source-research/OPEN_SOURCE_INTEGRATION_MASTER_PLAN.md
docs/source-research/projects/grobid-client-python.md
docs/source-research/projects/grobid.md
docs/source-research/projects/pyalex.md
frontend/openapi.json
frontend/package.json
frontend/scripts/check-production-mocks.mjs
frontend/src/api/adapter/index.ts
frontend/src/api/generated/index.ts
frontend/src/api/generated/sdk.gen.ts
frontend/src/api/generated/types.gen.ts
frontend/src/features/README.md
frontend/src/features/projects/ProjectWorkspacePage.tsx
frontend/src/features/projects/mappers.ts
frontend/src/features/projects/model.ts
frontend/src/routeTree.gen.ts
frontend/tests/projects-mappers.spec.ts
frontend/tests/projects-workspace.spec.ts
scripts/ci/frontend-quality.sh
scripts/m0-acceptance.ps1
uv.lock
```

Untracked files at checkpoint time, including this report:

```text
backend/app/adapters/documents.py
backend/app/adapters/literature.py
backend/app/agents/prompts/query-plan-generation-1.0.0.txt
backend/app/agents/prompts/research-question-parse-1.0.0.txt
backend/app/agents/prompts/research-question-scoping-1.0.0.txt
backend/app/alembic/versions/0008_research_question_domain.py
backend/app/alembic/versions/0009_rq_scoping_job.py
backend/app/alembic/versions/0010_query_plan_domain.py
backend/app/alembic/versions/0011_literature_search.py
backend/app/alembic/versions/0012_document_upload.py
backend/app/api/routes/documents.py
backend/app/api/routes/literature.py
backend/app/api/routes/query_plans.py
backend/app/api/routes/research_questions.py
backend/app/documents/__init__.py
backend/app/documents/parsing.py
backend/app/documents/schemas.py
backend/app/documents/service.py
backend/app/literature/__init__.py
backend/app/literature/normalization.py
backend/app/literature/schemas.py
backend/app/literature/service.py
backend/app/query_plans/__init__.py
backend/app/query_plans/ai_schemas.py
backend/app/query_plans/fixtures/manifest.json
backend/app/query_plans/fixtures/query-plan-generation-recorded-v1.json
backend/app/query_plans/generation.py
backend/app/query_plans/schemas.py
backend/app/query_plans/service.py
backend/app/research_questions/__init__.py
backend/app/research_questions/ai_schemas.py
backend/app/research_questions/fixtures/manifest.json
backend/app/research_questions/fixtures/rq-parse-recorded-v1.json
backend/app/research_questions/fixtures/rq-scoping-candidates-recorded-v1.json
backend/app/research_questions/fixtures/rq-scoping-needs-input-mock-v1.json
backend/app/research_questions/schemas.py
backend/app/research_questions/scoping.py
backend/app/research_questions/service.py
backend/tests/adapters/test_literature.py
backend/tests/alembic/test_migration_runtime.py
backend/tests/api/routes/test_documents.py
backend/tests/api/routes/test_literature.py
backend/tests/api/routes/test_query_plans.py
backend/tests/api/routes/test_research_question_scoping.py
backend/tests/api/routes/test_research_questions.py
backend/tests/documents/__init__.py
backend/tests/documents/test_parse_workflow.py
backend/tests/documents/test_parsing.py
backend/tests/fixtures/openalex/works_recorded.json
backend/tests/integration/__init__.py
backend/tests/integration/test_m2_live_services.py
backend/tests/integration/test_m2_vertical_demo.py
backend/tests/query_plans/__init__.py
backend/tests/query_plans/test_schemas.py
backend/tests/query_plans/test_service_and_generation.py
backend/tests/research_questions/__init__.py
backend/tests/research_questions/test_ai_schemas.py
backend/tests/research_questions/test_scoping_service.py
backend/tests/research_questions/test_service.py
docs/acceptance/M2_EXIT_GATE_REPORT.md
docs/acceptance/M2_ISSUE_REGISTER.md
docs/acceptance/M2_VERTICAL_INTEGRATION_REPORT.md
docs/acceptance/OPEN_DESIGN_REDESIGN_CHECKPOINT.md
docs/development/M2_FRONTEND_FEATURE_TEMPLATE.md
docs/source-research/M2_GROBID_PYPDF_SPIKE.md
docs/source-research/M2_OPENALEX_PYALEX_SPIKE.md
frontend/design-preview.html
frontend/research-question-preview.html
frontend/scripts/check-production-mocks.test.mjs
frontend/scripts/check-ui-boundaries.mjs
frontend/scripts/check-ui-boundaries.test.mjs
frontend/src/design-preview/ProjectFixturesPreview.tsx
frontend/src/design-preview/ResearchQuestionFixturesPreview.tsx
frontend/src/design-preview/main.tsx
frontend/src/design-preview/research-question-main.tsx
frontend/src/features/documents/containers/DocumentContainer.tsx
frontend/src/features/documents/fixtures/index.ts
frontend/src/features/documents/mappers.ts
frontend/src/features/documents/model.ts
frontend/src/features/documents/mutations.ts
frontend/src/features/documents/queries.ts
frontend/src/features/documents/ui/contracts.ts
frontend/src/features/literature/containers/LiteratureContainer.tsx
frontend/src/features/literature/fixtures/index.ts
frontend/src/features/literature/mappers.ts
frontend/src/features/literature/model.ts
frontend/src/features/literature/mutations.ts
frontend/src/features/literature/queries.ts
frontend/src/features/literature/ui/contracts.ts
frontend/src/features/projects/cache.ts
frontend/src/features/projects/containers/ApprovalsContainer.tsx
frontend/src/features/projects/containers/ArtifactsContainer.tsx
frontend/src/features/projects/containers/AuditContainer.tsx
frontend/src/features/projects/containers/JobsContainer.tsx
frontend/src/features/projects/containers/MembersContainer.tsx
frontend/src/features/projects/containers/OverviewContainer.tsx
frontend/src/features/projects/containers/ProjectActionsContainer.tsx
frontend/src/features/projects/fixtures/index.ts
frontend/src/features/projects/fixtures/types.ts
frontend/src/features/projects/mutations.ts
frontend/src/features/projects/ui/ApprovalsPanel.tsx
frontend/src/features/projects/ui/ArtifactsPanel.tsx
frontend/src/features/projects/ui/AuditPanel.tsx
frontend/src/features/projects/ui/JobsPanel.tsx
frontend/src/features/projects/ui/MembersPanel.tsx
frontend/src/features/projects/ui/OverviewPanel.tsx
frontend/src/features/projects/ui/ProjectActions.tsx
frontend/src/features/projects/ui/contracts.ts
frontend/src/features/query-plan/containers/QueryPlanContainer.tsx
frontend/src/features/query-plan/fixtures/index.ts
frontend/src/features/query-plan/mappers.ts
frontend/src/features/query-plan/model.ts
frontend/src/features/query-plan/mutations.ts
frontend/src/features/query-plan/queries.ts
frontend/src/features/query-plan/ui/contracts.ts
frontend/src/features/research-question/containers/ResearchQuestionContainer.tsx
frontend/src/features/research-question/fixtures/index.ts
frontend/src/features/research-question/mappers.ts
frontend/src/features/research-question/model.ts
frontend/src/features/research-question/mutations.ts
frontend/src/features/research-question/queries.ts
frontend/src/features/research-question/ui/ResearchQuestionWorkspace.tsx
frontend/src/features/research-question/ui/contracts.ts
frontend/src/routes/_layout/projects.$projectId_.research-question.tsx
frontend/tests/projects-cache.spec.ts
frontend/tests/projects-fixtures.spec.ts
frontend/tests/projects-m2-frontend-contracts.spec.ts
frontend/tests/projects-mutations.spec.ts
frontend/tests/projects-research-question-template.spec.ts
```

## Recovery

Inspect the immutable checkpoint without changing the source worktree:

```powershell
git show --stat checkpoint/m2-pre-open-design-redesign-20260802
git diff ac6447c checkpoint/m2-pre-open-design-redesign-20260802
```

Recreate an independent recovery worktree at a new path:

```powershell
git worktree add --detach D:\桌面\Recas\reca-m2-recovery checkpoint/m2-pre-open-design-redesign-20260802
```

Recreate the Open Design worktree if it is later removed:

```powershell
git worktree add D:\桌面\Recas\reca-open-design design/m2-open-design-redesign
```

Do not use `reset`, `checkout`, `stash pop`, or deletion as a recovery procedure. Compare or restore selected files from the checkpoint into a separate worktree first.

## Start decision

Open Design may begin only in `D:\桌面\Recas\reca-open-design`, on branch `design/m2-open-design-redesign`, after verifying the checkpoint ref and the six frontend gates above. The source M2 worktree remains the Codex business-development workspace.
