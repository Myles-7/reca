# M6 Open Design Handoff

Date: 2026-08-05
Owner: Codex
Stage: M6 Codex Stage 3.5
Production route: `/projects/$projectId/manuscript` (registered)

## 1. Readiness

`READY_FOR_OPEN_DESIGN=YES`

`READY_FOR_CODEX_INTEGRATION=YES` (Codex completed controlled integration from the
frozen contract)

The OpenAPI, generated client, adapter, ViewModel, events, typed fixtures and ownership
guards are executable. Project discovery now restores no-manuscript, current Manuscript,
inactive history and refresh state through an authorized project endpoint without inferring
existence from Artifact, Literature or another resource.

Open Design may implement the pure visual Workspace only in the allowed paths below. READY
does not mean the production Route is registered, browser integration is complete, or M6
has passed its Exit Gate.

## 2. Suggested Information Architecture

The pure UI should accept the injected Workspace ViewModel and may organize it into:

- Manuscript identity and immutable version history;
- check progress and degradation;
- located Issues with deterministic/AI/project-evidence distinctions;
- low-risk Fix preview, Approval and derived output version;
- before/after Revision Audit findings and limitations;
- source-located Claim state, evidence risk and confirmation Approval.

This is an information hierarchy, not a visual prescription. Do not merge Manuscript and
Version, Approval and execution, Job acceptance and completion, or Issue acceptance and
actual resolution into a single optimistic state.

## 3. Props And Events

UI entry contract: `ManuscriptWorkspaceProps` in
`frontend/src/features/manuscript-workspace/ui/contracts.ts`.

Props:

- `content`: loading, empty, error or ready `ManuscriptWorkspaceViewModel`;
- `pendingAction`: local request-in-flight indicator only;
- `mutationError`: normalized server error;
- `onRetry`, `onEvent`, optional initial view and view-change callback.

Frozen intent events:

```text
upload-manuscript
select-version
start-check
retry-job
cancel-job
accept-issue
reject-issue
create-fix-plan
preview-fix-plan
request-fix-approval
execute-fix-plan
start-revision-audit
create-claim
update-claim
request-claim-confirmation
download-version
refresh
```

Events never mean success. The Container revalidates permission knowledge, known status,
allowed action, retryability, lock version, Idempotency-Key, version/artifact/plan/Approval
hash, Claim locator and same-project relationships before transport. Server response plus
query invalidation/refetch is the only mutation authority.

Event input sources are frozen as follows:

| Event | UI input source |
| --- | --- |
| `upload-manuscript` | user-selected `File`; Container owns Artifact initiate/transfer/complete and passes the returned Artifact ID internally |
| `start-check` | `checkDefinitions` projected by the ViewModel; only enabled definitions may be submitted |
| `start-revision-audit` | two distinct enabled `revisionReferences`; result snapshots are resolved by the service/Worker |
| `create-claim` | enabled `claimTypeDefinitions`, authorized source object and locator already present in the Workspace facts |
| `update-claim` | editable text/scope plus an optional enabled `claimStatusTransitions` value; arbitrary status input is impossible |

All projected options are same-project facts with known permission/status and a disabled
reason. Open Design must not add free-form UUID or enum entry fields.

## 4. ViewModel Facts

The UI receives separate facts for:

- Manuscript, selected Version and version history;
- CheckRun, Job, degradation and low confidence;
- Issue locator, severity, provenance, risk, auto-fix eligibility and evidence read scope;
- Transformation preview/hash, Approval status/staleness, execution Job and output Version;
- Revision Audit before/after source hashes, findings, limitations and result hash;
- Claim source locator/hash, text hash, confidence, Approval and read-only state;
- `permissionsKnown`, raw `status`, `knownStatus`, `allowedActions`, capabilities and disabled reasons.
- project discovery state/knowledge, allowed check definitions, revision references, Claim
  type definitions and allowed Claim transitions.

Unknown enum values retain the raw server value. Mappers set `knownStatus=false`, remove
formal actions and keep the UI renderable. Unsupported evidence, degradation and unknown
facts must not be relabeled as pass, completed or confirmed.

## 5. Fail-Closed Matrix

| Condition | Display | Formal actions |
| --- | --- | --- |
| permissions known and action allowed | normal authorized fact | only the named action |
| `permissionsKnown=false` | permissions unavailable | all formal actions disabled |
| unknown resource status | raw status plus unknown treatment | disabled |
| unknown Approval status | raw status, not approved | approval-dependent actions disabled |
| stale/expired/superseded Approval | stale decision | execute/confirm disabled |
| Artifact/version/plan/source hash mismatch | conflict/stale state | mutation disabled; refresh available |
| cross-project or inaccessible ID | authorized default/no-disclosure error | disabled; existence not disclosed |
| low confidence/degraded | explicit limitation | no optimistic completion; high-risk action disabled |
| evidence denied/missing/stale | scoped evidence state | no fabricated excerpt or support |
| terminal Claim | read-only fact | update/confirm disabled |

## 6. Typed Fixtures

Catalog: `frontend/src/features/manuscript-workspace/fixtures/index.ts`.

