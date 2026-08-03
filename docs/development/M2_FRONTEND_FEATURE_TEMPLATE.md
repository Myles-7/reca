# M2 Frontend Feature Template

## Purpose

The Research Question feature is the reference for M2 UI ownership. It freezes
the frontend route, ViewModel, Props/Event contract, permission projection and
unknown-state behavior before a generated API client is connected.

Open Design owns `ui/` and may use only `ui/contracts.ts`, `model.ts` and typed
`fixtures/`. Codex owns generated API integration, adapter mapping, queries,
mutations, cache invalidation and containers.

## Activation Gate

The production routes are registered because all of the following are true:

1. The backend Research Question API is registered and covered by integration tests.
2. `frontend/openapi.json` contains the approved Research Question endpoints.
3. The generated client exposes those endpoints without manual edits.
4. An adapter implements the frozen query and mutation ports.
5. Permission and allowed-action projections come from the server.

Fixtures remain limited to explicit design previews and tests and must never be
used as a query or mutation port.

## Minimum Structure

```text
features/research-question/
  model.ts
  mappers.ts
  queries.ts
  mutations.ts
  containers/ResearchQuestionContainer.tsx
  ui/contracts.ts
  ui/ResearchQuestionWorkspace.tsx
  fixtures/index.ts
frontend/tests/research-question-template.spec.ts
```

## Frozen Policies

- Route: `/projects/$projectId/research-question`.
- Domain states: `DRAFT`, `NEEDS_INPUT`, `READY`, `CONFIRMED`, `SUPERSEDED`.
- Model scoping output states never map directly to domain states.
- Unknown states use `degraded`, expose no edit, transition or confirmation action.
- Permissions are explicit booleans projected by Codex-owned mapping; UI does not infer roles.
- Saving creates a new version and carries `basedOnVersionId` plus a change reason.
- Confirmation is requested through Approval; a button click is not confirmation success.

## When To Use The Full Template

Use all layers when a feature has remote state, mutations, cache invalidation,
permissions, domain status transitions, conflict handling or an Open Design
workstream that needs typed fixtures.

Do not create this structure for a local formatting component, a stateless
label, a single-use layout fragment or a component without an independent
domain contract. Keep those components beside their owner and extract a layer
only when it removes a real ownership or testing problem.

## M2 Open Design Handoff Baseline

Status: `FROZEN FOR OPEN DESIGN` on 2026-08-02; production activation was
subsequently completed and Stage 9 vertically tested the routes. TypeScript
remains the executable source of truth. The tables below name those sources and
explain how Open Design uses them without copying the complete types into
Markdown.

Shared rules for QueryPlan, Literature and Document:

| Content | Open Design usage |
| --- | --- |
| Input data | Receive only the frozen Props and ViewModel types. Do not consume backend DTOs. |
| User actions | Emit only the frozen discriminated Events through `onEvent`. An emitted event is user intent, not proof of backend success. |
| Loading and errors | Render `Loadable` plus `mutationError`; call `onRetry` only for the load failure path. |
| Permission | Render commands only from mapped permission booleans derived from server `allowed_actions`. Do not infer from role names, status labels or button state. |
| Design data | Import only the feature's typed fixtures. Fixtures are design/test data and never backend acceptance evidence. |
| API access | Files under `ui/` must not import generated client, adapter, TanStack Query, queries, mutations, controllers or containers. |
| Unknown state | Show warning/degraded presentation and keep state-changing or high-risk commands disabled. |
| Container integration | Codex injects the Open Design component as `View: ComponentType<...WorkspaceProps>`. The pure view never reads route params or query state. |

The shared executable types are `Loadable<T>`, `UiErrorViewModel` and
`SemanticTone` in `frontend/src/features/projects/model.ts`. `Loadable<T>` is
frozen to `loading | empty | error | ready`; degraded is a semantic tone or a
fact inside ready data, not a fifth transport state.

### QueryPlan handoff

| Contract | Frozen handoff |
| --- | --- |
| Open Design write area | `frontend/src/features/query-plan/ui/`; visual-only shared primitives may be changed under their normal ownership review. |
| ViewModel | `QueryPlanViewModel` and `QueryPlanFieldsViewModel` in `model.ts`. UI reads `knownStatus`, `tone`, `lockVersion`, fields, `generatedByAi` and mapped permissions. |
| Props | `QueryPlanWorkspaceProps`: `content`, `pendingAction`, `mutationError`, `onRetry`, `onEvent`. |
| Events | `update` and `generate` are dispatchable by the current detail container when their mapped permissions allow them. `update` must return the supplied `queryPlanId`, `lockVersion`, `changeReason` and complete fields. |
| Creation boundary | `create` is type-frozen for the creation workflow, but the current detail `QueryPlanContainer` deliberately rejects it. Open Design may design the state, but must not present it as active until Codex supplies the creation entry/container. |
| Server actions | `query_plan.update` -> `permissions.canUpdate`; `query_plan.generate` -> `permissions.canGenerate`. Unknown QueryPlan status clears both. |
| Typed fixtures | `queryPlanReadyFixture`, `queryPlanLoadingFixture`, `queryPlanDegradedFixture`, and aggregate `queryPlanFixtures`. |
| Container | `QueryPlanContainer({ projectId, queryPlanId, View })`. `projectId` and `queryPlanId` are Codex-owned route inputs and are not view props. |
| Route and IDs | Frozen semantic URL: `/projects/$projectId/query-plans/$queryPlanId`. Both params are project-scoped resource identifiers; the UI must return the ViewModel IDs in events rather than synthesize them. |
| Unknown/degraded behavior | `knownStatus=false`, `tone=degraded`, `canUpdate=false`, `canGenerate=false`; edit, save and AI generation remain disabled. |
| Activation | Production detail route is registered and Stage 9 browser-tested. Detail `create` remains `BLOCKED_BY_CONTRACT`; first-entry creation uses the formal API and server-returned ID. |

