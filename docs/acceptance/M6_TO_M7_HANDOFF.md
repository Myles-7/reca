# M6 To M7 Handoff

Status: **READY FOR M7**. This document freezes the M6 contracts for M7 consumption.

## Frozen M6 Facts

- `Manuscript` owns project relationship and discovery state.
- `ManuscriptVersion` is immutable; every derived version uses a new Artifact,
  SHA-256, `parent_version_id`, monotonically allocated `version_number`, and an
  atomic `current_version_id` update. Original uploads are never overwritten.
- Locators are versioned structured locations. Issue evidence is same-project and
  scope-checked; `auto_fixable` is false for high-risk or unsupported content.
- `ManuscriptTransformation` records canonical plan/hash, approval snapshot,
  input/output version and artifact hashes, fixer metadata and failure state.
- Claims retain source object/type, source version and text hash, scope, status and
  actor provenance. `CONFIRMED` is reachable only through `CLAIM_CONFIRMATION`
  Approval; stale source or edits invalidate the old approval.
- Revision audits write read-only `AuditResult` records containing before/after
  versions, finding codes, rule-set version, source hashes, evidence IDs and
  implementation metadata. Current Competition Core codes include numeric,
  citation, causal, scope, figure/version drift and stale-claim findings.

## M7 Consumption Rules

M7 may consume LiteratureRecord, EvidenceSpan, DatasetVersion, AnalysisResult,
Figure, Claim, Issue and AuditResult IDs only after rechecking same-project
membership, `AVAILABLE`/`COMPLETED`/`CONFIRMED` state, hashes, invalidation,
permissions and allowed actions at query time. M7 must not overwrite a
ManuscriptVersion, alter Claim confirmation history, recompute M5 numeric facts or
silently turn an Issue/Audit finding into a pass.

## Open Limitations

The host-only PostgreSQL runner remains an environment limitation; the authoritative
Compose-network migration verification passed. No Evidence Graph, ClaimEvidenceLink,
ReproPackage, Agent or M9 Demo implementation is part of this handoff.

```text
M7_ENTRY=ALLOWED
NEXT_STAGE_EXECUTED=NO
```
