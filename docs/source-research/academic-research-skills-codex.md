# Academic Research Skills Codex source record

Document version: `1.1.0`

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

## 12. Sources

- [ARS-Codex repository at fixed Commit](https://github.com/Imbad0202/academic-research-skills-codex/tree/f8d6b061efe98564a3f554c917fce66dcef6ca54)
- [ARS-Codex LICENSE](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/LICENSE)
- [ARS-Codex root skill](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/skills/academic-research-suite/SKILL.md)
- [ARS-Codex suite manifest](https://github.com/Imbad0202/academic-research-skills-codex/blob/f8d6b061efe98564a3f554c917fce66dcef6ca54/skills/academic-research-suite/manifest.json)
- [RECA ADR-001](../decisions/ADR-001-ARS-CODEX-USAGE.md)
- [RECA Open Source Governance](../security/OPEN_SOURCE_GOVERNANCE.md)
