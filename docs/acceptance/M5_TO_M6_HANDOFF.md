# M5 to M6 Handoff

Date: 2026-08-05
Source migration head: `0016_m5_figures`

## M6 Consumable Analysis Facts

M6 may consume only a same-project `AnalysisRun` whose status is `COMPLETED` and not invalidated,
together with immutable `AnalysisResult` rows. Each citation of a number must retain:

- Result schema version, method, variable IDs and effective N;
- statistic, confidence interval, p value/effect fields where applicable;
- warnings and interpretation constraints, including non-causal correlation wording;
- DatasetVersion/input/parameter/environment/code/result hashes;
- the system-generated Code Artifact and available Log Artifact.

M6 must not recompute, overwrite, patch or hide an M5 formal number. Null means unavailable or not
computable according to the schema; it must not be converted into a numeric string or invented value.

## M6 Consumable Figure Facts

M6 may consume only a same-project `Figure` whose status is `CONFIRMED` and not invalidated, with no
open blocking validation issue. It must retain caption, chart type, DatasetVersion, optional AnalysisRun
and AnalysisResult linkage, Figure hash and AVAILABLE PNG/SVG/PDF/Code Artifact hashes.

M6 must not render a replacement, modify an Artifact, or recalculate coefficients, CI, error bars or N.
It may select the appropriate existing format for manuscript layout after rechecking read/download scope.

## Mandatory Revalidation

Before each manuscript reference or export, M6 must revalidate:

1. actor permission, allowed action and read scope are known and current;
2. AnalysisRun/Result/Figure/DatasetVersion belong to the same project;
3. Run remains COMPLETED, Figure remains CONFIRMED and neither is invalidated or stale;
4. every referenced Artifact remains AVAILABLE with matching SHA-256;
5. Figure source IDs and hashes still match the referenced Result and DatasetVersion;
6. unknown status, stale approval/hash, mismatch or missing scope fails closed without disclosure.

Job acceptance, HTTP 202, local pending state, a rendered preview and AI interpretation are not formal
completion facts. M6 may explain results within `interpretation_constraints`, but may not turn
correlation into causation or present AI text as a deterministic statistic.

## M6 Entry Compatibility Audit

The M6 authoritative prerequisites are satisfied:

- M1 provides project-scoped immutable Artifact, Approval, Job, ProcessingRun and audit foundations;
- M3 is completion-approved and provides located EvidenceSpan and literature decision facts;
- M5 is completion-approved and provides deterministic AnalysisRun/AnalysisResult and confirmed Figure
  facts with generated-client and Service read boundaries.

M6 must read analysis identity by joining the formal Plan, Run and Result projections: Plan owns method
and variables, Run owns DatasetVersion/effective N/environment/code/log identity, and Result owns the
immutable structured numeric payload and result hash. It must not copy these into a mutable second
statistical record.

The first M6 migration must be additive after sole head `0016_m5_figures` and must not rewrite `0015`
or `0016`. M6 may add the frozen Manuscript, ManuscriptVersion, CheckRun, Issue, Transformation and Claim
objects plus `MANUSCRIPT_REVISION_AUDIT`; absence of those M6 objects before M6 begins is expected and
is not an M5 gap.

No unresolved M5 issue requires a Manuscript, Claim, citation, Evidence Graph, Export or Agent feature
to be implemented early. M6 can therefore begin directly from this handoff.

## Known Constraints

- One LOW Babel development-tooling advisory remains.
- Figure repeatability is frozen to structural/numeric comparison, not universal byte identity.
- Suggestion and interpretation providers remain explicitly degraded when not configured; M6 must not
  depend on them for formal manuscript facts.

## Entry Decision

```text
M5_EXIT=PASS
M5_COMPLETION=APPROVED
M6_ENTRY=ALLOWED
NEXT_STAGE_EXECUTED=NO
```
