# RECA M3 Open Design Handoff

## Status

```text
Stage: M3-8
Date: 2026-08-03 (Asia/Shanghai)
Branch: feat/m2-research-literature
HEAD at entry: 0e3c39dde65feaa8f784fd5fcfb1055cb557bb3c
Migration head: 0013_m3_evidence_matrix
READY_FOR_OPEN_DESIGN=NO
PRODUCTION_INTEGRATION_COMPLETE=YES_WITH_ISSUES
OPEN_DESIGN_OUTPUT_INTEGRATED=YES
VISUAL_ACCEPTANCE=PASS
```

This handoff freezes the M3 frontend business and UI contract, records the completed Stage 6
production wiring, and records the Stage 8 Open Design integration. It does not claim backend/M3 Exit
Gate completion.

## Single Workspace And Route Draft

The only product shell remains `/projects/$projectId/literature`. M3 uses the frozen draft in
`frontend/src/features/literature/m3-route-contract.ts`:

```text
view=matrix|analysis|topics (unknown/missing -> matrix)
documentId
extractionId
fieldId
evidenceSpanId
summaryId
topicRunId
```

Open Design must not create a second product shell or change route semantics. Codex will integrate
this parser into `frontend/src/routes/_layout/projects.$projectId_.literature.tsx` after the pure UI
handoff; the current M2 `searchRunId` behavior remains untouched in Stage 5.

## Workspace Contracts

| Workspace | Props/Event authority | Preview component | Fixtures |
| --- | --- | --- | --- |
| Evidence Matrix + PDF evidence viewer | `frontend/src/features/evidence-matrix/ui/contracts.ts` | `ui/EvidenceMatrixWorkspace.tsx` | `fixtures/index.ts` |
| Current Evidence Analysis | `frontend/src/features/evidence-analysis/ui/contracts.ts` | `ui/EvidenceAnalysisWorkspace.tsx` | `fixtures/index.ts` |
| Topic Candidates | `frontend/src/features/topic-candidates/ui/contracts.ts` | `ui/TopicCandidatesWorkspace.tsx` | `fixtures/index.ts` |

The preview components are intentionally minimal contract surfaces, not approved visual pages.
They are registered in `frontend/src/design-preview/DesignPreviewWorkbench.tsx`; every callback is
logged as an intent and does not call production APIs.

## Frozen Props And Events

- Matrix Props: loadable matrix, optional PDF viewer projection, pending action, normalized mutation
  error, retry callback, intent callback.
- Matrix Events: filter/sort, open PDF location, create extraction/evidence, correct/confirm field,
  verify/reject evidence, create LiteratureDecision.
- Analysis Props: loadable summary, optional bounded search result, pending action/error, retry and
  intent callbacks.
- Analysis Events: evidence search, create current-set summary, generate topics, retry Job.
- Topic Props: loadable exactly-three projection, pending action/error, retry and intent callbacks.
- Topic Events: request exactly-three generation and open a bound LiteratureRecord/EvidenceSpan.

Events express user intent only. Containers re-check `knownStatus`, `permissionsKnown`, exact server
`allowed_actions`, object identity, count and source validity before mutation. Unknown facts disable
the action. Button clicks, local state and accepted Jobs never mean business success.

## Fixture Matrix

All three features include ready, loading, empty, error, forbidden, read-only, permissions unknown,
pending, conflict, degraded, unknown and long-content fixtures.

- Matrix additionally covers ten fixed fields, low confidence, `NO_LOCATED_EVIDENCE`,
  `LOCATION_UNCERTAIN`, verified evidence, INCLUDED/EXCLUDED/UNCERTAIN decisions, PDF.js coordinates,
  no coordinates and pypdf degradation.
- Analysis covers counterexamples, current-literature-set evidence insufficiency, cautious language,
  empty candidates and unverified candidate boundaries.
- Topic covers exactly three sourced candidates, pending without optimistic candidates, count
  failure, invalid-source failure and unavailable formal `limitations` projection.

## Responsive States For Open Design

- Desktop: dense matrix/table scanning with a document location inspector; analysis and topics remain
  within the same workspace tabs.
- Tablet: keep the primary table/list and move the PDF/inspector to a controlled secondary pane.
- Mobile: one primary surface at a time; filters and inspectors use existing sheet/dialog primitives.
- Long titles, source text, limitations and research questions must wrap without changing control
  dimensions or overlapping adjacent content.
- Loading, error, conflict and degraded states must preserve stable workspace dimensions.

## Disabled Reasons

UI must render the reason already present in the ViewModel or normalized error. Required categories:
unknown permission, unknown status, read-only role, stale `If-Match`, server capability absent,
unverified/coordinate-less evidence, invalid source, non-exact candidate count, and pending Job.
Open Design must not infer permissions from role labels or hide unknown states as ordinary empty data.

## PDF.js Input Boundary

Allowed UI input: backend-authorized PDF URL, document/page identity, source text/hash, server page
number, optional normalized bounding boxes, parser type/coverage, location/review/read-scope status and
server actions. PDF.js may render, select text and request a jump. It does not compute authoritative
hashes, create EvidenceSpan, upgrade verification, infer full-text reading, or execute PDF content.
pypdf without trusted coordinates must show text-only degradation and never synthesize boxes.

## Open Design Ownership

Open Design may modify only pure presentation under:

```text
frontend/src/features/evidence-matrix/ui/**
frontend/src/features/evidence-analysis/ui/**
frontend/src/features/topic-candidates/ui/**
frontend/src/design-preview/** presentation/CSS needed for these modules
```

