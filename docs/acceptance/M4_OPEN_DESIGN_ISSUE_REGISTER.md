# RECA M4 Open Design Issue Register

## Stage 0 Baseline

```text
Assessment date: 2026-08-04 (Asia/Shanghai)
Stage: M4 Open Design Stage 0
Target worktree: D:/桌面/Recas/reca-m4-open-design
Target branch: design/m4-data-workbench
Target entry HEAD: 0e3c39dde65feaa8f784fd5fcfb1055cb557bb3c
Source worktree: D:/桌面/Recas/reca
Source branch: feat/m2-research-literature
Source HEAD: 0e3c39dde65feaa8f784fd5fcfb1055cb557bb3c
M3 design worktree: D:/桌面/Recas/reca-m3-open-design
M3 design branch: design/m3-evidence-workbench
M3 design HEAD: d0541567cf049347e4b4eec4ab140054afabdc0b
READY_FOR_OPEN_DESIGN=YES
PRODUCTION_INTEGRATION_COMPLETE=NO
NEXT_STAGE_EXECUTED=NO
```

The target path did not exist. It was created non-destructively from the formal
repository HEAD. The formal repository and M3 design worktree both had preserved
uncommitted changes; neither was reset, cleaned, stashed, checked out or overwritten.

## Controlled Sync

- Method: file-level SHA-256 comparison and copy from the formal repository.
- Scope: frontend package/config, shared components, unified Design Preview, integrated
  M3 feature dependencies, M4 `data-workspace`, generated/adapter compile snapshot,
  production routes, named frontend guards, and M3/M4 acceptance documents.
- Excluded: backend, migration `0014`, databases, object storage, `.env`, `.playwright-cli`,
  `.tanstack`, `dist`, `test-results`, Playwright reports and temporary environments.
- Compared files: `196`.
- Copied because hashes differed or target was absent: `66`.
- Verified without copy: `130`.
- Source/target SHA-256 mismatches after sync: `0`.
- Exact manifest: [M4_OPEN_DESIGN_SYNC_MANIFEST.tsv](./M4_OPEN_DESIGN_SYNC_MANIFEST.tsv).

M3 visual baseline decision: the M3 design worktree hashes differ from the formal
repository, but the formal repository records `M3_EXIT=PASS`, production integration,
frontend/browser gates and a later accepted implementation. The formal repository is
therefore the single M4 frontend baseline. No file was copied from the dirty M3 worktree.

## Ownership

Open Design may modify in later authorized stages:

- `frontend/src/features/data-workspace/ui/DataWorkspace.tsx`;
- `frontend/src/features/data-workspace/ui/data-workspace.css`;
- additional pure display files under `frontend/src/features/data-workspace/ui/**`;
- M4-only presentation branches under `frontend/src/design-preview/**`;
- explicitly authorized shared pure display components;
- M4 Open Design issue, acceptance and handoff documents.

Protected inputs remain read-only:

- data-workspace model, mapper, query, mutation, container, fixtures, contracts and
  route contract;
- generated client, adapter, OpenAPI, production routes and `routeTree.gen.ts`;
- frontend scripts/tests, backend, migration, Worker and storage/runtime data;
- M2/M3 production Workspaces unless a later handoff explicitly authorizes a shared fix.

## Known Integration Limits

### M4-ISSUE-0014

Some M4 success responses remain generated as `unknown`/open records. The adapter owns
temporary structural validation and must remain fail-closed. Open Design must not infer
additional DTO fields or use fixture shape as an API guarantee.

### M4-ISSUE-0015

There is no formal Dataset version-history list or independent Transformation-detail read
projection. UI may show only current ViewModel facts and disabled/integration-pending
presentation in Preview chrome; it must not synthesize production history or recovery.

## Stage 0 Gates

