# Security and Open Source Optimization Summary

Document status: `Conditional Approval`

Phase: Security and Open-Source Governance Optimization, Phase 3 final synchronization

Date: 2026-07-31

Root license: `PENDING_GOVERNANCE_DECISION`

Phase result: `PASS`

## 1. Scope

This report closes the three-phase documentation-only optimization. Phase 1 inventoried the old policy, Phase 2 rewrote the authoritative security, open-source and ARS-Codex policy, and Phase 3 synchronized active entry documents, implementation guidance, contracts, testing, milestones and third-party registration guidance.

No third-party Prompt, code, script, test or other asset was copied. No dependency, code, container, CI, migration, lock file, generated client or runtime configuration changed.

## 2. Policy Change

| Area | Previous policy | Current policy |
| --- | --- | --- |
| Security objective | Production-style controls broadly treated as delivery requirements | Competition-first minimum safeguards, visible warnings and deferred production hardening |
| Approval | Broad confirmation posture could imply formal approval for ordinary actions | `NONE`, `LIGHT_CONFIRMATION` and `FORMAL_APPROVAL` are selected by research risk |
| Open-source reuse | Research reference and clean-room reimplementation were the default posture | Effect-first licensed reuse through dependency, service, Fork, Vendor, Submodule or selective copy |
| Adapter | Broad architectural default for third-party capability | Chosen by replacement, domain, Mock, license, security and maintenance benefit |
| ARS-Codex | Research-only and mandatory clean-room posture | Selective or full reuse permitted after exact license, attribution and purpose review |

Competition Edition remains aimed at personal use and school competition. Scientific truthfulness, original-object immutability, minimum privacy and lawful attribution remain hard boundaries.

## 3. Competition Safeguards

### 3.1 RELEASE_BLOCKER

- real Secrets committed, bundled into frontend output or written to ordinary logs;
- original PDF, data or DOCX can be overwritten;
- a model produces formal statistical numbers;
- literature, EvidenceSpan or citations are fabricated;
- uploaded files can execute or escape controlled paths;
- Agent can execute arbitrary Shell, SQL or Python;
- no-license or unknown-source content is copied;
- required third-party license, copyright or NOTICE is removed;
- CC BY-NC or other special-license content is not isolated or attributed;
- demo material includes unauthorized sensitive or restricted content;
- failure or degradation is represented as formal success;
- a Critical supply-chain issue is reachable from the actual execution path;
- any of the six M0 required CI jobs or applicable infrastructure clean-room acceptance is bypassed.

### 3.2 COMPETITION_REQUIRED

- keep Secrets out of source, frontend bundles and ordinary logs;
- preserve original PDF, dataset and DOCX objects and create derived versions;
- obtain formal approval before high-risk data, formal-result, version or sensitive-export changes;
- prevent Agent self-approval, Service bypass and arbitrary execution;
- keep deterministic statistics, real evidence and project isolation;
- validate upload type, signature and actual parsing; prevent traversal and execution;
- expose model data scope, failures and degradation;
- record upstream repository, Commit/Tag, license, copied paths, attribution and modifications;
- reject no-license and unknown-source copying;
- keep demo data licensed, permitted and non-sensitive;
- preserve the M0 regression baseline and two disclosed LOW risks.

### 3.3 COMPETITION_RECOMMENDED

- finer-grained RBAC and exposed-login rate limiting;
- antivirus, advanced content sanitization and full quarantine platforms;
- signed URLs where backend streaming is sufficient;
- automated SBOM and automated license scanning;
- automatic blocking of LOW or unrelated MEDIUM advisories;
- full model-data classification and automated masking;
- read-only container filesystems and advanced network policy;
- formal backup exercises, longer log retention and richer monitoring;
- simple database export and MinIO demo copies.

These items are recorded as warnings or enhancements and do not block the school-competition build by themselves.

### 3.4 FUTURE_PRODUCTION

- enterprise SSO, organization hierarchy, access review and complex RBAC;
- public multi-tenant administration and regulatory privacy workflows;
- enterprise Secret Manager, DLP, SIEM and staffed incident response;
- formal vulnerability SLA and enterprise supply-chain governance;
- RPO/RTO, off-site backup, multi-region recovery and disaster exercises;
- advanced WAF, ingress, host and container hardening;
- legal deletion, retention, notification and long-term security archives;
- regional data-residency and compliance evidence.

## 4. Open-Source Reuse Policy

Allowed modes:

```text
PACKAGE_DEPENDENCY
INDEPENDENT_SERVICE
FORK
VENDOR
GIT_SUBMODULE
SELECTIVE_COPY
RESEARCH_REFERENCE
CLEAN_ROOM_REIMPLEMENTATION
```

`CLEAN_ROOM_REIMPLEMENTATION` is optional, not the default.

Before incorporation, record:

```text
project_name
repository
upstream_commit_or_tag
license
license_file_path
integration_mode
copied_paths
modified_paths
modification_summary
attribution_location
special_restrictions
commercialization_review_required
reviewed_by
reviewed_at
```

Prohibited actions include copying no-license or unknown-source content, removing attribution, claiming third-party work as wholly original, using a future root license to overwrite path-specific licenses, or bypassing RECA project, version, evidence and approval rules for integration speed.

`THIRD_PARTY_NOTICES.md` now includes a neutral registration template. It does not create a false ARS-Codex attribution. The existing Full Stack FastAPI Template and M0 dependency/image records remain factual.

## 5. Adapter Decision

Third-party integration uses one of:

```text
DIRECT_LIBRARY_INTEGRATION
ADAPTER_INTEGRATION
ISOLATED_SERVICE_OR_VENDOR
```

