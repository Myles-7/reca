# M4 to M5 Handoff

Date: 2026-08-04
Source migration head: `0014_m4_data_quality`

## M5 Consumable Facts

M5 may consume only server-projected facts from an accessible project:

- a `DatasetVersion` whose `status` is `AVAILABLE`;
- its immutable `artifact_id`, `data_hash`, `schema_hash`, `projection_hash`, parent Version and
  optional `transformation_id`;
- `DatasetColumn` rows whose `confirmation_status` is `CONFIRMED`, including confirmed type,
  semantic role, unit, identifier and sensitivity facts;
- the latest relevant completed `DataQualityRun`, its normalized Issues and warning state;
- formal version history and pairwise comparison/lineage reads;
- `DataTransformation.parameters_hash`, affected counts, output Artifact, optional `log_artifact_id`
  and ProcessingRun implementation metadata.

M5 must not infer these facts from browser selection, upload completion, a queued Job, AI output,
Preview output or an HTTP 202 response.

## Required Revalidation

Before every M5 analysis or figure command, the backend must revalidate:

1. actor membership and the formal M5 allowed action;
2. all referenced objects belong to the same project and Dataset lineage;
3. DatasetVersion remains `AVAILABLE` and its Artifact remains `AVAILABLE` with matching SHA-256;
4. required DatasetColumns remain formally `CONFIRMED` and are not invalidated by a newer Version;
5. quality warnings and sensitive-field rules are explicitly acknowledged where the future M5
   contract requires acknowledgement;
6. request `If-Match`, Idempotency-Key, input hash and Analysis/Figure parameter hash are current;
7. unknown status, permission, allowed action or relation fails closed with no-disclosure behavior.

## Allowed Actions And Invalidation

- M5 permissions and allowed actions must be server-projected; missing/unknown values disable writes.
- A new current DatasetVersion does not rewrite earlier analysis input. It marks dependent future M5
  results stale through explicit lineage/invalidation rules.
- Invalidated Versions, changed column confirmations, changed quality facts or hash mismatch must
  block new execution and invalidate or stale dependent M5 artifacts according to M5's own contract.
- Retry may reuse the same immutable inputs and parameter identity, but idempotent replay must not
  create duplicate AnalysisResult, Figure, Artifact or formal Version rows.

## Ownership Boundary

M5 must not:

- overwrite, delete, recalculate or mutate an M4 DatasetVersion or original/derived Artifact;
- rewrite M4 quality Runs/Issues, CleaningPlan, Approval or Transformation facts;
- execute an M4 unavailable action or introduce arbitrary Python, SQL, shell or expression execution;
- unmask sensitive values in prompts, logs, Issues, Events or browser payloads without a future
  explicit server scope;
- present AI suggestions as deterministic statistical results, formal approvals or completed Jobs.

M5 may add its own additive migrations, Analysis/Figure domain models, deterministic engines,
versioned parameters and derived Artifacts while referencing M4 inputs by immutable IDs and hashes.

## Known Constraints

- M4 bounded CSV/XLSX parsing and preview are not a general large-data execution engine.
- Only the five M4 Competition-Core Cleaning actions are executable.
- One LOW Babel development-tooling advisory remains; monitor before changing frontend build input
  trust assumptions.
- Deferred environment cleanup and generated screenshot/tool metadata are not production data.

## Entry Decision

```text
M4_EXIT=PASS
M4_COMPLETION=APPROVED
M5_ENTRY=ALLOWED
NEXT_STAGE_EXECUTED=NO
```