| Gate | Result | Evidence |
| --- | --- | --- |
| Target branch/worktree creation | PASS | New branch and worktree created from formal safe HEAD |
| Exact sync manifest | PASS | 196 files; 0 post-copy hash mismatches |
| Dependency installation | PASS | `bun install --frozen-lockfile`; 273 packages installed |
| TypeScript no-emit | PASS | `bunx tsc -p frontend/tsconfig.build.json --noEmit` |
| M4 fixture contract | PASS | `check:m4-fixtures`; 6/6 tests passed |
| UI ownership boundary | PASS | `check:ui-boundaries`; 4/4 tests passed; guard clean |
| Production mock guard | PASS | `check:production-mocks`; 6/6 tests passed; guard clean |
| Frontend build | PASS | TypeScript/Vite build completed; generated route snapshot restored from formal source afterward |
| `git diff --check` | PASS | No whitespace errors after Stage 0 documentation update |

## Stage 0 Result

```text
READY_FOR_OPEN_DESIGN=YES
M4_OPEN_DESIGN_CAN_START=YES
HANDOFF_SYNC_RESULT=PASS
OPEN_DESIGN_STAGE_RESULT=PASS
NEXT_STAGE_EXECUTED=NO
```

Stage 0 changed synchronization and acceptance documentation only. The synchronized
frontend baseline remains byte-identical to the formal source manifest, and no M4
DataWorkspace visual implementation or Stage 1 work was performed.

## Open Design Issues

### M4-OD-0001: UI Contract Registry is stale relative to the M4 handoff

- stage: `M4 Open Design Stage 0`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `documentation / contract readiness`
- page/surface: `Data Workspace`
- fixture: `all`
- viewport: `all`
- theme: `all`
- observed_behavior: `FRONTEND_DESIGN_INTEGRATION_RULES.md` still lists Data Quality
  Workspace as route/ViewModel/UI/Mock `TBD` or `NOT_STARTED`, while the later M4 handoff,
  TypeScript model/contracts and typed fixtures exist and state `READY_FOR_OPEN_DESIGN=YES`.
- expected_behavior: the registry should reference the actual frozen M4 paths and readiness
  without describing production integration as complete.
- evidence: M4 handoff sections 2-9 and the synchronized `data-workspace` TypeScript package.
- affected_ui_files: `none`
- contract_or_fixture_gap: documentation registry gap only; executable contracts exist.
- blocks_current_stage: `NO`
- blocks_codex_integration: `NO`
- safe_continuation: treat the newer M4 handoff and executable TypeScript as authoritative;
  do not modify the shared rules document from Open Design.
- resolution: Codex Stage 4.5 updated the shared UI Contract Registry with the frozen M4 route,
  ViewModel, UI contract, fixtures and Stage 5 entry state without claiming production integration.
- verification: registry paths and readiness markers match the executable formal repository.

### M4-OD-0002: Minimal DataWorkspace was not a stable multi-surface workbench

- stage: `M4 Open Design Stage 0-1`
- severity: `HIGH`
- status: `RESOLVED`
- area: `information architecture / responsive / accessibility`
- page/surface: `Data Workspace shell`
- fixture: `all`
- viewport: `1440x900, 1024x768, 390x844`
- theme: `Light and Dark`
- observed_behavior: the Stage 0 contract preview used an English vertical Band layout with
  a rail and one long document flow. It had no stable multi-surface navigation, contextual
  Inspector, Sheet/Dialog workflow or state-preserving loading shell.
- expected_behavior: one shared Workspace context with stable rail, primary work area and
  Inspector on desktop, controlled Sheet degradation on tablet/mobile and Chinese production copy.
- evidence: Stage 1 `DataWorkspace.tsx` now provides the shared rail/primary/Inspector shell,
  five stable views, responsive Sheet degradation and stable loading/error/empty geometry;
  `data-workspace.css` defines fixed pane/table/control dimensions and internal scrollers.
- affected_ui_files: `frontend/src/features/data-workspace/ui/DataWorkspace.tsx`,
  `frontend/src/features/data-workspace/ui/data-workspace.css`