### Literature handoff

| Contract | Frozen handoff |
| --- | --- |
| Open Design write area | `frontend/src/features/literature/ui/`; do not merge candidate and formal-record concepts in the view. |
| ViewModel | `LiteratureWorkspaceViewModel`, `LiteratureSearchRunViewModel`, `LiteratureCandidateViewModel` and `LiteratureRecordViewModel` in `model.ts`. |
| Props | `LiteratureWorkspaceProps`: `content`, `pendingAction`, `mutationError`, `onRetry`, `onEvent`. |
| Events | `search`, `import-candidates` and `import-doi` are dispatchable only when their workspace permissions allow them. Candidate selection is local UI state; import intent must submit `searchRunId` and explicit `candidateIds`. |
| Retry boundary | `retry-job` requires the matching formal Job to be failed with `retryable=true` and the project action `job.retry`; missing or unknown data fails closed. |
| Server actions | Project list envelope: `literature.search` -> `canSearch`, `literature.import_doi` -> `canImportDoi`; active run: `literature_search.import` -> `canImport`; candidate: `literature_candidate.import` -> `candidate.canImport`; record: `document.upload` -> `record.canUploadDocument`. |
| Typed fixtures | `literatureReadyFixture`, `literatureLoadingFixture`, `literatureDegradedFixture`, and aggregate `literatureFixtures`. |
| Container | `LiteratureContainer({ projectId, searchRunId?, View })`. `searchRunId` selects an active result set for integration but is not frozen as a browser URL param. |
| Route and IDs | Frozen semantic URL: `/projects/$projectId/literature`. `projectId` is the stable route param. `queryPlanId`, `searchRunId`, `candidateIds`, LiteratureRecord `id` and optional `documentId` come from ViewModels or Codex-owned integration state. |
| Unknown/degraded behavior | `permissionsKnown=false`, all workspace mutation permissions false, unknown run status uses `tone=degraded` and `degraded=true`; import and search commands remain disabled. |
| Activation | Production route is registered and Stage 9 browser-tested, including `searchRunId` refresh recovery. |

### Document handoff

| Contract | Frozen handoff |
| --- | --- |
| Open Design write area | `frontend/src/features/documents/ui/`; Document and LiteratureRecord remain separate visual/resource concepts. |
| ViewModel | `DocumentWorkspaceViewModel`, `DocumentViewModel`, `DocumentPageViewModel` and `DocumentJobViewModel` in `model.ts`. |
| Props | `DocumentWorkspaceProps`: `content`, `pendingAction`, `mutationError`, `onRetry`, `onEvent`. |
| Events | `upload`, `parse` and `retry-job`. Upload returns the selected `File`, explicit document type and optional `literatureRecordId`; parse returns the ViewModel `documentId` plus explicit fallback and coordinate choices; retry returns the projected `jobId`. |
| Server actions | `document.upload` -> workspace `canUpload`; `document.parse` -> `document.permissions.canParse`. Retry additionally requires a known Job state and server-projected `job.retryable`. |
| Typed fixtures | `documentReadyFixture`, `documentLoadingFixture`, `documentFallbackFixture`, `documentDegradedFixture`, and aggregate `documentFixtures`. |
| Container | `DocumentContainer({ projectId, documentId, jobId?, View })`. `jobId` enables progress/retry projection but is not frozen as a browser URL param. |
| Route and IDs | Frozen semantic URL: `/projects/$projectId/documents/$documentId`. `projectId` and `documentId` are stable route params. `artifactId`, page numbers, optional LiteratureRecord ID and Job ID are data/event values, not alternative route identity. |
| Unknown/degraded behavior | Unknown parse status sets `knownStatus=false`, `tone=degraded`, `permissionsKnown=false`, `canUpload=false`, `canParse=false`; no parse or retry action is enabled. pypdf output remains visibly degraded with LOW confidence. |
| Activation | Production route is registered and Stage 9 browser-tested, including `jobId` refresh recovery. |

## Freeze Change Control

The following are breaking handoff changes and require Codex and Open Design
review before implementation: renaming/removing ViewModel fields, changing a
`Loadable` variant, changing Props or Event payloads, changing route params,
changing ID meaning, changing permission projection, or adding a production
fixture dependency. API DTO changes continue through the formal API/OpenAPI
process and do not flow directly into pure UI.

Pure layout, token, typography, responsive, accessibility and component
composition changes inside the Open Design-owned UI boundary do not reopen the
handoff contract unless they require one of the breaking changes above.

Verification commands:

```bash
bun run --cwd frontend format:check
bun run --cwd frontend lint
bun run --cwd frontend check:ui-boundaries
bun run --cwd frontend check:production-mocks
bun run --cwd frontend test:e2e -- projects-m2-frontend-contracts.spec.ts
```