Open Design should replace the minimal Workspace preview components, add CSS/responsive composition,
and preserve the frozen exported Props/Event signatures and fixture meanings.

Codex-protected paths:

```text
frontend/src/api/generated/**
frontend/src/api/adapter/**
frontend/src/features/*/model.ts
frontend/src/features/*/mappers.ts
frontend/src/features/*/queries.ts
frontend/src/features/*/mutations.ts
frontend/src/features/*/containers/**
frontend/src/features/*/fixtures/**
frontend/src/features/literature/m3-route-contract.ts
frontend/src/routes/**
frontend/scripts/**
```

## Known Integration Limits

- `M3-ISSUE-0013`: TopicCandidate formal persistence/API lacks independent `limitations`; UI keeps
  it unavailable and never maps `major_risks` into limitations.
- `M3-ISSUE-0014`: no formal TopicGenerationRun/TopicCandidate GET projection exists yet.
- `M3-ISSUE-0015`: Evidence Search and first Summary creation lack explicit server capability
  projection; production containers keep these actions disabled until supplied.
- `M3-ISSUE-0016`: Topic generation currently returns HTTP 202 Job acceptance; UI treats it only as
  pending and never as topic success, but the global no-202 contract requires Stage 8 resolution.

## Focused Verification

```text
TypeScript no-emit: PASS
M3 fixture contract tests: PASS (5)
UI ownership boundary guard: PASS
Production mock guard: PASS
Generated-client consistency: PASS
Full build and Playwright: NOT RUN by Stage 5 policy
```

```text
READY_FOR_OPEN_DESIGN=YES
STAGE_RESULT=PASS_WITH_ISSUES
NEXT_STAGE_EXECUTED=NO
```

## Stage 6 Production Integration

Stage 6 has connected the frozen contracts to the real generated client and the single production
route at `/projects/$projectId/literature`. The route restores `view`, `documentId`, `extractionId`,
`fieldId`, `evidenceSpanId`, `summaryId`, and `topicRunId` from URL search state after refresh. Legacy
`searchRunId` links continue to use the M2 literature workspace.

The matrix production surface now provides the fixed ten fields through TanStack Table, server
sorting/filtering intents, local-only selection, correction/confirmation/decision/verification
mutations with capability re-checks, and exact query invalidation after server success. Unknown
permissions/statuses and stale conflicts remain explicit and fail closed.

`pdfjs-dist@6.2.108` is adopted with its matching package worker. It receives only the authorized
Artifact download URL and server evidence projection. Server page/source/hash/offset/box data remain
authoritative; PDF.js renders and jumps only. Missing coordinates and pypdf use page/text degradation
with zero synthetic boxes and cannot upgrade `VERIFIED`.

Analysis renders the completed current-included-literature scope, counterexamples, insufficiency and
source IDs. Topic rendering accepts only a valid server projection of exactly three sourced items and
never pads or truncates. Topic read deep links and first analysis/topic actions stay unavailable where
Issues 0014-0016 mean the server has not projected a trustworthy capability or terminal resource.

No Open Design output was present at integration time (`M3-ISSUE-0017`). The current CSS and
Workspaces are therefore the smallest usable desktop/mobile production composition using existing
RECA primitives; Open Design still owns final visual refinement under the paths listed above.

Stage 6 focused verification:

```text
Production TypeScript: PASS
Generated-client consistency: PASS
UI boundary guard: PASS (4)
Production mock guard: PASS (6)
M3 fixture contract tests: PASS (5)
Focused Playwright: PASS (4)
Repository-wide test TypeScript: OPEN as M3-ISSUE-0018
```

```text
READY_FOR_OPEN_DESIGN=YES
STAGE_RESULT=PASS_WITH_ISSUES
NEXT_STAGE_EXECUTED=NO
```

## Stage 8 Open Design Delivery And Integration

The previously missing Open Design output is now supplied in the frozen pure-presentation ownership
paths and integrated with the existing production Containers. Props, Events, fixtures, Route search
semantics, generated client and server-owned capabilities remain unchanged.

Delivered presentation changes:

```text
frontend/src/features/evidence-matrix/ui/**
frontend/src/features/evidence-analysis/ui/**
frontend/src/features/topic-candidates/ui/**
frontend/src/features/literature/M3LiteratureWorkspacePage.tsx
frontend/src/features/literature/m3-literature-workspace.css
frontend/src/components/ui/sidebar.tsx (tablet flex-width correction only)
```

Acceptance evidence:

```text
1440x900 desktop: matrix and PDF remain simultaneous; stable minimum pane widths; real highlight
820x1024 tablet: Matrix/Evidence segmented mode; no page-level horizontal overflow
390x844 mobile: single evidence surface; long hash/source text wraps; actions remain stable
Keyboard: view tabs traverse in order with a visible focus indicator
pypdf/no coordinates: text-only degradation, zero synthetic rectangles, Verify disabled
Unknown/capability failure: fail-closed controls retained
TypeScript: PASS
UI boundary guard: PASS (4)
Production mock guard: PASS (6)
M3 fixture contracts: PASS (5)
Focused M3 and shared-shell Playwright: PASS (12)
```

Temporary visual captures were reviewed outside the repository; no screenshot, fixture chrome or
design-preview dependency enters the production bundle.

```text
READY_FOR_OPEN_DESIGN=NO
OPEN_DESIGN_OUTPUT_INTEGRATED=YES
VISUAL_ACCEPTANCE=PASS
STAGE_RESULT=PASS_WITH_ISSUES
NEXT_STAGE_EXECUTED=NO
```