- contract_or_fixture_gap: `NO`; Stage 1 consumes the relevant frozen Dataset/Version surface.
- blocks_current_stage: `NO`
- blocks_codex_integration: `NO`; Stage 3 and Codex Stage 4.5 browser acceptance pass.
- safe_continuation: retain the Stage 1 shell and complete Quality/Cleaning in Stage 2 without
  changing the shared Dataset/Version context; close visual coverage in Stage 3.
- resolution: implemented in M4 Open Design Stage 1.
- verification: format, lint, TypeScript, M4 fixtures, UI boundaries, production mocks and build
  pass; the complete Codex browser matrix passes in Stage 4.5.

### M4-OD-0003: Hidden worksheet selection auto-acknowledges risk

- stage: `M4 Open Design Stage 0-1`
- severity: `HIGH`
- status: `RESOLVED`
- area: `data safety / interaction`
- page/surface: `Worksheet selection`
- fixture: `xlsx-worksheets`
- viewport: `all`
- theme: `all`
- observed_behavior: the Stage 0 implementation clicked a hidden or very hidden worksheet and
  immediately emitted
  `select-worksheet` with `acknowledgeHidden=true`, derived from visibility, without a user
  confirmation Dialog.
- expected_behavior: hidden/very hidden risk remains visible and the formal acknowledge flag is
  sent only after an explicit confirmation with focus trap, Escape and focus restoration.
- evidence: Stage 1 `WorksheetStrip` routes visible worksheets to `acknowledgeHidden=false` and
  hidden/very hidden worksheets to a Radix Dialog before emitting `acknowledgeHidden=true`.
- affected_ui_files: `frontend/src/features/data-workspace/ui/DataWorkspace.tsx`,
  `frontend/src/features/data-workspace/ui/data-workspace.css`
- contract_or_fixture_gap: `NO`; the frozen event already provides `acknowledgeHidden`.
- blocks_current_stage: `NO`
- blocks_codex_integration: `NO`; representative hidden worksheet verification passes.
- safe_continuation: keep the explicit Dialog implementation and never bypass the formal
  capability; verify focus trap/Escape/restore after the protected fixture gap is corrected.
- resolution: explicit confirmation implemented without contract or fixture changes.
- verification: Codex Stage 4.5 Playwright verifies explicit acknowledgement, Dialog behavior and
  sanitized intent emission with the corrected XLSX fixture.

### M4-OD-0004: Empty Loadable state has no upload capability projection

- stage: `M4 Open Design Stage 1-2`
- severity: `MEDIUM`
- status: `RESOLVED_BY_CODEX_STAGE_4_5`
- area: `contract / empty state / permissions`
- page/surface: `Data Workspace empty shell`
- fixture: `empty`
- viewport: `1440x900, 1024x768, 390x844`
- theme: `Light and Dark`
- observed_behavior: `Loadable.empty` provides only a message, so the UI cannot determine
  whether `upload-dataset` is formally allowed or why it is disabled.
- expected_behavior: the empty Workspace preserves the shell and exposes upload only when a
  formal capability is available.
- evidence: `DataWorkspaceWorkspaceProps.content` empty branch and `projects/model.ts` Loadable.
- affected_ui_files: `frontend/src/features/data-workspace/ui/DataWorkspace.tsx`
- contract_or_fixture_gap: `YES`; no capability projection exists in the empty branch.
- blocks_current_stage: `NO`
- blocks_codex_integration: `NO`, resolved by Codex Stage 4.5.
- safe_continuation: retain the full empty shell but keep upload visibly disabled with a formal
  reason; do not infer permission or emit upload from the message-only state.
- resolution: Codex Stage 4.5 aligned the empty fixture with the production query contract. An
  empty project remains a ready `DataWorkspaceViewModel` with zero datasets and a formal
  `uploadDataset` capability; message-only `Loadable.empty` is no longer used to imply permission.
- verification: focused contract test confirms zero datasets with upload allowed; the complete
  fixture/viewport/theme browser matrix and frontend gates pass.

