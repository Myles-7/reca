# Academic Research Skills Codex source record

## 1. Source metadata

```yaml
repository: https://github.com/Imbad0202/academic-research-skills-codex
upstream_commit: f8d6b061efe98564a3f554c917fce66dcef6ca54
upstream_commit_date: 2026-07-23T10:22:52+08:00
adapter_version: 0.1.22
adapter_tag: v0.1.22
tracked_ars_version: 3.19.0
tracked_ars_repository: https://github.com/Imbad0202/academic-research-skills
tracked_ars_commit: 828ef3b613b0e8b91830da3328a1e33d4eb5ab4c
tracked_experiment_agent_repository: https://github.com/Imbad0202/experiment-agent
tracked_experiment_agent_commit: 9b063fa895eaf1f63ac99ac03f924f8d31aa8d26
license: CC-BY-NC-4.0
usage_decision: research-and-independent-reimplementation
runtime_dependency: false
vendored_into_reca: false
reviewed_at: 2026-07-30
reviewer: RECA Team (documentation review)
copied_content: none
prompt_copying_policy: prohibited; independent reimplementation only
commercialization_risk: CC-BY-NC-4.0 upstream material must not be copied into a potentially commercial/distributed RECA product
```

Fixed source:
<https://github.com/Imbad0202/academic-research-skills-codex/tree/f8d6b061efe98564a3f554c917fce66dcef6ca54>

The researched snapshot was cloned into a temporary external directory. It is
not part of RECA's source tree, build context, dependency graph, container
images, or runtime.

## 2. Executive decision

ARS-Codex is useful to RECA as a design-research and test-pattern source, not
as product backend code or a runtime dependency.

RECA may independently reimplement these ideas:

- staged academic workflows and explicit phase boundaries;
- intent routing and Socratic research-question scoping;
- human checkpoints and fail-closed continuation rules;
- claim, citation, reading-scope, and revision-drift audits;
- degradation records and visible fallback behavior;
- schema, fixture, golden-set, and deterministic quality-gate patterns.

RECA must retain its own architecture:

- database-owned domain state;
- a single controlled research orchestrator;
- service-mediated writes and project authorization;
- explicit `ApprovalRecord` checks;
- allowlisted Agent tools;
- deterministic statistics and figures;
- immutable artifacts and versioned research objects;
- auditable `AgentRun`, `ToolCall`, and model-invocation records.

No ARS-Codex prompt, workflow file, schema, script, or fixture is copied into
RECA by this decision.

## 3. Verified upstream facts

