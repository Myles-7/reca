<a id="adr-005-manuscript-citation-stack"></a>

# ADR-005: Adopt controlled DOCX processing and a staged citation stack

ADR ID: `ADR-005-MANUSCRIPT-CITATION-STACK`

## Status

Accepted on 2026-07-31

Documentation status: `APPROVED FOR M1 DEVELOPMENT`

Decision version: `1.0.1`

Current amendment: 2026-07-31

## Context

RECA needs useful manuscript checks and citation output while preserving original DOCX files and avoiding an unresolved citation-processor license decision.

## Decision

- Use python-docx as the planned direct dependency for supported DOCX traversal and derived-document edits.
- Use lxml or controlled OOXML access only for explicitly tested gaps.
- Never overwrite the original DOCX Artifact; produce a versioned derived file.
- Use a simple deterministic citation formatter for Competition Core.
- Snapshot only the selected CSL styles/locales required for accepted formats after file-level rights review.
- Defer citeproc-js until its license metadata conflict, distribution obligations, isolation mode, and permissive alternatives are resolved.

CSL style files are resources with their own rights and attribution. A resource snapshot must record exact paths, upstream Commit, file hash, `<rights>` metadata, modifications, and locale dependencies. Citation rendering formats supplied metadata; it does not verify the source or establish an EvidenceSpan.

## Alternatives considered

- Copy the complete CSL styles repository: rejected because the competition version needs a small reviewed set.
- Adopt citeproc-js immediately because it is mature: rejected because maturity does not resolve license and packaging ambiguity.
- Edit DOCX files in place: rejected because original material is immutable.

## Consequences

- Full CSL processing remains a later decision; the basic deterministic path is the fallback.
- DOCX/OOXML and citation golden corpora are required before milestone acceptance.
- MANU-P0-018 and all existing manuscript/evidence boundaries remain unchanged.

## Change record

| Version | Date | Status | Change |
| --- | --- | --- | --- |
| 1.0.0 | 2026-07-31 | Accepted / Conditional Approval documentation | Recorded the original decision and its RECA authority boundaries |
| 1.0.1 | 2026-07-31 | Accepted / APPROVED FOR M1 DEVELOPMENT documentation | Synchronized the documentation approval state; decision content and integration facts are unchanged |

## References

- [Master plan](../source-research/OPEN_SOURCE_INTEGRATION_MASTER_PLAN.md)
- [python-docx research](../source-research/projects/python-docx.md)
- [CSL Styles research](../source-research/projects/csl-styles.md)
- [citeproc-js research](../source-research/projects/citeproc-js.md)