### M4-OD-0005: XLSX fixture disables worksheet selection with an inconsistent reason

- stage: `M4 Open Design Stage 1`
- severity: `HIGH`
- status: `RESOLVED_BY_CODEX_STAGE_4_5`
- area: `fixture / worksheet interaction`
- page/surface: `Worksheet selector and hidden worksheet Dialog`
- fixture: `xlsx-worksheets`
- viewport: `1440x900, 390x844`
- theme: `Light`
- observed_behavior: the fixture version is `CREATING`, but inherits `selectWorksheet.allowed=false`
  with disabled reason `The selected version is already AVAILABLE.`; all worksheet buttons are
  therefore disabled and the hidden confirmation path cannot be exercised.
- expected_behavior: the representative XLSX fixture should project a capability consistent with
  its version state so visible and hidden worksheet event paths can be verified.
- evidence: `dataWorkspaceXlsxFixture` overrides only `version` and inherits ready capabilities.
- affected_ui_files: `frontend/src/features/data-workspace/ui/DataWorkspace.tsx`
- contract_or_fixture_gap: `YES`; protected fixture/capability inconsistency.
- blocks_current_stage: `NO`
- blocks_codex_integration: `NO`, resolved by Codex Stage 4.5.
- safe_continuation: display every worksheet and the server disabled reason, keep all actions
  disabled, and retain the explicit confirmation implementation without changing the fixture.
- resolution: Codex Stage 4.5 made the XLSX fixture project `selectWorksheet.allowed=true` for its
  formal `CREATING` Version and disabled unrelated AVAILABLE-only actions.
- verification: the hidden worksheet Dialog and explicit `acknowledgeHidden=true` intent pass in
  the formal repository Playwright suite.

### M4-OD-0006: Chromium launch hangs before representative Stage 1/2 screenshots

- stage: `M4 Open Design Stage 1-2`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `visual acceptance environment`
- page/surface: `Data Workspace design preview`
- fixture: `ready, xlsx-worksheets, loading, quality completed, approval stale, transform running, transform failed, long-content`
- viewport: `1440x900, 390x844`
- theme: `Light`
- observed_behavior: both the screenshot matrix run and one instrumented single-page retry
  produced no output before the bounded timeout and required termination.
- expected_behavior: Chromium should launch and capture the representative Stage 1/2
  fixture/viewport sets, including root overflow and console-error assertions.
- evidence: two bounded Playwright attempts on 2026-08-04; no screenshots or browser processes
  remained after termination.
- affected_ui_files: `none`
- contract_or_fixture_gap: `NO`; environment execution gap.
- blocks_current_stage: `NO`
- blocks_codex_integration: `NO` at Stage 1; full visual acceptance remains required in Stage 3.
- safe_continuation: rely on passing static/type/build/boundary gates and preserve the prepared
  Stage 1/2 representative matrices; retry once in Stage 3 or a functioning browser environment.
- resolution: Stage 3 used an isolated Playwright port and forced `NODE_ENV=development`, avoiding
  both an unrelated reused Vite server and the inherited production-mode Preview guard.
- verification: the M4 Stage 3 suite passed 15/15, including all 30 fixtures at three viewports in
  Light/Dark and 20 representative screenshots.

## Stage 1 Acceptance

Implemented pure UI files:

- `frontend/src/features/data-workspace/ui/DataWorkspace.tsx`
- `frontend/src/features/data-workspace/ui/data-workspace.css`

Implemented surfaces and interactions: shared Dataset/Version rail, Workspace header, stable
Data/Columns/Quality/Cleaning/Versions navigation, responsive Inspector Sheet, upload Dialog,
Dataset Identity draft, explicit hidden worksheet confirmation, bounded masked preview table,
column dictionary and contract-limited field editing. Quality and Cleaning remain Stage 2 summary
slots; Approval, Transformation and complete history workflows were not started.

