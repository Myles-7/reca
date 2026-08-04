# M4 Open Design Acceptance Report

Assessment date: 2026-08-04 (Asia/Shanghai)

```text
MILESTONE=M4_DATA_QUALITY_AND_VERSIONING
OPEN_DESIGN_STAGE=3
READY_FOR_CODEX_INTEGRATION=YES
OPEN_DESIGN_STAGE_RESULT=PASS_WITH_GAPS
CODEX_STAGE_4_5_RESULT=PASS
REVALIDATION_OWNER=CODEX
NEXT_STAGE_EXECUTED=NO
```

## Scope And Ownership

Stage 3 stopped feature expansion and accepted only the pure UI surface driven by frozen typed
Props, Events and fixtures. No production Route, Container, API, query, mutation, cache, generated
client, adapter, backend, migration or Worker behavior was added.

Workspace and pure UI files:

- `frontend/src/features/data-workspace/ui/DataWorkspace.tsx`
- `frontend/src/features/data-workspace/ui/DataWorkspaceOperations.tsx`
- `frontend/src/features/data-workspace/ui/data-workspace.css`
- `frontend/src/features/data-workspace/ui/data-workspace-operations.css`
- `frontend/tests/projects-m4-open-design-stage3.spec.ts`

No shared display component was added or modified. Data Workspace now consumes the existing
`VisualThemeProvider` through `useVisualTheme`; the shared theme implementation itself is unchanged.

## Frozen Props And Events

`DataWorkspaceWorkspaceProps` remains:

- `content: Loadable<DataWorkspaceViewModel>`
- `pendingAction`
- `mutationError`
- `onRetry`
- `onEvent`

Frozen intents consumed by the UI remain:

- `upload-dataset`, `select-worksheet`, `update-dataset-identity`, `update-column`
- `select-version`, `compare-versions`
- `run-quality`, `acknowledge-issue`, `ignore-issue`
- `create-plan`, `update-plan`, `preview-plan`, `request-approval`, `execute-plan`
- `retry-job`

The UI does not emit `create-plan`, `update-plan` or `compare-versions` without missing formal
projections. It introduces no approve/reject, Job cancel, AI suggestion, arbitrary expression or M5
analysis/chart action.

## Fixture Coverage Matrix

All 30 frozen fixtures passed at every required viewport/theme combination:

| Viewport | Light | Dark | Root overflow | Console/page errors |
| --- | --- | --- | --- | --- |
| 1440x900 | PASS | PASS | 0 | 0 |
| 1024x768 | PASS | PASS | 0 | 0 |
| 390x844 | PASS | PASS | 0 | 0 |

Fixtures: `ready`, `loading`, `empty`, `error`, `forbidden`, `read-only`,
`permissions-unknown`, `upload-pending`, `upload-failure`, `xlsx-worksheets`, `invalidated`,
`quality-queued`, `quality-running`, `quality-failed`, `quality-unknown`, `plan-draft`,
`plan-needs-input`, `plan-ready`, `approval-pending`, `approval-rejected`, `approval-stale`,
`conflict`, `transform-queued`, `transform-running`, `transform-failed`, `future-enums`,
`long-content`, `desktop-light`, `tablet-dark`, `mobile-light`.

The long-content field table owns its horizontal overflow; the page, Preview product surface and
Workspace root remain at zero horizontal overflow. Loading, empty, error and forbidden keep stable
Workspace geometry. Light/Dark is asserted through the root `data-theme`; representative image
hashes differ.

## Responsive And Theme Conclusions

- Desktop: stable 248px Dataset rail, dominant center workspace and 336px Inspector.
- Tablet: Dataset and Inspector use Sheets; the center surface remains dominant.
- Mobile: formal Data/Columns/Quality/Cleaning/Versions tabs remain reachable; Dataset and Inspector
  are secondary Sheet surfaces. No desktop three-column compression is used.
- Light/Dark: all Loadable states use the explicit RECA visual theme and shared semantic tokens.
- Long identifiers, hashes, filenames, columns, values and action reasons wrap or scroll internally.

## Interaction And Accessibility

Playwright verifies:

- local Issue filters and selection emit no formal Event;
- ignore reason is required and intent submission does not mutate the fixture Issue status;
- upload file/name drafts do not mutate Dataset facts or expose file content in Event Log;
- controlled Dialogs trap focus, support Escape and restore their real trigger;
- mobile Inspector Sheet contains focus, restores focus and disables Portal motion under
  `prefers-reduced-motion: reduce`;
- permissions unknown fails closed with visible and accessible disabled reasons;
- pending upload prevents duplicate submission; retry emits one intent and leaves Job FAILED;
- status is always icon plus text/label rather than color-only;
- Event Log contains no complete rows, sensitive values, file content or full action parameters.

At the original Open Design Stage 3 stop, the protected XLSX fixture still disabled worksheet
selection and Plan/Approval fixtures remained inconsistent. Codex Stage 4.5 subsequently corrected
both protected fixture projections and verified the hidden worksheet, request-approval and execute
guards in the formal repository.

## Local UI State

Allowed local state is limited to view/mobile surface, Dataset/column/cell/Issue selection, local
Issue filters, upload and edit drafts, Dialog/Sheet open state, focus restoration targets, hidden
worksheet acknowledgement and ignore reason. None is persisted as permission, Approval, Job,
Transformation, Version lineage or server success.

## Data Semantics

Acceptance confirms the UI keeps these distinctions visible:

