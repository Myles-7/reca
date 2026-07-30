# Security and Open Source Optimization Summary

Document status: `Conditional Approval`

Phase: Security and Open-Source Governance Optimization, Phase 2

Date: 2026-07-31

Root license: `PENDING_GOVERNANCE_DECISION`

Phase result: `CONDITIONAL PASS`

## 1. Scope

This phase rewrote the authoritative security entry, four security child
specifications, ARS-Codex ADR and source-research record. It applied the Phase 1
inventory in
[SECURITY_AND_REUSE_OPTIMIZATION_BASELINE.md](./SECURITY_AND_REUSE_OPTIMIZATION_BASELINE.md).

Modified policy files:

```text
docs/SECURITY_AND_OPEN_SOURCE.md
docs/security/SECURITY_CONTROLS.md
docs/security/FILE_MODEL_AND_AGENT_SECURITY.md
docs/security/OPERATIONS_DATA_AND_INCIDENTS.md
docs/security/OPEN_SOURCE_GOVERNANCE.md
docs/decisions/ADR-001-ARS-CODEX-USAGE.md
docs/source-research/academic-research-skills-codex.md
```

All paths matched the modular documentation structure described by the task.

This phase did not modify README, AGENTS, architecture, product, data-model,
API/Tool, test or roadmap details. Their policy alignment belongs to Phase 3.

## 2. Core Policy Changes

### 2.1 Competition-first security

The entry policy now defines:

```text
COMPETITION_REQUIRED
COMPETITION_RECOMMENDED
FUTURE_PRODUCTION
RELEASE_BLOCKER
```

`RELEASE_BLOCKER` is limited to direct competition-delivery failures involving
Secrets, original-object overwrite, fabricated research evidence, model-created
formal statistics, file execution/path traversal, arbitrary Agent execution,
unlicensed copying, removed attribution, unisolated special-license content,
unauthorized demo material, hidden failure, reachable Critical supply-chain risk
or bypassed M0 required CI/clean-room acceptance.

Low/Medium vulnerabilities, missing enterprise SBOM, missing off-site disaster
recovery and missing formal recovery exercises are no longer competition
release blockers.

### 2.2 Deployment profiles

`SECURITY_CONTROLS.md` now uses:

| Profile | Policy role |
| --- | --- |
| `DEMO_LOCAL` | Default Competition Edition target for single-machine or trusted local-network use |
| `SHARED_SCHOOL` | Optional school-sharing enhancement with basic login, project authorization, simple roles, private files, limits and audit |
| `PUBLIC_PRODUCTION` | Future public/commercial profile that activates enterprise security and compliance design |

Existing authentication, backend authorization, Secret hygiene and project
isolation were retained. The policy does not remove any M0 security feature.

### 2.3 File, model and Agent policy

Minimum file controls retained:

- size and parser resource limits;
- extension, MIME, signature and actual parse validation;
- display-only user file names and system-generated storage keys;
- SHA-256;
- ZIP/DOCX traversal protection;
- upload non-execution;
- parsing failure without original overwrite.

Model access retains:

```text
requested_data_access_level
max_allowed_data_access_level
effective_data_access_level
```

The Competition Edition requirement is now minimal necessary content, no
Secrets, no default full sensitive dataset transfer, visible data scope and
visible failure/degradation. Enterprise DLP and full automated classification
were moved to future production.

Agent operations now use:

```text
AUTO_ALLOWED
LIGHT_CONFIRMATION
FORMAL_APPROVAL
PROHIBITED
```

Read-only and candidate/preview workflows may run continuously. Formal approval
remains for irreversible operations, research-data modification, formal plan
execution, high-risk manuscript changes, result invalidation and sensitive/raw
exports. Agent self-approval, arbitrary code, Service bypass, original overwrite
and model-generated formal numbers remain prohibited.

## 3. Rules Downgraded to Competition Recommended

- fine-grained RBAC beyond the simple project role model;
- basic login/expensive-endpoint rate limiting for exposed deployments;
- antivirus scanning and advanced content sanitization;
- a full file quarantine/audit platform;
- signed URLs when authorized backend streaming is sufficient;
- automated SBOM and automated license scanning;
- automatic blocking of Medium/Low vulnerabilities;
- full model-data classification and automated masking;
- container non-root/read-only/resource hardening beyond practical defaults;
- formal backup drills and extended log retention;
- local database export and MinIO demo copies.

These controls remain useful and may be elevated when the deployment profile
changes, but they do not block school-competition delivery by default.

## 4. Rules Moved to Future Production

- enterprise SSO, organization hierarchy, complex RBAC and access review;
- large-scale multi-tenant administration;
- formal privacy-law, legal deletion and data-retention workflows;
- enterprise Secret Manager and automatic key rotation;
- DLP, SIEM, centralized monitoring and staffed incident response;
- formal vulnerability remediation SLA and enterprise supply-chain governance;
- RPO/RTO, off-site backup, multi-region recovery and automatic failover;
- advanced ingress/network policy, WAF and host/container hardening;
- long-term security archives, legal notification and regulatory reporting;
- multi-region data residency and compliance evidence.

The documents explicitly require re-evaluation if RECA becomes public,
commercial, large-scale or handles high-risk real data.

## 5. Hard Safeguards Retained

