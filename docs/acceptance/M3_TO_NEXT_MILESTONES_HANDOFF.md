# RECA M3 to Next Milestones Handoff

```text
M3_EXIT=PASS
M3_COMPLETION=APPROVED
M4_ENTRY=ALLOWED
M6_M7_M3_DEPENDENCY_SATISFIED=YES
M8_AGENT_ENTRY=PROHIBITED_UNTIL_M7
Migration head: 0013_m3_evidence_matrix
```

## M4 Baseline

M4 may reuse project-scoped Artifact, Job, ProcessingRun, ModelInvocation, Audit, idempotency,
optimistic concurrency, generated-client and clean-room patterns. It must create DatasetVersion and
quality-domain truth in its own formal models rather than JSON/local UI state. M4 depends on M1, so
M3 evidence objects are optional inputs, not a reason to couple data-quality state to literature UI.

## M6/M7 Evidence Rules

Consume only project-matched EvidenceSpan IDs with immutable source text/hash, explicit location,
review and verification states, and retained limitations. `NO_LOCATED_EVIDENCE` has no Span;
`LOCATION_UNCERTAIN` is not VERIFIED. Revisions, verification records and decisions are append-only.
Current summaries remain bounded to current INCLUDED literature and retain counterexamples.

## M8 Boundary

No Agent runtime may bypass Service authorization, Job/ProcessingRun, ModelInvocation governance,
EvidenceSpan locator/verification, user-only LiteratureDecision or exactly-three sourced Topic rules.
Formal Agent runtime remains an M8 concern after M7.

## Remaining LOW

- M3-ISSUE-0019: authorized 10-20 real-paper dual-reviewed corpus; metrics NOT MEASURED.
- M3-ISSUE-0021: development-only Babel 7 advisory; reassess before M9 distribution.
- Live model/OpenAlex runs are optional environment evidence and were not substituted for Recorded
  deterministic acceptance.

The worktree is intentionally uncommitted. Create a commit/tag/push only with separate authorization.
