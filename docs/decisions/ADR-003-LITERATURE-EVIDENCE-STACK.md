<a id="adr-003-literature-evidence-stack"></a>

# ADR-003: Adopt a candidate-first literature and evidence stack

ADR ID: `ADR-003-LITERATURE-EVIDENCE-STACK`

## Status

Accepted on 2026-07-31

Documentation status: `Conditional Approval`

## Context

RECA needs a strong literature demonstration without allowing provider, parser, retrieval, or active-learning state to replace verified project evidence and user decisions.

## Decision

The selected stack is:

```text
PyAlex provider
-> GROBID service and RECA TEI converter
-> DocumentPage / DocumentChunk / LiteratureReference candidates
-> PostgreSQL + pgvector retrieval
-> selected PaperQA2 ranking and packing assets
-> CandidateEvidence validation
-> EvidenceSpan or explicit absence
-> optional ASReview recommendation
-> user LiteratureDecision
```

PDF.js provides display, navigation, text/annotation layers, and highlight interaction. It is not an evidence truth source. GROBID TEI is retained as an intermediate Artifact and converted by RECA. PaperQA2 is eligible only for selective Vendor after an experiment proves value. ASReview is eligible only behind a provider and may rank records but cannot write a final screening decision.

The integration modes and project pins remain those in the master plan. The implementation PR must select compatible released versions or image digests and record any difference from the research Commit.

## Non-substitution rules

- PaperQA candidate evidence is not `EvidenceSpan`.
- ASReview ranking is not `LiteratureDecision`.
- GROBID TEI is not validated document truth.
- PDF.js coordinates are not automatically authoritative evidence coordinates.
- Vector similarity is not evidence validity.

## Fallback

Recorded OpenAlex responses, pypdf degraded parsing, exact SQL/text retrieval, native bounded evidence packing, table-based PDF/evidence review, and manual literature screening remain available. Degradation must be visible.

## Consequences

- Existing Requirements and API/Schema/Tool names remain unchanged.
- Candidate conversion and negative tests become mandatory integration work.
- No upstream project or Agent gains ownership of RECA project state.

## References

- [Master plan](../source-research/OPEN_SOURCE_INTEGRATION_MASTER_PLAN.md)
- [PyAlex research](../source-research/projects/pyalex.md)
- [GROBID research](../source-research/projects/grobid.md)
- [PaperQA2 research](../source-research/projects/paperqa2.md)
- [ASReview research](../source-research/projects/asreview.md)
