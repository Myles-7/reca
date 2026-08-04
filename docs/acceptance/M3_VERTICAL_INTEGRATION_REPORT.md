# RECA M3 Vertical Integration Report

## Baseline

```text
Final verification: 2026-08-04 (Asia/Shanghai)
Branch: feat/m2-research-literature
HEAD: 0e3c39dde65feaa8f784fd5fcfb1055cb557bb3c
Migration head: 0013_m3_evidence_matrix
Vertical result: PASS
```

## Deterministic Chain

```text
Confirmed ResearchQuestionVersion with approved ApprovalRecord
-> QueryPlan
-> included/excluded LiteratureRecord
-> immutable PDF Artifact
-> DocumentPage and DocumentChunk
-> RECORDED extraction Job/ProcessingRun/ModelInvocation
-> fixed ten fields and deterministic locator
-> verified, uncertain and no-evidence states
-> matrix and PDF display/highlight/degradation
-> append-only user correction and confirmation
-> UNCERTAIN -> INCLUDED decision history plus EXCLUDED contaminant
-> included-only EvidenceSetSummary retaining counterexample
-> exactly three TopicCandidates with summary-valid Literature/Evidence sources
```

The PostgreSQL vertical test passed against migration head 0013. It uses the RECA-authored synthetic
fixture only for deterministic contract truth, not scientific accuracy. The locator rejects wrong
page/document/project/hash, fabricated source text and ambiguous candidates; pypdf creates no
coordinates and cannot be upgraded to VERIFIED without a deterministic location.

## Verification

| Layer | Result |
| --- | --- |
| Golden/schema/locator | PASS |
| PostgreSQL M3 vertical | PASS |
| Complete database suite | PASS, 310 passed and 2 skipped |
| Role/project/no-disclosure/idempotency/concurrency | PASS |
| Included-only/counterexample/exactly-three | PASS |
| Generated client and production frontend guards | PASS |
| Desktop/tablet/390px/keyboard/degraded visual acceptance | PASS |
| Complete shell Playwright | PASS |

The formal 10-20 real-paper dual-reviewed corpus is still absent (`M3-ISSUE-0019`). Consequently,
field extraction accuracy and human EvidenceSpan agreement remain `NOT MEASURED`; no synthetic or
model-produced answer is reported as annotation truth.

```text
STAGE_RESULT=PASS_WITH_ISSUES
NEXT_STAGE_EXECUTED=NO
```
