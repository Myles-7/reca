# M7 To M8 Handoff

Date: 2026-08-06
Handoff status: APPROVED

`M8_ENTRY=ALLOWED`

## Frozen M7 Contracts

- ClaimEvidenceLink freezes relation, strength, status, confirmation, invalidation, canonical
  identity, optimistic version and source snapshot. `SUGGESTED` is never `ACTIVE`.
- EvidenceGraph returns authorized node/edge projections with stable IDs, raw and known status,
  risk, completeness, allowed actions, limitations, depth/limit/cursor and explicit partial state.
- Stored link edges and derived domain edges remain distinguishable. Unauthorized objects are
  omitted without existence or count disclosure.
- AuditResult separates execution status from outcome and carries finding codes, limitations,
  target/source snapshots, hashes and invalidation facts. M6 Revision Audit remains supported.
- Export readiness is a deterministic audit over a canonical scope and snapshot hash. Approval is
  bound to readiness, candidate items, policy acknowledgements, expiry and staleness.
- Export, Job, ReproPackage, ExportItem, Manifest and Artifact states are distinct. COMPLETED and
  AVAILABLE are server facts; immutable historical package versions are never overwritten.
- Manifest canonical JSON, ZIP member metadata, SHA-256, source versions, license, sensitive and
  include status must match actual package bytes.

## M8 Consumption Rules

- Every Tool call must revalidate project, membership, source object, read scope, Approval, current
  status, invalidation and hash through the existing M7 Services.
- Unknown status, permissions unknown, missing allowed action, stale Approval, hash mismatch,
  cross-project source or invalidated object must fail closed.
- M8 may request existing M7 API actions but may not directly create an ACTIVE graph edge, modify
  completeness, approve its own Export, skip readiness or rewrite a ReproPackage/Manifest/Artifact.
- M8 may explain evidence strength, limitations and missing evidence, but cannot create scientific
  facts, formal hashes or export approval.
- Queue actor/project/scope/approval/hash payloads are untrusted; Workers must reload authority.
- M8 may only orchestrate M7 abilities that independently passed API, Worker and browser acceptance.

## Allowed Read-Only Inputs

M8 may consume authorized Claim, ClaimEvidenceLink, Graph, completeness, AuditResult, readiness,
Export, Job, Approval, ReproPackage, Manifest and Artifact projections plus their allowed actions.
Read scope and no-disclosure behavior remain authoritative at each request.

## Retained Limits

- Large graph behavior remains bounded by server depth/node limits and progressive cursors.
- Restricted or unknown-license originals remain metadata-only or excluded.
- Sensitive values remain excluded unless both scope and formal Approval allow inclusion.
- Bun supply-chain audit retains one LOW Babel advisory.

`M7_EXIT=PASS`

`M7_COMPLETION=APPROVED`

`NEXT_STAGE_EXECUTED=NO`
