# Academic Research Skills Codex source record

Document version: `1.2.0`

Document status: `Conditional Approval`

Last updated: 2026-07-31

## 1. Source metadata

```yaml
project_name: academic-research-skills-codex
repository: https://github.com/Imbad0202/academic-research-skills-codex
upstream_commit_or_tag: f8d6b061efe98564a3f554c917fce66dcef6ca54
upstream_commit_date: 2026-07-23T10:22:52+08:00
adapter_version: 0.1.22
adapter_tag: v0.1.22
tracked_ars_version: 3.19.0
tracked_ars_repository: https://github.com/Imbad0202/academic-research-skills
tracked_ars_commit: 828ef3b613b0e8b91830da3328a1e33d4eb5ab4c
tracked_experiment_agent_repository: https://github.com/Imbad0202/experiment-agent
tracked_experiment_agent_commit: 9b063fa895eaf1f63ac99ac03f924f8d31aa8d26
license: CC-BY-NC-4.0
license_file_path: LICENSE at the fixed upstream commit
purpose_status: NONCOMMERCIAL_INTENT_DECLARED
integration_mode: RESEARCH_REFERENCE
runtime_dependency: false
vendored_into_reca: false
fork_integrated: false
submodule_added: false
copied_paths: []
modified_paths: []
modification_summary: none; policy update only
attribution_location: this source record; future THIRD_PARTY_NOTICES entry required upon incorporation
special_restrictions:
  - noncommercial restriction requires purpose/distribution review
  - preserve CC BY-NC 4.0 and attribution
  - inspect separately licensed vendored or tracked upstream material
commercialization_review_required: true
reviewed_by: RECA Team documentation review
reviewed_at: 2026-07-31
```

Fixed source:
<https://github.com/Imbad0202/academic-research-skills-codex/tree/f8d6b061efe98564a3f554c917fce66dcef6ca54>

## 2. Change record

| Version | Date | Status | Change |
| --- | --- | --- | --- |
| 1.0.0 | 2026-07-30 | Reviewed | Recorded fixed source and research-only clean-room decision |
| 1.1.0 | 2026-07-31 | Conditional Approval | Recorded effect-first permitted modes, noncommercial intent and incorporation prerequisites; no content copied |
| 1.2.0 | 2026-07-31 | Conditional Approval | Added Phase 5 repository-depth evidence, asset-by-asset RECA mapping and Vendor option comparison; ADR conclusion unchanged and no content copied |

## 3. Current decision

The governing decision is
[ADR-001](../decisions/ADR-001-ARS-CODEX-USAGE.md).

ARS-Codex may be used through licensed `SELECTIVE_COPY`, `FORK`, `VENDOR`,
`GIT_SUBMODULE`, development-time `RESEARCH_REFERENCE`, optional
`CLEAN_ROOM_REIMPLEMENTATION`, or a separately approved runtime architecture.

The current actual mode remains:

```text
RESEARCH_REFERENCE
```

No ARS-Codex Prompt, workflow, code, schema, script, test corpus, fixture or
other copyrightable file has been copied into RECA by this policy update.

## 4. Purpose and license caution

The project owner currently intends RECA for personal development/use and
school-competition demonstration. The recorded state is:

```text
NONCOMMERCIAL_INTENT_DECLARED
```

This source record does not state `LEGALLY_CONFIRMED_NONCOMMERCIAL`. It does not
conclude that a competition, prize, sponsorship, public repository, download,
portfolio or hosted deployment satisfies the CC BY-NC 4.0 NonCommercial
condition. Exact use and distribution must be reviewed before incorporation and
again before commercialization or public product deployment.

The fixed upstream license text must be re-read at the time of incorporation.
The review must also check whether tracked/vendored workflow material, fixtures,
datasets or subprojects contain additional licenses or attribution obligations.

## 5. Verified upstream facts