Gate coverage: affected Biome format/lint, TypeScript no-emit, `check:m4-fixtures` (6/6),
`check:ui-boundaries` (4/4), `check:production-mocks` (6/6) and frontend build pass. The ready,
XLSX, loading and long-content code paths are bundled, but their 1440/390 pixel screenshots are
pending under M4-OD-0006.

```text
OPEN_DESIGN_STAGE_RESULT=PASS_WITH_GAPS
NEXT_STAGE_EXECUTED=NO
```

### M4-OD-0007: Cleaning Action editor lacks a typed option and parameter projection

- stage: `M4 Open Design Stage 2`
- severity: `HIGH`
- status: `RESOLVED_BY_CODEX_STAGE_4_5`
- area: `contract / CleaningPlan editor`
- page/surface: `Cleaning view`
- fixture: `plan-draft, plan-needs-input, plan-ready`
- viewport: `all`
- theme: `Light and Dark`
- observed_behavior: the ViewModel exposes only Action summaries, while create/update Events accept
  open `Record<string, unknown>[]` values without typed action options or parameter schemas.
- expected_behavior: an authorized typed projection should define supported Action types,
  parameters, validation and safe defaults before a production editor can emit create/update.
- evidence: `CleaningPlanViewModel.actions` summary versus `DataWorkspaceEvent` create/update inputs.
- affected_ui_files: `frontend/src/features/data-workspace/ui/DataWorkspaceOperations.tsx`
- contract_or_fixture_gap: `YES`; typed editor projection is absent.
- blocks_current_stage: `NO`
- blocks_codex_integration: `NO`, resolved by Codex Stage 4.5.
- safe_continuation: display formal Action summaries and keep editor controls disabled with a
  reason; do not send empty actions or invent parameter fields.
- resolution: Codex Stage 4.5 added a strict frontend discriminated union matching the five M4
  backend executable Action schemas, fail-closed DTO mapping, runtime mutation guards, API wire
  conversion and a bounded CleaningPlan editor using deterministic `ALL_ROWS` input.
- verification: focused tests map all five executable variants, reject unavailable Actions, verify
  create/update guards, and confirm the editor emits an intent without changing fixture state.

### M4-OD-0008: Plan fixtures inherit capabilities inconsistent with their formal Plan state

- stage: `M4 Open Design Stage 2`
- severity: `HIGH`
- status: `RESOLVED_BY_CODEX_STAGE_4_5`
- area: `fixture / capability projection`
- page/surface: `Cleaning actions`
- fixture: `plan-draft, plan-needs-input, plan-ready, approval-pending, approval-rejected, approval-stale`
- viewport: `all`
- theme: `Light and Dark`
- observed_behavior: fixture Plan `allowedActions` changes by state, but the workspace-level
  capabilities remain inherited from the completed ready fixture, producing contradictory disabled
  reasons for preview, request approval and execute.
- expected_behavior: each representative fixture should project workspace capabilities consistent
  with its formal Plan and Approval facts.
- evidence: the fixture helper overrides `plan` or `approval` without updating matching capabilities.
- affected_ui_files: `frontend/src/features/data-workspace/ui/DataWorkspaceOperations.tsx`
- contract_or_fixture_gap: `YES`; protected fixture inconsistency.
- blocks_current_stage: `NO`
- blocks_codex_integration: `NO`, resolved by Codex Stage 4.5.
- safe_continuation: require both workspace capability and Plan allowedActions; show the formal
  disabled reason and never bypass either source.
- resolution: Codex Stage 4.5 aligned Plan `allowedActions`, workspace capabilities, Approval,
  Transformation and Job facts for draft, needs-input, ready, pending, rejected and stale fixtures.
- verification: focused contract assertions and the complete browser matrix pass; no DRAFT or
  NEEDS_INPUT fixture inherits a completed Transformation/Job.

### M4-OD-0009: No typed duplicate Issue fixture exists for Stage 2 visual coverage