- real Secrets do not enter source, frontend bundles, exports or ordinary logs;
- original PDF/data/DOCX and formal source versions are immutable;
- formal statistics come from deterministic programs;
- literature, EvidenceSpan, citations and formal status cannot be fabricated;
- uploaded files do not execute and cannot escape storage/temporary roots;
- existing authentication and backend authorization are preserved;
- multi-user deployments cannot cross project boundaries;
- Agent tools remain allowlisted and Service-mediated;
- Agent cannot self-approve or execute arbitrary Shell, SQL or Python;
- high-risk research changes retain version-bound formal approval;
- failures and degradation cannot be reported as formal success;
- no-license or unknown-source content cannot be copied;
- attribution, license, upstream Commit and modification history are retained;
- demo data cannot expose unauthorized sensitive/restricted material;
- actual-path Critical supply-chain risk blocks delivery;
- six M0 required CI jobs and infrastructure clean-room acceptance remain mandatory.

## 6. Open-Source Reuse Modes

The authoritative governance policy now defines:

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

`CLEAN_ROOM_REIMPLEMENTATION` is an optional mode rather than the default.

The minimum incorporation record includes project/repository, fixed Commit or
Tag, actual license and path, integration mode, copied and modified paths,
modification summary, attribution location, special restrictions,
commercialization review flag, reviewer and review date.

License classifications are:

```text
PERMISSIVE_REUSE_ALLOWED
COPYLEFT_REVIEW_REQUIRED
NONCOMMERCIAL_RESTRICTION
NO_DERIVATIVES_RESTRICTION
CUSTOM_LICENSE_REVIEW
NO_LICENSE_DO_NOT_COPY
UNKNOWN_SOURCE_DO_NOT_COPY
```

Permissive and Copyleft content is not blanket-prohibited. The selected mode
must satisfy the exact license obligations and preserve path-level provenance.
No-license content may be studied but not copied/Vendored/distributed without
authorization; unknown-source content cannot enter the formal repository.

No Vendor directory, Fork, Submodule, dependency or copied third-party content
was added in this phase.

## 7. Adapter Policy

The old near-absolute Adapter posture was replaced with a conditional rule.

Adapter is required for unstable/replaceable external APIs, multiple
implementations, domain-object isolation, offline Mock/Recorded alternatives,
license/security boundaries or clear testing/degradation benefits.

Direct integration is allowed for mature, stable, small-interface libraries
with no replacement need, no domain-model pollution and lower maintenance cost.

Both modes remain subject to Service authorization, project isolation,
scientific truthfulness, immutable versions, Schema, approval and audit.

## 8. ARS-Codex Decision

ADR-001 was amended rather than deleting its history. The old research-only,
mandatory-clean-room decision is retained in the change record and replaced by
licensed effect-first reuse.

Current purpose status:

```text
NONCOMMERCIAL_INTENT_DECLARED
```

It is not `LEGALLY_CONFIRMED_NONCOMMERCIAL`.

After exact license/path review, RECA may selectively copy Prompts, workflow
templates, scripts, test structures and test materials; Vendor or Fork the
project; keep it as a development resource; or consider runtime use through a
separate architecture ADR.

Reuse does not automatically:

- change the single-orchestrator architecture;
- move Agent runtime before M8;
- permit free multi-Agent state;
- move business truth to Agent sessions;
- replace deterministic statistics, evidence or parsing;
- bypass Project, Approval, Evidence or Tool contracts.

Current actual incorporation remains `RESEARCH_REFERENCE`; copied content,
Vendor, Fork, Submodule and runtime dependency are all absent.

## 9. Unresolved License Questions

The following remain unresolved and require exact-use review or legal advice:

1. Whether the specific school competition, prize, sponsorship and distribution
   qualify as NonCommercial under CC BY-NC 4.0.
2. Whether public repository, download, portfolio or hosted use changes that
   analysis.
3. Whether every relevant ARS-Codex file and tracked/vendored asset uses the
   same license.
4. Which attribution/change-notice form applies to each copied path and reuse
   mode.
5. How future commercial/public product use would replace, isolate, relicense
   or remove CC BY-NC content.
6. Which root license RECA will adopt.
7. Whether competition datasets, PDFs, visual assets and fixtures allow public
   redistribution.

## 10. Deferred Phase 3 Alignment

Phase 3 must align README/AGENTS, architecture/development Adapter prose,
ApprovalRecord/data/API/Tool contracts, testing gates and roadmap milestones.
This Phase 2 intentionally did not change those documents.

During the temporary transition, the security entry and four security child
documents are authoritative for security-policy classification. Existing code,
Schema, API and test behavior is not implicitly changed.

Repository-wide restriction scanning found two active entry summaries outside
the Phase 2 modification scope:

- `README.md` still describes ARS-Codex as research-only and not a runtime
  dependency;
- `AGENTS.md` still describes ARS-Codex as a clean-room research reference and
  not a runtime dependency.

Historical migration/baseline reports also retain the prior decision, which is
correct as historical evidence. The active README/AGENTS summaries must be
updated in Phase 3 before the repository-wide old-policy scan can pass without
qualification. This is the reason for `CONDITIONAL PASS`; it does not invalidate
the new authoritative security policy or ADR.

## 11. Validation and Scope Confirmation

- Documentation status: `Conditional Approval`.
- Root license: `PENDING_GOVERNANCE_DECISION`.
- M0 required CI removed or weakened: no.
- Infrastructure clean-room acceptance removed or weakened: no.
- Existing authentication removed: no.
- Project isolation removed: no.
- Model formal statistics allowed: no.
- Agent arbitrary code execution allowed: no.
- Third-party content copied: no.
- Dependency or lock file changed: no.
- Vendor/Submodule created: no.
- Backend/frontend/Compose/CI/migration changed: no.
- Phase 3 executed: no.