| Fact | Evidence | Confidence |
|---|---|---:|
| The researched repository commit is `f8d6b06...`; package version is `0.1.22` and it tracks ARS `v3.19.0`. | [Repository README](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/README.md), [VERSION](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/VERSION) | High |
| The package pins the upstream ARS and experiment-agent repositories by commit. | [Suite manifest](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/skills/academic-research-suite/manifest.json) | High |
| The Codex entry point is one root `academic-research-suite` skill which routes to five workflow entry files. | [Root skill](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/skills/academic-research-suite/SKILL.md), [full-runtime manifest](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/skills/academic-research-suite/codex/full-runtime-manifest.json) | High |
| A broad paper topic without a clear research question is routed to `deep-research` Socratic mode before outlining or drafting. | [Paper Topic Scoping Override](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/skills/academic-research-suite/SKILL.md#paper-topic-scoping-override) | High |
| Normal Codex behavior runs role prompts inline. Automatic subagent spawning is not the default. | [Codex runtime mapping](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/skills/academic-research-suite/SKILL.md#codex-runtime-mapping) | High |
| The optional full-runtime, agent-team, and hook profile is disabled by default. | [Full-runtime manifest](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/skills/academic-research-suite/codex/full-runtime-manifest.json) | High |
| External cross-model review requires explicit configuration and content consent; unpublished material must not be sent merely because credentials exist. | [Security boundaries](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/skills/academic-research-suite/SKILL.md#security-boundaries) | High |
| The package contains schemas, degradation contracts, held-out/gold fixtures, and deterministic validators for citation, PDF-read, human-read, and revision behavior. | [Shared resources](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/skills/academic-research-suite/SKILL.md#shared-resources), [quality-gate registry](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/skills/academic-research-suite/codex/full-runtime-manifest.json) | High |
| The root and vendored workflow material are licensed under CC BY-NC 4.0. | [License](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/LICENSE) | High |

## 4. Important corrections and limits

### 4.1 Prompt copying is not the recommended use

The statement “可以大规模复制提示词” is rejected.

CC BY-NC 4.0 permits reproduction and adaptation only within its license
conditions, including attribution and the non-commercial restriction. A
competition project that may later be distributed, sponsored, licensed, or
commercialized should not assume that wholesale prompt copying is compatible
with its intended use.

RECA therefore uses clean-room reimplementation:

1. record the upstream idea and fixed commit;
2. write a RECA-owned requirement and domain contract;
3. independently author prompts, schemas, code, and fixtures;
4. avoid distinctive upstream wording, examples, and file-level copying;
5. perform a license review before any future direct reuse.

This is a project risk decision, not legal advice.

### 4.2 “Prompt CI” is a design pattern, not a verified hosted CI guarantee

The fixed Codex repository has no root GitHub Actions workflow for these
vendored tests; its root `.github` tree only contains funding metadata. The
upstream workflow files and test harnesses are vendored under the skill for
traceability and local execution.

It is accurate to say that ARS-Codex provides:

- local quality-gate runners;
- deterministic validators;
- schemas and manifests;
- gold and held-out corpora;
- mutation and fixture tests;
- explicit degradation and parity records.

It is not accurate to claim, from this snapshot alone, that all of those gates
run automatically on every ARS-Codex pull request.

### 4.3 RECA target design is ahead of current implementation

RECA's approved documents define objects such as `ResearchProject`,
`Artifact`, `ApprovalRecord`, `EvidenceSpan`, `ClaimEvidenceLink`,
`AnalysisRun`, and `AgentRun`. The current repository implementation is the M0
foundation and does not yet implement those business models, tables, services,
or Agent runtime.

Therefore:

- “RECA already defines these objects” is true at the design-contract level;
- “RECA already has these objects in the running product” is false at M0;
- ARS-derived runtime work must not bypass the approved M1–M8 milestone order.

### 4.4 Agent-oriented implementation must remain late

`ProjectContextSnapshot`, `StageResolver`, prompt modes, and the orchestrator
may be designed early as schemas and tests. Their production implementation
belongs with M8 after the required domain queries, approvals, deterministic
tools, and evidence-chain services exist.

For the current M1 entry point, the relevant ARS benefit is limited to:

- approval semantics;
- append-only audit thinking;
- artifact provenance;
- failure-state vocabulary;
- future contract test cases.

## 5. RECA adoption matrix

| Upstream pattern | RECA adaptation | Implementation authority | Timing |
|---|---|---|---|
| Single root router | `StageResolver` using persisted project state and explicit intent | RECA query services and Agent policy | Design now; implement M8 |
| Material Passport | Read-only `ProjectContextSnapshot`, regenerated from database facts | RECA query service | Design after core IDs stabilize; implement M8 |
| Socratic scoping | Structured RQ scoping with evidence-bounded candidates and user approval | Research-question service and Prompt contract | M2/M3 UI and service; Agent orchestration M8 |
| Workflow checkpoint | Version-bound `ApprovalRecord` plus service precondition | Approval service | M1 onward |
| Claim/citation audit | `ClaimEvidenceLink`, deterministic existence/version checks, bounded semantic review | Evidence and manuscript services | M6/M7 |
| Human-read scope | Evidence verification status and explicit review scope | Literature/evidence service | M3 |
| Revision drift | Deterministic number, citation, qualifier, causal-word, and figure-version diff | Manuscript quality service | M6 |
| Data-access declaration | Enforced server-side model-data policy and minimal payload builder | Model invocation service | M8 |
| Degradation registry | Persisted/user-visible `DegradationRecord` or equivalent audit event | Adapter/service layer | M1 foundation, extended by module |
| Quality-gate suite | RECA-owned schemas, fixtures, golden tests, injection tests, and version gates | RECA test suite and CI | Incrementally from M1 |

### Adoption ledger

The ledger records RECA's independent adoption decisions. It must not be used
to imply that upstream text, prompts, schemas, scripts, or fixtures were
copied. New upstream reviews append a dated review entry; they do not silently
replace the fixed commit above.

| Pattern | Adoption status | RECA authority | Milestone | Direct copy |
|---|---|---|---|---|
| Socratic scoping | Planned | Product/API contract | M2 | No |
| Evidence verification and read scope | Planned | Domain model/API/test contract | M3 | No |
| Revision drift audit | Planned | Manuscript/evidence/test contract | M6 | No |
| Claim finding codes | Planned | Evidence/API/test contract | M7 | No |
| Context snapshot and stage resolver | Planned | Agent architecture/API/tool contract | M8 | No |
| Prompt manifest and contract gates | Planned | Agent/API/test contract | M8, with test scaffolding earlier | No |
| Degradation disclosure | Planned | Adapter/service/security contract | M1 onward | No |

## 6. Priority recommendation

### Now: M1-safe work

1. Keep this source record and the corresponding ADR.
2. Implement the approved M1 objects: Project, Artifact, Approval, Job, and
   audit foundations.
3. Add RECA-owned approval-bypass, project-isolation, immutable-artifact, and
   degradation-state tests.
4. Define only the minimum future Agent DTO interfaces needed to avoid blocking
   later work; do not add an Agent runtime.

### M2–M7

1. Implement RQ versioning and Socratic-scoping outputs as normal service/API
   contracts.
2. Implement real literature, document, and evidence objects.
3. Implement deterministic analysis, figure, manuscript, and evidence-chain
   checks.
4. Build golden fixtures from RECA-owned synthetic or licensed material.

### M8

1. Implement `ProjectContextSnapshot`.
2. Implement `StageResolver`.
3. Register RECA-owned prompt modes and strict output schemas.
4. Connect the single `ResearchOrchestrator` to allowlisted service tools.
5. Run routing, injection, approval, schema, degradation, and consistency
   golden tests before enabling side effects.

## 7. Local verification record

The following read-only checks were run against the fixed temporary snapshot:

- `git rev-parse HEAD` returned
  `f8d6b061efe98564a3f554c917fce66dcef6ca54`;
- the adapter quality-gate runner returned `ok: true` for all six reported
  groups: desktop plugin bundle, hook safety, manifest, reviewer fixture,
  single root skill, and upstream lock;
- the manifest reported adapter version `0.1.22`, 16 command routes, five
  workflow templates, and upstream lock `828ef3b...`;
- repository enumeration found 270 Python test files, 62 JSON Schema files,
  and five workflow entry points. These are file counts, not proof that every
  test passes.

A supplementary full-test claim was deliberately not made:

- the active Python environment did not contain `pytest` or `pypdf`;
- direct `unittest` execution confirmed the revision-conservation tests and
  most human-read tests, but PDF tests correctly degraded to `UNAVAILABLE`
  without `pypdf`;
- two permission tests call POSIX-only `os.geteuid()` and errored on Windows.

These limits reinforce the decision to copy test ideas into RECA's own
cross-platform test suite rather than importing the upstream harness.

## 8. Overall confidence

**High** for repository structure, versions, license, routing behavior, default
runtime behavior, and the recommended non-runtime relationship. These facts
were checked against the pinned source and executable adapter gates.

**Medium** for the exact future benefit of individual patterns, because RECA is
currently at M0 and the value will depend on its later domain implementation
and competition constraints.

## 9. Sources

1. [ARS-Codex fixed repository snapshot](https://github.com/Imbad0202/academic-research-skills-codex/tree/f8d6b061efe98564a3f554c917fce66dcef6ca54)
2. [ARS-Codex root skill and router](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/skills/academic-research-suite/SKILL.md)
3. [ARS-Codex suite manifest](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/skills/academic-research-suite/manifest.json)
4. [ARS-Codex optional full-runtime manifest](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/skills/academic-research-suite/codex/full-runtime-manifest.json)
5. [ARS-Codex license](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/LICENSE)
6. [Creative Commons BY-NC 4.0 license deed](https://creativecommons.org/licenses/by-nc/4.0/)