| Fact | Evidence | Confidence |
| --- | --- | ---: |
| The reviewed Codex repository is fixed at `f8d6b061...`, package `0.1.22`, tracking ARS `3.19.0`. | [Repository README](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/README.md), [VERSION](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/VERSION) | High |
| The package pins ARS and experiment-agent repositories by Commit. | [Suite manifest](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/skills/academic-research-suite/manifest.json) | High |
| One root skill routes to research, paper, reviewer, pipeline and experiment workflows. | [Root skill](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/skills/academic-research-suite/SKILL.md) | High |
| Broad topics are routed through Socratic scoping before drafting. | [Scoping override](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/skills/academic-research-suite/SKILL.md#paper-topic-scoping-override) | High |
| Normal Codex behavior runs role prompts inline; automatic subagent spawning is not the default. | [Runtime mapping](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/skills/academic-research-suite/SKILL.md#codex-runtime-mapping) | High |
| Optional full-runtime, Agent-team and hook profiles are disabled by default. | [Full-runtime manifest](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/skills/academic-research-suite/codex/full-runtime-manifest.json) | High |
| External cross-model review requires explicit configuration and content consent. | [Security boundaries](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/skills/academic-research-suite/SKILL.md#security-boundaries) | High |
| The package contains schemas, degradation contracts, gold/held-out fixtures and deterministic validators. | [Shared resources](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/skills/academic-research-suite/SKILL.md#shared-resources) | High |
| The root and included workflow material are presented under CC BY-NC 4.0 in the reviewed snapshot. | [LICENSE](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/LICENSE) | High for root; file-level review still required before copying |

## 6. Reusable asset categories

Subject to exact license and path review, useful asset categories include:

| Asset category | Potential RECA use | Recommended initial mode |
| --- | --- | --- |
| Root routing and workflow selection | StageResolver and prompt-mode design | `SELECTIVE_COPY` or `RESEARCH_REFERENCE` |
| Socratic research-question scoping | Candidate research question workflow | `SELECTIVE_COPY` with RECA Schema adaptation |
| Academic pipeline templates | Milestone and checkpoint flow | `SELECTIVE_COPY` or `FORK` |
| Claim, citation and reading-scope audits | Evidence and manuscript audit policy | `SELECTIVE_COPY` with deterministic validators |
| Degradation contracts | Failure and fallback records | `SELECTIVE_COPY` or direct schema adaptation after review |
| Prompt and output schemas | Prompt manifest and golden tests | `SELECTIVE_COPY`, preserving attribution |
| Scripts and deterministic validators | Development/test tooling | `SELECTIVE_COPY`, `VENDOR` or `FORK` depending coupling |
| Gold, held-out and mutation tests | Prompt/Schema CI and adversarial cases | `SELECTIVE_COPY`; check fixture/data rights separately |
| Whole workflow suite | Development resource or possible runtime | `FORK`/`VENDOR`; runtime requires separate ADR |

This table authorizes review, not automatic copying. The exact `copied_paths`
and `modified_paths` must be recorded before content enters RECA.

## 7. Required attribution and modification record

For any incorporated content, preserve at minimum:

- project and author attribution required by upstream;
- CC BY-NC 4.0 license text and applicable notices;
- upstream repository and fixed Commit/Tag;
- copied file/path list;
- RECA modification list and summary;
- date and reviewer;
- special restrictions and commercialization review flag;
- location in `THIRD_PARTY_NOTICES.md`;
- separation from the future RECA root-license coverage.

For a whole or large Vendor/Fork, use the structure recommended in
[Open Source Governance](../security/OPEN_SOURCE_GOVERNANCE.md), including
`LICENSE`, applicable `NOTICE`, `UPSTREAM.md`, `ORIGINAL_COMMIT` and
`MODIFICATIONS.md`.

## 8. RECA architecture mapping

Reuse does not mean importing upstream runtime assumptions unchanged.

| ARS-Codex asset/concept | Required RECA mapping |
| --- | --- |
| Workflow router | `StageResolver` using persisted ResearchProject state |
| Material Passport | Read-only, database-regenerable `ProjectContextSnapshot` |
| Human checkpoint | Appropriate `LIGHT_CONFIRMATION` or version-bound `FORMAL_APPROVAL` |
| Role prompt | Prompt mode inside the single `ResearchOrchestrator` unless a later ADR decides otherwise |
| Tool/action | Allowlisted Tool calling a tested Service |
| Model result | Strict Schema, ModelInvocation audit and no direct business truth |
| Statistical or figure output | Deterministic RECA tool result, never model calculation |
| Citation/claim audit | EvidenceSpan/ClaimEvidenceLink validation and AuditResult |
| Degradation | Persisted/user-visible DegradationRecord or equivalent audit state |

The single orchestrator remains scheduled for M8. Reuse does not introduce free
multi-Agent state, move business state into sessions, or advance Agent runtime
before deterministic capabilities and approval contracts exist.

## 9. Integration mode recommendations

### Development-time assets

Prefer `RESEARCH_REFERENCE` or reviewed `SELECTIVE_COPY` for Prompt, workflow,
schema and test assets. Keep copied files isolated enough to preserve attribution
and make upstream comparison practical.

### Highly coupled workflow suite

Prefer `FORK` or `VENDOR` if RECA needs a large coherent portion. Record upstream
Commit, modifications, upgrade policy and license boundary.

### Runtime component

Requires a separate ADR covering exact package/service, data access, Tool and
Service mapping, offline/degradation behavior, license packaging, upgrade and
removal. No runtime integration exists today.

### Clean-room mode

Use `CLEAN_ROOM_REIMPLEMENTATION` only when direct reuse creates unacceptable
license, commercialization, coupling or maintenance risk. It is optional.

## 10. Commercialization and public-deployment review gate

Re-review is mandatory before:

- paid or commercial SaaS use;
- sponsorship or competition terms that may affect NonCommercial analysis;
- public hosted product deployment;
- downloadable/public redistribution of copied content;
- root-license publication covering a mixed repository;
- transfer to an organization with different use objectives;
- upgrading to a different upstream Commit or license.

The review may result in continued use, additional attribution, isolation,
replacement, relicensing request or removal. This document does not prejudge the
legal outcome.

## 11. Current incorporation confirmation

As of 2026-07-31:

```text
ARS-Codex content copied into RECA: none
ARS-Codex runtime dependency: no
ARS-Codex Vendor directory: no
ARS-Codex Fork integrated: no
ARS-Codex Git Submodule: no
THIRD_PARTY_NOTICES entry required by actual incorporation: no
```

The temporary external research clone was not added to RECA's source tree,
build context, dependency graph, container images or runtime.

## 12. Phase 5 repository-depth inspection

The Phase 5 review inspected the fixed snapshot rather than relying only on the
root README. The snapshot is a Codex-native distribution that vendors two fixed
upstreams and adapts them through one root router Skill.

### Repository and runtime facts

| Field | Verified value |
| --- | --- |
| Default branch | `main` |
| Research commit | `f8d6b061efe98564a3f554c917fce66dcef6ca54` |
| Latest repository tag | `v0.1.22` |
| Package version | `0.1.22` |
| Root license | CC BY-NC 4.0 |
| Main language | Python plus Markdown/JSON/Shell assets |
| Primary install mode | Codex plugin or direct installation of the root Skill |
| Main entrypoint | `skills/academic-research-suite/SKILL.md` |
| Vendored ARS root | `skills/academic-research-suite/ars/` |
| Codex adapter root | `skills/academic-research-suite/codex/` |
| Tracked ARS | `Imbad0202/academic-research-skills@828ef3b6...`, suite `3.19.0` |
| Tracked experiment-agent | `Imbad0202/experiment-agent@9b063fa8...` |
| Automatic subagents | No; role prompts run inline by default |
| Full-runtime profile | Optional and disabled by default |
| Hooks | Preserved for traceability; disabled/not installed by default |
| Cross-model calls | Disabled by default; require provider configuration and content consent |
| Test/evaluation surface | Python validators, fixtures, gold/held-out sets and nested upstream CI metadata |
| Maintenance status | Active at the fixed snapshot; repository not archived |

The root manifest records exactly which upstream paths were included and which
Claude/plugin loader paths were excluded. Nested upstream workflows and CI are
traceability/self-test material; they are not automatically RECA runtime or CI.

### Inspected asset families

The fixed snapshot contains:

- a root Codex routing Skill and command-alias recipes;
- deep-research, academic-paper, paper-reviewer and academic-pipeline workflows;
- an experiment-agent compatibility subtree;
- role/phase prompts under workflow-specific `agents/` directories;
- Material Passport, review, writer, patch, evaluator and audit Schemas;
- PRISMA, compliance, claim verification and revision protocols;
- deterministic validators and transport adapters;
- examples, fixtures, tests, gold sets and held-out evaluation sets;
- optional Codex planner, Agent-team templates, hooks and quality-gate runner;
- upstream design/migration documentation retained as historical evidence.

## 13. Asset inventory and disposition

The classifications below are candidate integration decisions for later
implementation. They do not copy or approve any specific path.

| Asset | Upstream evidence surface | Classification | RECA use and reason |
| --- | --- | --- | --- |
| `SCOPING` | root router topic override; deep-research Socratic mode; research-question prompt | `ADAPT_AND_VENDOR` | Strong candidate-question workflow, but must emit RECA Scoping Schema and preserve separate AI Scoping/ResearchQuestionVersion states |
| `DEEP_RESEARCH` | deep-research workflow, bibliography/source-verification/synthesis prompts | `ADAPT_AND_VENDOR` | Reuse search planning and evidence-synthesis patterns while RECA owns QueryPlan, LiteratureRecord and EvidenceSpan |
| `PRISMA` | systematic-review mode, protocol/report templates, PRISMA-trAIce and compliance gates | `DESIGN_REFERENCE` | P0 should not import the entire 13-role pipeline; reuse checklist/reporting structure only when matched to existing review scope |
| `MATERIAL_PASSPORT` | academic-pipeline state, reset-boundary protocol, passport Schemas | `REWRITE_FOR_RECA` | Useful provenance pattern, but RECA database/Artifact lineage and ProjectContextSnapshot already define authority |
| `CLAIM_VERIFICATION` | claim verification protocol, claim/ref audit prompt, claim Schemas and validators | `ADAPT_AND_VENDOR` | High-value patterns for Claim, EvidenceSpan, ClaimEvidenceLink and AuditResult; must not certify unsupported evidence |
| `MODE_ROUTING` | root Skill router, mode registry, mode advisors | `REWRITE_FOR_RECA` | Translate intent cues into deterministic StageResolver inputs; do not import free workflow state or multi-Agent ownership |
| `CHECKPOINT` | workflow FULL/SLIM/MANDATORY checkpoints and reset ledger | `REWRITE_FOR_RECA` | Map only meaningful decisions to NONE/LIGHT_CONFIRMATION/FORMAL_APPROVAL and persisted project state |
| `REVIEW_REVISION` | revision coach, revision patch protocol, R&R traceability and claim-drift guards | `ADAPT_AND_VENDOR` | Strong M6-M7 candidate for ManuscriptIssue, versioned patches and re-review; deterministic patching must remain controlled |
| `PAPER_REVIEW` | reviewer workflow, independent reviewer prompts, rubrics and editorial synthesis | `DESIGN_REFERENCE` | Use rubric and dissent-preservation ideas without importing a free multi-reviewer runtime into Competition Core |
| `PROMPTS` | workflow/agent Markdown prompts and command recipes | `ADAPT_AND_VENDOR` | Select high-value prompts, split into RECA Prompt manifests and strict Schemas, preserve attribution and hashes |
| `POLICY_MARKERS` | IRON RULE, mandatory/advisory markers, degradation and compliance protocols | `REWRITE_FOR_RECA` | Convert useful markers into RECA ToolPolicy, ApprovalPolicy, evidence and degradation rules; never treat prose markers as enforcement alone |
| `TESTS` | validator tests, mutation tests, fixtures and adapter tests | `ADAPT_AND_VENDOR` | Reuse test structures selectively after fixture rights and RECA contract mapping are reviewed |
| `GOLDEN_CASES` | `evals/gold`, held-out sets, calibration and robustness fixtures | `ADAPT_AND_VENDOR` | Useful for Prompt/Schema regressions, but imported cases need license, provenance, sensitive-data and domain-fit review |
| `SCRIPTS` | deterministic checkers, audit wrappers, patch and verification scripts | `ADAPT_AND_VENDOR` | Candidate development/test tooling; each script needs dependency, path, side-effect and platform review |
| `HOOKS` | upstream and Codex hook metadata | `DO_NOT_USE` | Hooks are runtime-specific, disabled by default upstream and can create invisible behavior; RECA should implement explicit Services/jobs/tests instead |

No category is classified `DIRECT_REUSE` without adaptation. Even high-value
assets encode ARS file-state, role, checkpoint and runtime assumptions that do
not match RECA's database-owned architecture.

## 14. Precise ARS-to-RECA mapping

| ARS asset | RECA object or module | Milestone | Integration method |
| --- | --- | --- | --- |
| Scoping / Socratic research-question flow | `ResearchQuestionVersion`, AI Scoping output Schema and existing confirmation flow | M2 | `ADAPT_AND_VENDOR` selected prompt/rubric; strict RECA Schema; no direct state import |
| Deep Research search planning | `QueryPlan`, literature provider/search run and `LiteratureRecord` candidate flow | M2-M3 | Adapt workflow/prompt patterns; execute through existing literature Services and Tools |
| Source verification and evidence packing | `DocumentChunk`, candidate evidence, `EvidenceSpan` validation | M3 | Adapt verification rubrics; require page/text/source checks before EvidenceSpan creation |
| PRISMA systematic-review assets | Existing literature review requirements and reporting/export surface | M3/P1 enhancement | Design reference first; selective templates only after scope and license review |
| Material Passport | `Artifact`, `ArtifactRelation`, version lineage, `ProjectContextSnapshot` | M1-M7 | Rewrite as database queries and derived snapshot metadata; never a second source of truth |
| Claim verification | `Claim`, `ClaimEvidenceLink`, `EvidenceSpan`, `AuditResult` | M6-M7 | Selectively adapt prompts, Schemas and deterministic consistency tests |
| Review/revision workflow | `ManuscriptIssue`, `ManuscriptVersion`, manuscript checks and approvals | M6-M7 | Adapt revision planning and claim-drift tests; RECA owns version and approval transitions |
| Mode router | `StageResolver` | M8 | Rewrite deterministic rules and bounded intent classification; one Orchestrator only |
| Checkpoint | Approval policy and persisted project state | M1-M8 | Map to NONE/LIGHT_CONFIRMATION/FORMAL_APPROVAL; do not require formal approval at every ARS checkpoint |
| Agent role prompts | Prompt modes inside `ResearchOrchestrator` | M8 | Selective Prompt Vendor with manifests; no independently stateful free Agent team |
| Prompt assets | Git-managed `PromptContract` manifest and AI Schemas | M1+ | Selective adaptation begins only with a licensed incorporation PR; runtime consumption follows feature milestones |
| Commands/workflow templates | RECA tasks, Services and Agent routes | M1-M8 | Treat as design recipes; do not register upstream slash commands as business APIs |
| Policy markers | ToolPolicy, ApprovalPolicy, ModelDataPolicy, evidence/audit policies | M1-M8 | Translate into executable checks and tests, preserving RECA terminology |
| Tests and golden cases | Prompt, Schema, Tool, evidence and milestone golden tests | M1-M9 | Selectively Vendor compatible cases and record fixture rights/source |
| Scripts | Development/test validators or narrow deterministic workers | M1-M9 | Per-script review; no arbitrary Shell/Python Tool exposure to the Agent |
| Hooks | No direct RECA runtime object | None | Do not install; convert desired checks into explicit CI, jobs or Services if separately approved |

### Mapping rules

- ARS candidate references never become `EvidenceSpan` without RECA source and
  location validation.
- Material Passport content cannot overwrite ResearchProject, Artifact,
  ApprovalRecord or versioned domain objects.
- ARS checkpoints are not copied mechanically; read-only/candidate work remains
  automatic and only high-risk facts/versions require formal approval.
- Role prompts remain Prompt assets. They do not create a new stable Tool, API,
  Schema, Enum or milestone.
- ARS multi-role language can be executed as modes inside the single
  `ResearchOrchestrator`; it does not imply autonomous peer Agents.
- Deterministic ARS scripts may support tests or narrow Services, but they are
  never exposed as a generic Python/Shell execution capability.

## 15. Selective Vendor versus full snapshot

### Option A: selective Vendor

Candidate structure, not created by this phase:

```text
vendor/ars-adapted/
├── LICENSE
├── ATTRIBUTION.md
├── UPSTREAM_COMMIT
├── MODIFICATIONS.md
├── selected-prompts/
├── selected-workflows/
└── selected-tests/
```

### Option B: full snapshot Vendor

Candidate structure, not created by this phase:

```text
vendor/academic-research-skills-codex/
├── LICENSE
├── UPSTREAM.md
├── ORIGINAL_COMMIT
├── MODIFICATIONS.md
└── ...
```

### Comparison

| Dimension | Selective Vendor | Full snapshot Vendor |
| --- | --- | --- |
| Demonstration effect | Focuses effort on scoping, claim verification, revision and golden cases that visibly improve RECA | Preserves the broad suite, including many capabilities RECA may never expose |
| Development speed | Faster after an initial asset-selection pass; less runtime adaptation | Fastest archival import, but slower before usable integration because many paths assume ARS runtime/state |
| License isolation | Clear copied-path ledger and compact attribution boundary | Strong physical snapshot boundary, but all distributed content remains under special-license review |
| Maintenance | Smaller diff and test surface; manual upstream cherry-pick decisions | Easier whole-snapshot comparison, much larger update and regression surface |
| Context pollution | Low if assets are grouped by RECA feature and manifests | High: hundreds of prompts/docs/fixtures can confuse Codex and duplicate authority |
| RECA architecture adaptation | Explicit conversion to Project/Approval/Evidence/Tool contracts | High risk of importing Material Passport, checkpoint and multi-role assumptions unchanged |
| Test reuse | Can select contract-relevant fixtures and validators | Includes broad upstream tests, some requiring excluded Claude/plugin inputs |
| Removal cost | Per-feature removal is straightforward | Snapshot removal is simple physically, but downstream coupling may be broad |
| Commercialization re-review | Narrow path list can be assessed/replaced | Entire snapshot and all derived use must be re-reviewed |

### Recommendation

Prefer **Option A, selective Vendor**, beginning with scoping, claim verification,
revision safeguards, selected policy markers and compatible golden tests. Keep
the fixed upstream repository/Commit in the evidence record so omitted assets
remain discoverable.

Use a full snapshot only if a later spike proves that maintaining the coherent
suite produces substantially better results than selective adaptation and a
separate architecture/license decision accepts the context and maintenance
cost. This recommendation does not amend ADR-001's permission or runtime gate.

## 16. Runtime assumptions and incompatibilities

ARS-Codex assumes a conversational Codex Skill environment, Markdown role
prompts, file-based workflow artifacts and optional runtime features controlled
by environment flags. The optional full-runtime profile can plan Agent teams and
hooks, but is disabled by default. Cross-model transport and some source checks
assume explicit credentials, network access and consent.

RECA differs in material ways:

- project and workflow state are durable database facts;
- Tools are stable allowlisted contracts calling application Services;
- Agent runtime is M8 and uses one Orchestrator;
- Approval is risk-based and version-bound, not a generic checkpoint prompt;
- evidence must join verified source text and location semantics;
- deterministic programs own formal statistics and transformations;
- Prompt manifests are Git-managed from M1;
- ToolCall, ModelInvocation and AgentRun are persisted audit records;
- arbitrary hooks and generic code execution are prohibited.

Therefore ARS-Codex is best treated as a high-value asset library and workflow
research source, not as an application framework that owns RECA state.

## 17. Phase 5 validation spikes

Before copying any ARS path:

1. choose one asset family and list exact files;
2. re-read the fixed root license and inspect file-level/upstream notices;
3. add the required attribution/source/modification record;
4. translate its inputs/outputs to existing RECA Schemas without new IDs;
5. run it against recorded/golden RECA cases;
6. test missing, conflicting and fabricated evidence;
7. verify it cannot write project state or self-approve;
8. measure context/token cost against a RECA-native prompt baseline;
9. confirm no free multi-Agent runtime or early M8 dependency is introduced;
10. retain a clean removal path.

The first recommended spike is the M2 Scoping prompt/rubric plus golden cases,
implemented as a PromptContract candidate rather than a runtime Agent. A second
spike should test claim-verification assets against M6-M7 EvidenceSpan and
AuditResult fixtures.

## 18. Phase 5 decision boundaries

```text
usage_intent: NONCOMMERCIAL_INTENT_DECLARED
recommended_reuse: selective Vendor after path-level license and attribution review
runtime_component: not approved by this research phase
single_orchestrator: preserved
M8_boundary: preserved
actual_content_copied: none
ADR-001_formal_decision_changed: no
commercialization_re_review_required: true
```

This research does not state that school competition use is legally confirmed
NonCommercial. It records the project owner's intent and preserves the review
gate for changed use, sponsorship, public distribution or commercialization.

## 19. Sources

- [ARS-Codex repository at fixed Commit](https://github.com/Imbad0202/academic-research-skills-codex/tree/f8d6b061efe98564a3f554c917fce66dcef6ca54)
- [ARS-Codex LICENSE](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/LICENSE)
- [ARS-Codex root skill](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/skills/academic-research-suite/SKILL.md)
- [ARS-Codex suite manifest](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/skills/academic-research-suite/manifest.json)
- [RECA ADR-001](../decisions/ADR-001-ARS-CODEX-USAGE.md)
- [RECA Open Source Governance](../security/OPEN_SOURCE_GOVERNANCE.md)