- stage: `M4 Open Design Stage 2`
- severity: `MEDIUM`
- status: `OPEN`
- area: `fixture / Quality semantics`
- page/surface: `Quality Issue table and Inspector`
- fixture: `quality completed`
- viewport: `1440x900, 390x844`
- theme: `Light and Dark`
- observed_behavior: ready data covers missing value, extreme-value clue and sensitive candidate,
  but no duplicate Issue is present.
- expected_behavior: a typed duplicate fixture should verify deterministic duplicate wording,
  affected rows and allowed actions without synthetic UI data.
- evidence: frozen `readyData.issues` contains three non-duplicate Issue types.
- affected_ui_files: `frontend/src/features/data-workspace/ui/DataWorkspaceOperations.tsx`
- contract_or_fixture_gap: `YES`; representative fixture is absent.
- blocks_current_stage: `NO`
- blocks_codex_integration: `NO`
- safe_continuation: support arbitrary formal issueType/ruleCode values in the shared table and do
  not invent a duplicate row.
- resolution: pending optional authorized fixture addition.
- verification: generic deterministic-fact presentation is implemented; duplicate pixels pending.

### M4-OD-0010: compare-versions Event has no formal capability projection

- stage: `M4 Open Design Stage 2`
- severity: `MEDIUM`
- status: `RESOLVED_BY_CODEX_STAGE_4_5`
- area: `contract / Versions interaction`
- page/surface: `Versions and Comparison`
- fixture: `ready and comparison absent states`
- viewport: `all`
- theme: `Light and Dark`
- observed_behavior: the frozen Event union includes `compare-versions`, but
  `DataWorkspaceCapabilities` has no corresponding allowed/disabled projection.
- expected_behavior: a formal capability should determine whether comparison navigation may be
  emitted and provide a disabled reason.
- evidence: `ui/contracts.ts` Event union and `model.ts` capabilities type.
- affected_ui_files: `frontend/src/features/data-workspace/ui/DataWorkspaceOperations.tsx`
- contract_or_fixture_gap: `YES`; capability is absent.
- blocks_current_stage: `NO`
- blocks_codex_integration: `NO`, resolved by Codex Stage 4.5.
- safe_continuation: render comparison facts already present in Props but expose no compare action;
  do not infer permission from Event existence.
- resolution: Codex Stage 4.5 added `compareVersions` capability and exposes one safe compare intent
  only when the selected known Version has a formal `parentVersionId`.
- verification: mapper/mutation focused coverage and Playwright confirm the parent comparison intent
  is enabled and emitted without creating local lineage.

## Stage 2 Acceptance

Implemented pure UI files:

- `frontend/src/features/data-workspace/ui/DataWorkspace.tsx`
- `frontend/src/features/data-workspace/ui/DataWorkspaceOperations.tsx`
- `frontend/src/features/data-workspace/ui/data-workspace-operations.css`

Implemented surfaces and interactions: Quality Run summary, local multi-filter Issue table,
deterministic fact versus clue/sensitive semantics, contextual Issue Inspector, acknowledge
confirmation, ignore-reason Dialog, CleaningPlan summary, deterministic Preview facts, Approval
status, Job flags/progress/retry, Transformation result, compact formal process track, current
version lineage and formal Comparison facts. No approve/reject/cancel/AI/editor/compare action was
invented, and local selection/filtering does not change formal state.

Gate coverage: affected Biome format/lint, TypeScript no-emit, `check:m4-fixtures` (6/6),
`check:ui-boundaries` (4/4), `check:production-mocks` (6/6) and frontend build pass. The requested
quality completed, approval stale, transform running/failed and long-content 1440/390 screenshots
remain pending under M4-OD-0006; no full fixture matrix or Stage 3 acceptance was executed.

```text
OPEN_DESIGN_STAGE_RESULT=PASS_WITH_GAPS
NEXT_STAGE_EXECUTED=NO
```

### M4-OD-0011: Controlled Dialog and Sheet surfaces did not restore focus or fully honor reduced motion