- upload intent versus Dataset Version `AVAILABLE`;
- Dataset versus Version and inferred versus confirmed type;
- sensitive candidate versus confirmed sensitive and clue versus deterministic detection fact;
- Preview versus Approval and request approval versus approved;
- Job accepted/queued/running versus completed;
- Transformation completed versus target Version `AVAILABLE`;
- invalidated versus deleted and local selection versus server lineage;
- completed fixture presentation versus production success.

Masked values remain masked. No local unmask, synthetic version history, Transformation detail,
Cleaning Action parameter editor or project-level Approval decision surface was introduced.

## M4-ISSUE-0014 And M4-ISSUE-0015

- `M4-ISSUE-0014`: UI consumes only mapped ViewModel facts and fails closed on unknown statuses or
  permissions. Open Design does not import or harden generated/adapter response DTOs.
- `M4-ISSUE-0015`: Versions shows only current/original/invalidated and available comparison facts;
  Transformation shows only the current projection. No fixture-derived history or detail is
  presented as formal lineage. `integration pending` remains Preview chrome only.

## Screenshot Index

Directory: `D:\OPenDesign\2ab278d1-4474-4a10-b954-777fc8bc8b77\output\playwright\qa\m4-stage3`

For each state below, `1440x900` and `390x844` screenshots exist in both `light` and `dark`:

- `quality-completed-{viewport}-{theme}.png`
- `approval-stale-{viewport}-{theme}.png`
- `transform-running-{viewport}-{theme}.png`
- `transform-failed-{viewport}-{theme}.png`
- `long-content-{viewport}-{theme}.png`

Total: 20 PNG files. Dimensions were verified against their filenames.

## Command Results

| Command | Result |
| --- | --- |
| `bun run --cwd frontend format:check` | FAIL: protected `openapi.json` and `api/adapter/index.ts` require Biome formatting |
| `bun run --cwd frontend lint` | FAIL: same two protected formatting findings |
| targeted Biome on five authorized UI/test files | PASS |
| `bun run --cwd frontend check:m4-fixtures` | PASS, 6/6 |
| `bun run --cwd frontend check:ui-boundaries` | PASS, 4/4 and clean scan |
| `bun run --cwd frontend check:production-mocks` | PASS, 6/6 and clean scan |
| `bun run --cwd frontend check-generated-client` | PASS, 4 generated files |
| `bun run --cwd frontend build` | PASS |
| M4 Open Design Playwright Stage 3 suite | PASS, 15/15 |
| `git diff --check` on authorized Stage 3 files | PASS |
| Open Design root mirror rebuild | FAIL: Bun path encoding/module resolution; existing root unchanged |

Playwright used an isolated port and `NODE_ENV=development` because the inherited shell environment
sets `NODE_ENV=production` and port 5173 may host another RECA worktree.

## Remaining Non-Blocking Open Design Gaps

- `M4-OD-0009`: no dedicated duplicate-Issue pixel fixture; generic deterministic Issue rendering
  and backend duplicate coverage remain available.
- `M4-OD-0015`: the single-file Open Design root mirror could not be rebuilt from the Chinese-path
  worktree; it is not integration evidence.

Codex Stage 4.5 resolved `M4-OD-0004/0005/0007/0008/0010/0014` and reran the complete UI matrix.

## Codex Production Integration Responsibility

Codex Stage 5/6 remains responsible for:

- production Route/search validation, Container injection and deep-link restoration;
- generated/adapter contract hardening and resolution of the full format/lint gate;
- formal version-history and Transformation read facts;
- API query/mutation/cache invalidation;
- Job refresh/SSE/retry behavior;
- Approval record loading and the project-level decision entry;
- permissions, allowed actions, If-Match and Idempotency-Key enforcement;
- production Route/Container use of the corrected fixture and capability contracts;
- backend/browser vertical E2E and clean-room acceptance.

Codex Stage 5 was not executed. No Commit, Tag or Push was created.

## Codex Stage 4.5 Addendum

Codex performed the integration-readiness repair directly in the formal repository; no second Open
Design review was requested. The accepted pure UI files and Stage 3 browser suite were synchronized
by exact SHA-256 match before Codex-owned contract changes.

Resolved integration blockers:

- empty-project upload now uses a ready zero-dataset ViewModel with a formal capability;
- XLSX `CREATING` fixture allows worksheet selection and verifies hidden-sheet acknowledgement;
- CleaningPlan create/update use a strict five-variant typed Action projection matching the backend
  whitelist, with fail-closed mapping and runtime guards;
- Plan/Approval fixtures no longer inherit contradictory completed capabilities or Job facts;
- version comparison requires a formal parent Version and an explicit capability;
- protected OpenAPI/adapter formatting drift is reconciled.

Codex reran the complete M4 fixture/theme/viewport suite plus focused contract coverage. Results:

```text
M4_FIXTURE_GUARD=PASS_8_OF_8
UI_BOUNDARY_GUARD=PASS_4_OF_4
PRODUCTION_MOCK_GUARD=PASS_6_OF_6
M4_CODEX_BROWSER_AND_CONTRACT=PASS_22_OF_22
FRONTEND_FORMAT=PASS
FRONTEND_LINT=PASS
GENERATED_CLIENT_CHECK=PASS
PRODUCTION_BUILD=PASS
READY_FOR_CODEX_INTEGRATION=YES
CODEX_STAGE_5_ENTRY=ALLOWED
NEXT_STAGE_EXECUTED=NO
```

`M4-OD-0009` and `M4-OD-0015` remain non-blocking. The former is optional duplicate-Issue pixel
coverage; the latter affects only the separate single-file Open Design root mirror, not the Vite,
Playwright or production integration path.