The catalog contains **87** descriptors. Every descriptor supplies `content`,
`pendingAction`, `mutationError`, `initialView`, viewport and theme. It covers
upload/no-manuscript, version lineage and unknown status, every CheckRun phase,
mixed Issues, evidence scopes, permission/error/degradation states, Fix preview/Approval/
execution, Revision Audit, Claim lifecycle, loading/empty/conflict, long content, desktop/
tablet/mobile and light/dark variants. Fixtures are typed against the frozen ViewModel and
may not import generated, adapter, query, mutation or Container modules.

Fixtures, preview logs, integration-pending flags and design notes must never be imported
by production routes, queries, mutations or adapter code. The production-mock guard enforces
this boundary.

Route-view fixture mapping:

| View | Primary fixture families |
| --- | --- |
| `manuscript` | loading/empty/error, no-manuscript, upload, original/multiple/inactive/unknown versions, responsive/theme/long content |
| `checks` | queued, parsing, rules, project consistency, needs review, completed, failed, low confidence, cancelled, pending |
| `issues` | citation/numeric/causal/terminology/format, resolved/rejected/invalidated, evidence scopes, accept/reject pending |
| `fixes` | preview, Approval pending/approved/stale/rejected, execution pending/failed/success, action pending |
| `audits` | running, completed mixed, insufficient, failed and request pending |
| `claims` | draft/evidence states, Approval pending, confirmed/read-only/permissions unknown and mutation pending |

## 7. Responsive And Accessibility Requirements

- Desktop, tablet and mobile must preserve the distinction between navigation, status,
  evidence and formal actions without overlap or off-screen controls.
- Light and dark themes require equivalent semantic contrast; status cannot rely on color.
- All controls require keyboard access, visible focus and stable focus after refetch.
- Reduced-motion must remove nonessential movement; progress updates remain understandable.
- Dialogs and destructive/reject decisions require focus containment and return.
- Loading, error, empty, forbidden, unknown and degraded states require programmatic labels.

## 8. Long And Sensitive Content

DOI, 64-character hashes, filenames and unbroken identifiers must wrap or use controlled
ellipsis with a full accessible value. Manuscript excerpts, citations, numbers and long
Chinese/English text must not overlap adjacent actions or status labels.

Sensitive excerpts are rendered only when the ViewModel provides them with an available
read scope. Denied/missing/stale evidence uses a non-disclosing state and never reconstructs
text from identifiers, logs or client caches. Do not put excerpts, Claim text, hashes,
Approval payloads or source locations into analytics, screenshots or Event logs by default.

## 9. Ownership

Codex-protected paths:

```text
backend/app/api/m6_responses.py
backend/app/api/routes/manuscripts.py
frontend/openapi.json
frontend/src/api/generated/**
frontend/src/api/adapter/**
frontend/src/features/manuscript-workspace/model.ts
frontend/src/features/manuscript-workspace/mappers.ts
frontend/src/features/manuscript-workspace/queries.ts
frontend/src/features/manuscript-workspace/mutations.ts
frontend/src/features/manuscript-workspace/route-contract.ts
frontend/src/features/manuscript-workspace/containers/**
frontend/src/features/manuscript-workspace/fixtures/**
frontend/src/features/manuscript-workspace/ui/contracts.ts
frontend/scripts/check-m6-contracts.test.mjs
```

Open Design allowed paths after readiness becomes YES:

```text
frontend/src/features/manuscript-workspace/ui/** except ui/contracts.ts
frontend/src/design-preview/** only for an explicit M6 preview entry
frontend/src/components/ui/** only for display-level additions that do not import M6 model,
adapter, queries, mutations, fixtures or Container
frontend/src/styles/** only for shared presentation tokens with no business-state selectors
```

Open Design must not register the production route, change Props/Event/ViewModel, read the
generated client, add queries/mutations, construct permissions/status, or import fixtures
into production code.

## 10. Preview And Delivery

The future preview must use only the typed fixture catalog and a design-only entry. Delivery
must include changed allowed paths, fixture IDs reviewed, desktop/tablet/mobile and light/
dark screenshots, keyboard/focus/reduced-motion notes, and unresolved display questions.

`READY_FOR_CODEX_INTEGRATION=YES`; contract-first production integration is complete.

## 11. Known Limitations And Pending Integration

- `M6-ISSUE-0005` is resolved by project-scoped discovery and refresh recovery.
- `M6-ISSUE-0002`: broader OOXML round-trip golden coverage remains an Exit Gate issue.
- `M6-ISSUE-0003`: hard parser deadline/memory isolation remains an Exit Gate issue.
- `M6-ISSUE-0004`: complete scientific matcher matrix remains an Exit Gate issue.
- `M6-ISSUE-0006`: Compose PostgreSQL is healthy but internal-only and the production API
  image omits test dependencies; database discovery tests are implemented but await the
  accepted integration runner. This does not block display-contract readiness.
- Production route registration, real API browser E2E and Workspace visual implementation
  are intentionally pending Stage 4.
- No production list of AnalysisResult/Figure selector records is exposed in this stage;
  revision audit uses before/after versions and server-resolved snapshots.
- Open Design delivery still requires Codex review before any production integration.