- stage: `M4 Open Design Stage 3`
- severity: `HIGH`
- status: `RESOLVED`
- area: `accessibility / portal interaction`
- page/surface: `Issue Dialogs, upload/worksheet Dialogs, Dataset/Inspector Sheets`
- fixture: `ready, quality completed`
- viewport: `1440x900, 390x844`
- theme: `Light and Dark`
- observed_behavior: externally controlled Issue Dialogs closed to an inactive focus target, and
  Portal-mounted Sheet/Dialog animation classes were outside the original reduced-motion selector.
- expected_behavior: initial focus, trap, Escape and focus restore remain deterministic, while
  reduced-motion disables Portal motion.
- contract_or_fixture_gap: `NO`.
- blocks_current_stage: `NO`, resolved in place.
- blocks_codex_integration: `NO`.
- resolution: record the active trigger before opening controlled surfaces, restore it after close,
  and include `.m4-dialog` and `.m4-sheet-content` in the reduced-motion scope.
- verification: dedicated Dialog and mobile Sheet Playwright assertions pass.

### M4-OD-0012: Mobile navigation hid Quality, Cleaning and Versions

- stage: `M4 Open Design Stage 3`
- severity: `HIGH`
- status: `RESOLVED`
- area: `responsive navigation`
- page/surface: `Data Workspace mobile view switcher`
- fixture: `all ready-state operation fixtures`
- viewport: `390x844`
- theme: `Light and Dark`
- observed_behavior: the five formal Workspace tabs were hidden below 700px while the replacement
  switcher exposed only Dataset, Data, Columns and Inspector.
- expected_behavior: Quality, Cleaning and Versions remain directly reachable on mobile without a
  compressed desktop three-pane layout.
- contract_or_fixture_gap: `NO`.
- blocks_current_stage: `NO`, resolved in place.
- blocks_codex_integration: `NO`.
- resolution: retain the horizontally scrollable formal view tabs on mobile and reduce the
  secondary surface switcher to Dataset and Inspector.
- verification: the full mobile fixture matrix and Quality/Cleaning screenshots pass.

### M4-OD-0013: Data Workspace ignored the explicit Preview theme

- stage: `M4 Open Design Stage 3`
- severity: `HIGH`
- status: `RESOLVED`
- area: `theme projection`
- page/surface: `Data Workspace and stable loading/empty/error shells`
- fixture: `all`
- viewport: `1440x900, 1024x768, 390x844`
- theme: `Light and Dark`
- observed_behavior: `VisualThemeProvider` changed Context but Data Workspace did not apply
  `data-theme`, so Light and Dark screenshots were byte-identical and inherited Preview dark mode.
- expected_behavior: every Loadable state binds the explicit Light/Dark choice to the shared RECA
  tokens.
- contract_or_fixture_gap: `NO`.
- blocks_current_stage: `NO`, resolved in place.
- blocks_codex_integration: `NO`.
- resolution: consume `useVisualTheme()` in ready and stable-state roots and assert `data-theme` for
  every fixture/theme matrix entry.
- verification: all theme assertions pass and representative Light/Dark SHA-256 values differ.

### M4-OD-0014: Full repository format and lint remain blocked by protected integration files

- stage: `M4 Open Design Stage 3`
- severity: `HIGH`
- status: `RESOLVED_BY_CODEX_STAGE_4_5`
- area: `frontend gate / protected files`
- page/surface: `repository-wide frontend checks`
- fixture: `not applicable`
- viewport: `not applicable`
- theme: `not applicable`
- observed_behavior: both `format:check` and `lint` fail only because Biome would reformat
  `frontend/openapi.json` and `frontend/src/api/adapter/index.ts`.
- expected_behavior: the full frontend format and lint gates pass without Open Design modifying
  generated or adapter integration ownership.