Use Adapter when an external API may change, multiple implementations or offline Mock are needed, third-party objects must not leak into the domain, or a license/security boundary or testing benefit is material. Direct integration is allowed for mature, stable, small-interface libraries without replacement need or domain pollution. Large components and special-license boundaries may use an isolated service, Fork or Vendor.

Every mode remains behind the appropriate business Service. Direct integration does not permit Router, Worker or Agent Tool to operate a third-party SDK outside project, permission, version, evidence, audit or formal-result rules.

## 6. Approval Decision

The documentation now uses the following normative policy classification:

```text
NONE
LIGHT_CONFIRMATION
FORMAL_APPROVAL
```

- `NONE`: query, retrieval, parsing, extraction candidates, quality scans, suggestions and previews;
- `LIGHT_CONFIRMATION`: adoption of a candidate question or field, chart choice and low-risk formatting repair;
- `FORMAL_APPROVAL`: research-data modification, imputation, outlier deletion, recoding, formal AnalysisPlan execution, high-risk manuscript change, formal-result invalidation and raw/sensitive export.

These labels do not add an API field, persisted database enum or Tool parameter. Existing `requires_approval`, confirmation records and `ApprovalRecord` express the implementation. Prohibited tools remain absent from the allowlist.

## 7. ARS-Codex Decision

```text
NONCOMMERCIAL_INTENT_DECLARED
selective_or_full_reuse_allowed_after_license_and_attribution_review
no_actual_copy_in_this_documentation_task
commercialization_re_review_required
```

This is not a legal conclusion that a school competition is NonCommercial. Exact upstream license text and path coverage must be checked before copying. Attribution, repository, fixed Commit, copied paths and modifications must be retained; special-license content must remain distinct from the root-license decision.

Reuse does not move Agent runtime before M8, change the single-orchestrator design, permit free multi-Agent operation or bypass Project, Approval, Evidence and Tool contracts.

## 8. Cross-Document Synchronization

| Files | Synchronization |
| --- | --- |
| `README.md` | Added Competition Edition positioning, effect-first reuse, attribution and root-license separation |
| `AGENTS.md` | Replaced old copy prohibitions, added pre-copy checklist, task reading rule and Agent/AI reuse boundary |
| Product entry and UX requirements | Narrowed formal approval to high-risk actions and stated reuse as delivery strategy, not P0 functionality |
| Architecture entry and child specifications | Added direct, Adapter and isolated-service/Vendor modes while retaining Service and domain boundaries |
| Data-model entry and child specifications | Clarified approval policy without deleting ApprovalRecord, AuditLog, ToolCall, ModelInvocation or lineage |
| API/Tool entry and Tool contracts | Applied risk-based approval semantics without changing paths, errors, Schema or Tool names |
| Test entry and child specifications | Added license/source/attribution tests, blocker versus warning rules and approval-risk cases |
| Roadmap entry, common files and M1-M9 | Added lightweight source review in the integration PR and removed mandatory self-rewrite/Adapter assumptions |
| `THIRD_PARTY_NOTICES.md` | Added a registration template and explicit no-actual-ARS-copy statement |
| `backend/README.md` | Repaired its obsolete link to the current root quick-start guide; no backend behavior changed |
| Security, ADR and source-research files | Retained the Phase 2 authoritative competition-first and ARS-Codex decisions |

Historical reports and previous-decision sections may retain old wording as evidence. Active authoritative instructions no longer impose mandatory ARS clean-room reimplementation or universal Adapter use.

## 9. Contract Preservation

Stable identifier comparison against `docs/reports/document-split-baseline/` confirms no intentional business-contract change:

| Type | Result |
| --- | --- |
| Requirement ID | preserved |
| Acceptance ID | preserved |
| API Path | preserved |
| Error Code | preserved |
| AI Schema name | preserved |
| Agent Tool name | preserved |
| Domain Enum value | preserved; policy labels are normative, not persisted Enum additions |
| Milestone ID | preserved |

Literal baseline coverage is 181/181 Requirement IDs, 16/16 Acceptance IDs, 236/236 API paths, 87/87 error codes, 16/16 Schema names, 51/51 Tool names and 20/20 milestone identifiers. The broad Phase 0 enum-candidate inventory already had 23 non-domain candidates absent at the starting HEAD; the current tree has the same 23 absent candidates, so this phase introduced zero enum removals.

M0 remains `COMPLETED`, M1 Entry remains `ALLOWED`, commit `79825914c7c975e8be256a5a89abe812f486769e` and tag `m0-complete` remain unchanged. The six required CI jobs, infrastructure clean-room trigger, `M0-ISSUE-0006`, `M0-ISSUE-0009`, Git-managed Prompt manifest, data-access three-layer semantics, minimal ProjectContextSnapshot, EvidenceSpan non-fabrication, MANU-P0-018 boundary and M8 Agent timing remain intact.

## 10. Deferred

- selection of additional GitHub projects;
- actual Fork, Vendor, Submodule or selective copy;
- actual ARS-Codex copying or runtime integration;
- exact legal review for each special-license path and competition use;
- root project license decision;
- formal `APPROVED FOR M1 DEVELOPMENT` status;
- `docs-m1-approved` tag;
- enterprise production security implementation.

## 11. No-Code-Change Confirmation

This phase modified Markdown documentation and documentation governance records only. The only file under `backend/` was `backend/README.md`, whose broken documentation link was repaired. No backend or frontend source, `docker-compose.yml`, `.github/workflows/`, migration, dependency manifest, lock file, generated client or runtime asset changed.