- evidence: Stage 3 full command output; the five authorized UI/test files pass targeted Biome.
- contract_or_fixture_gap: `YES`; protected integration baseline/generation formatting.
- blocks_current_stage: `YES` for an unconditional PASS.
- blocks_codex_integration: `NO`, resolved by Codex Stage 4.5.
- safe_continuation: preserve both files exactly; do not format, regenerate or partially revert them
  from Open Design.
- resolution: Codex Stage 4.5 formatted the protected OpenAPI snapshot and adapter through Biome
  without hand-editing generated client files.
- verification: repository-wide frontend `format:check` and `lint` pass, followed by generated-client
  consistency and production build.

### M4-OD-0015: Open Design root mirror cannot rebuild from the Chinese-path M4 worktree

- stage: `M4 Open Design Stage 3`
- severity: `MEDIUM`
- status: `OPEN`
- area: `Preview artifact generation`
- page/surface: `reca-live-design-preview.html`
- fixture: `all`
- viewport: `not applicable`
- theme: `not applicable`
- observed_behavior: Bun 1.2.22 corrupts the Chinese `RECA_FRONTEND_DIR` value while importing
  Vite, and a temporary ASCII drive mapping is not resolved by the module loader.
- expected_behavior: the existing mirror builder should inline the M4 worktree Preview into the
  Open Design root HTML.
- evidence: bounded Stage 3 generator attempts failed before Vite execution; the existing root file
  was not modified and is excluded from Stage 3 acceptance evidence.
- contract_or_fixture_gap: `NO`; local Preview toolchain/path limitation.
- blocks_current_stage: `NO`; real M4 Vite Preview and Playwright evidence are available.
- blocks_codex_integration: `NO`.
- safe_continuation: use the M4 source files and Stage 3 screenshots; rebuild the root mirror from an
  ASCII checkout/path or a module loader that preserves the path.
- resolution: pending Open Design Preview tooling repair.
- verification: current root HTML still passes the single-file structural rule but does not contain
  the Stage 3 rebuild.

## Stage 3 Acceptance

At the original Stage 3 stop, Open Design completed the full 30-fixture matrix at 1440x900,
1024x768 and 390x844 in Light and Dark. The dedicated Playwright suite passed 15/15 after closing
the Stage 3 UI HIGH issues above. M4 fixture, UI boundary, production mock, generated-client and
production build gates pass. Repository-wide format/lint remain nonzero under M4-OD-0014, and the
protected fixture/contract HIGH issues M4-OD-0005, M4-OD-0007 and M4-OD-0008 were still open. The
Codex Stage 4.5 section below supersedes that readiness decision.

```text
READY_FOR_CODEX_INTEGRATION=YES
OPEN_DESIGN_STAGE_RESULT=PASS_WITH_GAPS
CODEX_STAGE_4_5_RESULT=PASS
REVALIDATION_OWNER=CODEX
NEXT_STAGE_EXECUTED=NO
```

## Codex Stage 4.5 Integration Readiness Repair

Codex synchronized the four accepted production UI/CSS files plus the M4 Stage 3 Playwright suite
by exact file hash, then resolved the protected contract, fixture and formatting issues without a
second Open Design review. `M4-OD-0004`, `0005`, `0007`, `0008`, `0010` and `0014` are closed.
`M4-OD-0009` remains a non-blocking optional duplicate-Issue pixel fixture; `M4-OD-0015` remains a
non-blocking single-file mirror tooling limitation. Neither is used as production integration
evidence.

Codex verification in the formal repository:

- M4 fixture guard: `8/8`;
- UI boundary guard: `4/4`;
- production mock guard: `6/6`;
- focused contract plus full M4 browser suite: `22/22`;
- all 30 fixtures at 1440x900, 1024x768 and 390x844 in Light/Dark: PASS;
- frontend format, lint, generated-client consistency and production build: PASS.

```text
READY_FOR_CODEX_INTEGRATION=YES
CODEX_STAGE_4_5_RESULT=PASS
CODEX_STAGE_5_ENTRY=ALLOWED
NEXT_STAGE_EXECUTED=NO
```
