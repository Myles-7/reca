# RECA Security and Reuse Optimization Baseline

Document status: `Conditional Approval`

Phase: Security and Open-Source Governance Optimization, Phase 1

Assessment date: 2026-07-31

Root license status: `PENDING_GOVERNANCE_DECISION`

Policy application status: `DESIGN_ONLY_NOT_APPLIED`

## 1. Scope

This report inventories the security, approval, integration, supply-chain, and
open-source reuse rules that exist in the current modular documentation set. It
identifies conflicts with the project owner's personal-development and school-
competition direction and proposes a policy framework for later implementation.

This phase does not modify a formal policy, ADR, source-research record, test
gate, product contract, code, dependency, Compose file, CI workflow, or
migration. It does not copy any third-party content.

The inventory was produced from the repository at commit
`9ae136c0170f395c3f0b5ca9232f84684951b86e` on branch
`docs/document-split-compression`. The review covered the nine entry documents,
the four `docs/security/` specifications, relevant architecture, development,
testing and roadmap specifications, `docs/source-research/`, `docs/decisions/`,
the latest documentation split and consistency reports, and
`THIRD_PARTY_NOTICES.md`.

Rules below are consolidated by unique policy meaning. Repeated summaries and
test restatements are cited as additional sources rather than counted as new
rules. The five allowed recommendation levels are:

- `COMPETITION_BLOCKER`: violation invalidates research credibility, permits a
  direct compromise, or creates an unlicensed redistribution risk.
- `COMPETITION_REQUIRED`: must be implemented for the competition workflow, but
  may use a simple local design rather than an enterprise control system.
- `COMPETITION_RECOMMENDED`: valuable defense or quality improvement that does
  not block school-competition development or demonstration.
- `FUTURE_PRODUCTION`: retain as a future deployment requirement; remove it from
  competition completion and release gates.
- `REMOVE_DUPLICATE`: remove or replace a duplicated/obsolete restriction after
  establishing one authoritative policy location.

## 2. Current Security Rule Inventory

### A. Research truthfulness

| Current rule | Current file | Current level | Suggested level | Suggested action | Reason |
| --- | --- | --- | --- | --- | --- |
| Literature and citations must not be fabricated. | `docs/SECURITY_AND_OPEN_SOURCE.md` 5.1, `docs/security/FILE_MODEL_AND_AGENT_SECURITY.md` 56.2 | Release blocker | `COMPETITION_BLOCKER` | Retain as a single research-truthfulness rule and test it. | A fabricated source invalidates the product's central claim. |
| An `EvidenceSpan` must be grounded in located source text; absence or uncertain location must not be represented by a synthetic span. | `AGENTS.md` 8, `docs/testing/E2E_ACCEPTANCE_AND_RELEASE_GATES.md`, M3 roadmap | Release blocker | `COMPETITION_BLOCKER` | Retain explicit absence and `LOCATION_UNCERTAIN` semantics. | This is the evidence-chain trust boundary. |
| Formal statistical values must come from deterministic programs, not model prose. | `README.md`, `AGENTS.md` 7.4, `docs/SECURITY_AND_OPEN_SOURCE.md` 5.12 | Release blocker | `COMPETITION_BLOCKER` | Retain without weakening. | Model-generated numbers are not reproducible calculations. |
| Data must not be altered or selectively reported to obtain significance. | `docs/SECURITY_AND_OPEN_SOURCE.md` 5.12, security release gates | No-exception blocker | `COMPETITION_BLOCKER` | Retain and include in prohibited operations. | This is research misconduct, not an operational hardening choice. |
| Citation support, claim wording, data versions and formal results must remain traceable. | `docs/security/FILE_MODEL_AND_AGENT_SECURITY.md` 15, 56; E2E gates | Required | `COMPETITION_REQUIRED` | Keep a competition-sized evidence chain and visible source/version links. | Traceability is necessary for judging and reproducibility. |
| The system must distinguish AI suggestions from user decisions and deterministic results. | PRD principles, `AGENTS.md` 7.4, security entry document | Required | `COMPETITION_REQUIRED` | Keep labels and persisted decision/result types; deduplicate prose. | Prevents suggestions from being mistaken for verified output. |

### B. Original data and file protection

| Current rule | Current file | Current level | Suggested level | Suggested action | Reason |
| --- | --- | --- | --- | --- | --- |
| Original PDF, dataset and DOCX artifacts must never be overwritten. | `README.md`, `AGENTS.md` 7.2, `docs/security/FILE_MODEL_AND_AGENT_SECURITY.md` 15 | No-exception blocker | `COMPETITION_BLOCKER` | Retain; all changes create derived artifacts or versions. | Preserves evidence and enables recovery. |
| Original `DatasetVersion` and formal version objects are immutable. | `AGENTS.md` 7.2, data-model invariants, security entry document | No-exception blocker | `COMPETITION_BLOCKER` | Retain database/service enforcement. | Formal results must remain reproducible against the exact input. |
| Approval and audit history must be append-only rather than overwritten. | `AGENTS.md` 7.2, `docs/security/FILE_MODEL_AND_AGENT_SECURITY.md` 15.5 | Required | `COMPETITION_REQUIRED` | Retain a simple append-only record; defer enterprise archive controls. | Required to explain who confirmed a high-risk action. |
| Derived files must reference their source artifact/version and operation. | `docs/security/FILE_MODEL_AND_AGENT_SECURITY.md` 15.2-15.4 | Required | `COMPETITION_REQUIRED` | Retain source IDs, hashes and transformation relation. | Needed for lineage without enterprise data governance. |
| File hashes must be recorded and checked at trust-boundary transitions. | `docs/security/FILE_MODEL_AND_AGENT_SECURITY.md` 11.6, 15.6 | Required | `COMPETITION_REQUIRED` | Keep SHA-256 or equivalent for uploads and formal artifacts. | Low-cost integrity protection with high demo value. |
| Deletion must not silently erase evidence required by still-valid formal results. | operations deletion rules, data-model invalidation rules | Required | `COMPETITION_REQUIRED` | Use dependency checks and explicit invalidation; simplify retention scheduling. | Prevents broken evidence chains while avoiding full lifecycle bureaucracy. |

### C. Secrets and basic privacy

| Current rule | Current file | Current level | Suggested level | Suggested action | Reason |
| --- | --- | --- | --- | --- | --- |
| Secrets must not enter source control, frontend bundles, exports or ordinary logs. | `README.md`, `AGENTS.md` 7.6, security release gates | Release blocker | `COMPETITION_BLOCKER` | Retain secret scanning and server-side configuration. | A leaked credential is an immediate compromise. |
| Real credentials must not be placed in `.env.example`, fixtures or screenshots. | `README.md`, operations demo rules, open-source release checklist | Release blocker | `COMPETITION_BLOCKER` | Retain placeholders and demo-screen checks. | School demos commonly expose terminals and configuration. |
| Sensitive real data must not be used in demos without permission and minimization. | `docs/security/OPERATIONS_DATA_AND_INCIDENTS.md` 54, security entry release blockers | Release blocker | `COMPETITION_BLOCKER` | Use synthetic, public, or explicitly permitted data. | Prevents avoidable privacy and redistribution harm. |
| Model calls should send only the minimum fields needed and disclose external transfer. | `docs/security/FILE_MODEL_AND_AGENT_SECURITY.md` 18 | Required | `COMPETITION_REQUIRED` | Keep a simple requested/max/effective access decision and user-visible disclosure. | Necessary privacy boundary even for a local competition tool. |
| Complete automated data classification and field-level masking are required before all model calls. | file/model security 17-18 | P0 broad control | `COMPETITION_RECOMMENDED` | Use explicit high-risk exclusions now; automate classification later. | Full classification is costly and not needed for approved demo data. |
| Enterprise Secret Manager, scheduled rotation and centralized key custody are required. | operations priority list, security controls secret sections | Future enhancement mixed into policy | `FUTURE_PRODUCTION` | Replace competition gate with environment-variable/local secret hygiene. | Personal and school use does not justify enterprise key infrastructure. |

### D. File and parser security

| Current rule | Current file | Current level | Suggested level | Suggested action | Reason |
| --- | --- | --- | --- | --- | --- |
| Uploaded files are untrusted input and must never be executed. | `docs/security/FILE_MODEL_AND_AGENT_SECURITY.md` 11-14, 21 | No-exception blocker | `COMPETITION_BLOCKER` | Retain across PDF, DOCX, ZIP, CSV and XLSX handling. | Directly prevents code execution from user material. |
| Normalized file names and resolved paths must remain inside the assigned storage root. | file/model security 11.4-11.5, security tests 27.2 | Release blocker | `COMPETITION_BLOCKER` | Retain path traversal and ZIP Slip rejection tests. | Prevents arbitrary host-path reads and writes. |
| Archive extraction must reject traversal, excessive expansion and unsafe external relations. | file/model security 13 | Release blocker | `COMPETITION_BLOCKER` | Retain bounded extraction and relationship filtering. | Malicious office files are realistic inputs. |
| Claimed extension, MIME type and parser signature must be checked before parsing. | file/model security 11.1-11.3 | Required | `COMPETITION_REQUIRED` | Keep lightweight multilayer validation. | Cheap protection against accidental or malicious type confusion. |
| PDF JavaScript, office macros, spreadsheet formulas and external links must not execute. | file/model security 12.4, 13.4-13.5, 14.2-14.4 | Required | `COMPETITION_REQUIRED` | Parse as data and neutralize active content in exports/previews. | Maintains the non-execution rule for supported formats. |
| Every upload must pass an antivirus engine before use. | file/model security 11.8, operations P0 priorities | Recommended/future mixed | `COMPETITION_RECOMMENDED` | Do not block local competition use; preserve an extension point and warning. | Antivirus integration adds operations cost beyond the minimum parser sandbox. |
| Downloads must always use signed URLs and advanced content-disposition policy. | file/model security 11.9, 31.6; operations priorities | Core strengthening | `COMPETITION_RECOMMENDED` | Permit authenticated backend streaming for competition scope. | Signed URLs are useful but not essential for a small local deployment. |

### E. User permissions and project isolation

| Current rule | Current file | Current level | Suggested level | Suggested action | Reason |
| --- | --- | --- | --- | --- | --- |
| A user must not access another project's records or object-storage paths. | `AGENTS.md`, `docs/security/SECURITY_CONTROLS.md`, security tests | Release blocker | `COMPETITION_BLOCKER` | Retain ownership/project checks in every service query. | Basic isolation prevents direct data disclosure. |
| Authorization must be enforced by the backend, never only by hidden UI controls. | security controls authorization sections, architecture service rules | Required | `COMPETITION_REQUIRED` | Retain service-level checks. | UI state is not a security boundary. |
| A minimal owner/member role and project-scoped membership model is required. | PRD, foundation models, security controls | Required | `COMPETITION_REQUIRED` | Keep a small role set; avoid enterprise policy engines. | Supports demo collaboration and project isolation. |
| Fine-grained enterprise RBAC, administrative delegation and periodic access reviews are required. | security controls identity/authorization sections | P0/production mixed | `FUTURE_PRODUCTION` | Move beyond simple owner/member roles to future production. | Excessive for personal and school-competition use. |
| Strong multi-tenant isolation and tenant administration are release requirements. | security controls and architecture deployment assumptions | Production-oriented | `FUTURE_PRODUCTION` | Retain only project ownership isolation now. | RECA is not currently a large multi-tenant SaaS. |

### F. Agent and model boundaries

| Current rule | Current file | Current level | Suggested level | Suggested action | Reason |
| --- | --- | --- | --- | --- | --- |
| Agent tools must be allowlisted and must call Services rather than write the database directly. | `AGENTS.md` 7.4-7.5, agent tool contracts, security 20 | No-exception blocker | `COMPETITION_BLOCKER` | Retain. | Keeps authorization, validation and audit enforceable. |
| The Agent must not execute arbitrary Shell, Python or SQL. | `AGENTS.md`, file/model security 20-21, M8 tests | No-exception blocker | `COMPETITION_BLOCKER` | Retain explicit rejection and absence-of-ToolCall tests. | Arbitrary execution collapses all other boundaries. |
| The Agent cannot approve its own action or treat chat assent as formal approval. | `AGENTS.md` 7.3, security 20.4 | No-exception blocker | `COMPETITION_BLOCKER` | Retain for formal approvals; introduce light confirmation for low-risk choices. | Separation of proposal and high-risk authorization is essential. |
| Prompt injection in PDF/DOCX/data must remain content and cannot grant tools or override policy. | file/model security 19, security contract tests | Release blocker | `COMPETITION_BLOCKER` | Retain content/instruction separation and tool-policy checks. | Research documents are a direct untrusted prompt source. |
| Model output must pass a strict schema before it can affect persisted business state. | API/AI contracts, file/model security 19.6 | Required | `COMPETITION_REQUIRED` | Retain schema validation and controlled retry/no-write failure. | Prevents malformed model output from becoming business truth. |
| Requested, maximum and effective model data-access levels must be separately recorded. | data-model invariants, AI contracts, file/model security 18 | Required | `COMPETITION_REQUIRED` | Keep the three-level semantics with a compact implementation. | Prevents callers or models from expanding access. |
| External cross-model review requires separate provider, consent, data-category and audit decisions. | open-source governance 46.5, ADR-001 | Required | `COMPETITION_REQUIRED` | Keep disabled by default; allow explicit one-time enablement. | Content transfer is a separate privacy decision. |
| Comprehensive token, loop, time and per-tool quotas must be production-grade before Agent use. | file/model security 20.5-20.6 | Required controls | `COMPETITION_RECOMMENDED` | Keep simple hard caps and cancellation; defer advanced policy tuning. | Basic stability matters, but enterprise quota management does not. |

### G. Runtime and container security

| Current rule | Current file | Current level | Suggested level | Suggested action | Reason |
| --- | --- | --- | --- | --- | --- |
| Internal databases, queues, object storage and parser management ports should not be publicly exposed. | `README.md`, security controls network sections | Required | `COMPETITION_REQUIRED` | Keep private Compose networking and minimal published ports. | Low-cost protection that also improves demo stability. |
| Services should run as non-root where practical. | operations priority list, security controls containers | Core strengthening | `COMPETITION_RECOMMENDED` | Apply to maintained images when easy; do not block all competition work. | Useful defense, but some third-party images may constrain it. |
| Login and expensive endpoints require production-grade rate limiting. | security controls, operations priority list | Core strengthening | `COMPETITION_RECOMMENDED` | Add simple limits if internet-exposed; otherwise document local scope. | Local/school demos have a small traffic surface. |
| Read-only filesystems, dropped capabilities and advanced container hardening are mandatory. | security controls container sections | Production-oriented | `FUTURE_PRODUCTION` | Move to production deployment profile. | Adds compatibility and maintenance cost beyond the current threat model. |
| Advanced network policy, ingress protection and traffic filtering are mandatory. | security controls network/deployment sections | Production-oriented | `FUTURE_PRODUCTION` | Defer until a public deployment architecture exists. | No current large-scale public deployment target. |

### H. Backup and incident response

| Current rule | Current file | Current level | Suggested level | Suggested action | Reason |
| --- | --- | --- | --- | --- | --- |
| Failures, cache use, fallbacks and degraded evidence location must be visible and must not be reported as formal success. | security entry, open-source governance 46.5, roadmap risk rules | Release blocker | `COMPETITION_BLOCKER` | Retain user-visible degradation records or equivalent audit events. | A hidden fallback undermines research trust. |
| A local export/recovery path should exist for competition projects and formal artifacts. | operations backup sections, export roadmap | Required | `COMPETITION_REQUIRED` | Keep simple reproducibility export and documented local restore steps. | Protects the demo and supports reproducibility without enterprise backup systems. |
| Basic incident notes should record a secret leak, cross-project access or corrupted formal result. | operations 32-33, appendix D | Required | `COMPETITION_RECOMMENDED` | Keep a lightweight issue/report template, not an organization-wide process. | Useful for recovery, but need not block feature development. |
| Formal data retention schedules, legal deletion workflows and backup deletion propagation are required. | operations 29-30 | P0/production mixed | `FUTURE_PRODUCTION` | Move to a production/privacy policy task. | Requires legal and operational decisions absent from current scope. |
| Off-site backup, disaster recovery, RPO/RTO and periodic recovery exercises are required. | operations 30, architecture operations | Production-oriented | `FUTURE_PRODUCTION` | Defer until hosting and availability commitments exist. | No enterprise availability objective has been declared. |
| A staffed incident-response organization, disclosure channel, severity SLA and formal evidence preservation process are required. | operations 33, 49, 58 | Production-oriented | `FUTURE_PRODUCTION` | Retain as a future template, remove from competition gates. | A personal/school project cannot honestly implement an enterprise response organization. |

### I. Supply-chain security

| Current rule | Current file | Current level | Suggested level | Suggested action | Reason |
| --- | --- | --- | --- | --- | --- |
| Dependencies and images must come from identifiable sources and be version-locked for reproducible builds. | open-source governance 35.1-35.2, M0 regression | Required | `COMPETITION_REQUIRED` | Retain lock files and pinned service versions. | Supports stable demos and traceable license review. |
| Install scripts and newly introduced executable build hooks require review. | open-source governance 35.4-35.5 | Required | `COMPETITION_REQUIRED` | Retain focused review for scripts that execute during install/build. | Direct supply-chain execution is high impact. |
| Known actively exploitable Critical/High vulnerabilities in shipped components block release. | open-source governance 35.7, operations 59.6 | Release blocker | `COMPETITION_BLOCKER` | Retain a scoped blocker with an explicit documented exception only when not reachable. | Avoids knowingly shipping a direct compromise path. |
| Dependency scanning and secret scanning remain part of the M0 required CI baseline. | M0 regression baseline, development test rules | Required CI | `COMPETITION_BLOCKER` | Do not weaken the six required CI jobs in this policy task. | The user explicitly preserved the completed M0 baseline. |
| Medium/Low vulnerability remediation must meet formal SLAs and automatically block builds. | open-source governance 35.7, operations defect levels | Production-oriented | `FUTURE_PRODUCTION` | Report for competition; define SLA only for production. | Blanket blocking slows development without proportional school-demo benefit. |
| A fully automated SBOM for packages, images and Vendor content is mandatory for every competition release. | open-source governance 36, operations 59.6 | Release gate | `COMPETITION_RECOMMENDED` | Keep a complete dependency/notices list; automate SBOM later. | Traceability is required, but automation is not the only reliable mechanism. |

### J. Open source and licensing

| Current rule | Current file | Current level | Suggested level | Suggested action | Reason |
| --- | --- | --- | --- | --- | --- |
| No-license or unknown-source code, Prompt, script, test, data or media must not be copied or redistributed. | open-source governance 39.5, 51; security entry blockers | Release blocker | `COMPETITION_BLOCKER` | Retain without weakening. | Public visibility is not permission to copy. |
| Before copying or distributing third-party content, verify the license from the pinned version's authoritative text. | open-source governance 35, 39, 50 | Release blocker | `COMPETITION_BLOCKER` | Retain version-specific verification. | Repository-level memory or labels may be wrong or outdated. |
| Attribution, license text, upstream repository/commit and modification records must accompany incorporated content. | open-source governance 40-43, `THIRD_PARTY_NOTICES.md` | Release blocker | `COMPETITION_BLOCKER` | Retain, with a lightweight incorporation ledger. | These are core compliance and honesty obligations. |
| RECA must not claim third-party work is wholly original or covered solely by the future root license. | open-source governance 38.3, 42-43 | Release blocker | `COMPETITION_BLOCKER` | Add explicit provenance in notices and copied files. | Prevents misleading attribution and license scope. |
| Root license remains `PENDING_GOVERNANCE_DECISION`; no document may select one implicitly. | security entry, open-source governance 38, README/AGENTS | Governance blocker | `COMPETITION_REQUIRED` | Retain until the project owner makes a separate decision. | This task does not authorize a root-license choice. |
| Package, independent service, Fork, Vendor, Submodule and selective copy each require a recorded reuse mode. | open-source governance 40-43, target policy direction | Partly defined | `COMPETITION_REQUIRED` | Normalize the eight reuse modes and their minimum records. | Enables effect-first reuse without losing provenance. |
| Dataset, PDF, model and code licenses must be evaluated separately. | open-source governance 37, 44-46 | Required | `COMPETITION_REQUIRED` | Retain separate rights fields and redistribution decisions. | A code license does not grant rights to data or documents. |
| Comprehensive enterprise license scanning, counsel workflow and organization-wide exception management are required. | open-source governance 50-51, operations exceptions | Production-oriented | `FUTURE_PRODUCTION` | Keep manual verification for competition; defer enterprise workflow. | Formal legal operations exceed the declared project scope. |

### K. ARS-Codex special rules

| Current rule | Current file | Current level | Suggested level | Suggested action | Reason |
| --- | --- | --- | --- | --- | --- |
| RECA keeps database-owned state, immutable artifacts, Services, approvals and deterministic tools even when ARS patterns are reused. | ADR-001 Decision, source record section 2 | Architectural blocker | `COMPETITION_BLOCKER` | Retain as a non-negotiable integration boundary. | Reuse must not replace RECA's research-trust architecture. |
| RECA retains one controlled orchestrator rather than independently stateful free multi-Agent product actors. | ADR-001 Decision, timing; AGENTS | Architectural blocker | `COMPETITION_BLOCKER` | Retain. | Prevents state conflicts and approval bypass; not a license restriction. |
| ARS-Codex content cannot replace deterministic statistics, figures, hashes, parsing or version checks. | ADR-001 Decision | Architectural blocker | `COMPETITION_BLOCKER` | Retain. | This is a research-integrity boundary independent of reuse mode. |
| Cross-provider model transfer remains separately consented and audited. | ADR-001 Decision, open-source governance 46.5 | Required | `COMPETITION_REQUIRED` | Retain. | Reuse permission does not authorize data transfer. |
| ARS-Codex must never be a runtime, build, package, container or deployment dependency. | ADR-001 Decision; README/AGENTS; source record | Absolute prohibition | `REMOVE_DUPLICATE` | Replace with case-by-case architecture and license review; runtime use may be allowed by a new ADR. | Conflicts with the owner's effect-first reuse decision. |
| ARS-Codex Prompt, schema, workflow, script and test material must not be copied. | ADR-001, source record 4.1, open-source governance 46.6 | Absolute prohibition | `REMOVE_DUPLICATE` | Replace with licensed selective-copy/Fork/Vendor rules and an incorporation ledger. | License compliance, not blanket prohibition, should govern reuse. |
| Clean-room independent reimplementation is mandatory for every adopted ARS-Codex idea. | ADR-001 risk controls, source metadata and 4.1 | Default requirement | `REMOVE_DUPLICATE` | Make clean-room one optional reuse mode, not the default. | Conflicts with the owner's explicit policy change and slows development. |

### 2.1 Inventory counts

The consolidated inventory contains **70** unique rule themes:

| Suggested level | Count |
| --- | ---: |
| `COMPETITION_BLOCKER` | 27 |
| `COMPETITION_REQUIRED` | 22 |
| `COMPETITION_RECOMMENDED` | 8 |
| `FUTURE_PRODUCTION` | 10 |
| `REMOVE_DUPLICATE` | 3 |
| **Total** | **70** |

These counts describe policy themes, not occurrences. The same rule may appear
in entry summaries, detailed specifications, tests, roadmaps and `AGENTS.md`.

## 3. Production-Level Over-Design Candidates

The following controls should remain documented for a future public or
commercial deployment, but should not block the current personal/school-
competition delivery:

| Production-oriented topic | Current locations | Target treatment |
| --- | --- | --- |
| Enterprise RBAC, delegated administration and access review | `docs/security/SECURITY_CONTROLS.md` identity/authorization sections | Keep minimal owner/member and project isolation now; move enterprise features to `FUTURE_PRODUCTION`. |
| Full privacy-law workflow and legal deletion requests | operations sections 16 and 29; privacy statements | Do not make legal claims; defer jurisdiction-specific workflows. |
| Formal data lifecycle and retention schedules | operations section 29 | Keep user-controlled project deletion and honest backup disclosure; defer formal schedules. |
| Staffed incident response, disclosure organization and severity workflow | operations sections 33, 49 and 58 | Use a lightweight incident note for competition; future production owns organization and SLA. |
| Vulnerability remediation SLA for all severities | open-source governance section 35.7 | Block known exploitable Critical/High; report other severities without automatic competition failure. |
| Automatic SBOM generation | open-source governance section 36; operations 59.6 | Keep locked dependencies and notices; automation is recommended. |
| Enterprise Secret Manager and scheduled rotation | security controls; operations section 61 | Keep secrets out of source/frontend/logs; defer centralized custody. |
| Off-site disaster recovery, RPO/RTO and formal restore exercises | operations section 30; architecture operations | Keep local reproducibility export; defer service commitments. |
| Read-only containers, capability dropping and advanced hardening | security controls container sections | Recommended when compatible; production profile owns strict enforcement. |
| Advanced network policies, ingress and traffic defense | security controls network sections | Keep private internal services; defer public-edge architecture. |
| SaaS multi-tenant isolation beyond project ownership | security controls and architecture | Keep project isolation; defer tenant administration. |
| DLP and comprehensive automated sensitive-data handling | operations section 61; file/model section 17 | Use approved demo data and explicit exclusions; defer enterprise DLP. |
| Long-term audit archive and evidence-retention organization | operations sections 32-33 | Keep append-only project audit records; defer formal archive operations. |
| Multi-region compliance and data residency | implied by privacy/deployment policy | Do not add until a deployment region and legal scope exist. |
| Advanced rate limiting, abuse detection and traffic protection | security controls; operations section 61 | Simple internet-facing limits are recommended; enterprise controls are future production. |

## 4. Approval Rule Inventory and Target Levels

The current data model defines these `ApprovalRecord` types:

```text
RESEARCH_QUESTION_CONFIRMATION
LITERATURE_DECISION_CONFIRMATION
LITERATURE_EXTRACTION_CONFIRMATION
CLEANING_PLAN_APPROVAL
VARIABLE_ROLE_CONFIRMATION
ANALYSIS_PLAN_APPROVAL
FIGURE_CONFIRMATION
MANUSCRIPT_FIX_APPROVAL
CLAIM_CONFIRMATION
EXPORT_CONFIRMATION
```

Current tool contracts already allow many read-only or candidate-producing
operations without approval, but product and security prose sometimes describes
all user choices as formal `ApprovalRecord` checkpoints. Phase 2 should preserve
formal approval for high-risk effects while defining a lower-cost confirmation
record for ordinary choices.

| Target class | Operations | Target record/behavior | Current-policy observation |
| --- | --- | --- | --- |
| `AUTO_ALLOWED` | Query, search, metadata verification, PDF/document parsing, candidate extraction, read-only EvidenceSpan retrieval, dataset profiling, quality scan, cleaning preview, assumption validation, recommendation generation, manuscript check, claim audit and evidence-graph query | Authorization, input schema and ordinary audit only; no ApprovalRecord | Generally aligned with `AGENT_TOOL_CONTRACTS.md`; clarify entry summaries that imply universal approval. |
| `LIGHT_CONFIRMATION` | Adopt a candidate research question; correct extracted literature fields; choose include/exclude; adopt a topic candidate; confirm variable roles/pairing; choose figure type; accept low-risk formatting repair; confirm non-destructive claim wording | Persist a version-bound confirmation event or lightweight decision record; one-step UI confirmation is sufficient | Several current `*_CONFIRMATION` types are modeled like formal approvals and should be distinguished without losing traceability. |
| `FORMAL_APPROVAL` | Create a formal cleaned dataset version; missing-value imputation; outlier deletion; variable recoding; execute an approved AnalysisPlan; invalidate a formal result; apply high-risk manuscript content changes; export raw/sensitive data | Version-bound `ApprovalRecord`, impact preview, approver identity, Service precondition, audit and stale-version rejection | Current CleaningPlan, AnalysisPlan, manuscript high-risk, invalidation and sensitive export rules should remain hard gates. |
| `PROHIBITED` | Model writes formal statistics; Agent self-approval; arbitrary Shell/Python/SQL; direct database writes bypassing Service; overwrite original files/data/results; alter data to obtain significance | Reject before execution, write a denied ToolCall/security event where applicable, never offer an approval bypass | Current policy is aligned and must not be weakened. |

Phase 2 must define whether `LIGHT_CONFIRMATION` reuses `ApprovalRecord` with a
new level field or uses a separate decision record. That is a data/API decision,
not assumed in this report. Existing stored types must not be renamed without a
migration and contract review.

## 5. Open-Source Reuse Restriction Conflicts

The following current restrictions conflict with the new project-owner
direction. They remain in force until the formal policy and ADR are changed.

| File and section | Current restriction | Conflict | Required later action |
| --- | --- | --- | --- |
| `README.md`, ARS-Codex reference boundary | ARS-Codex is not a runtime dependency and is clean-room research only. | New direction allows runtime use after license and architecture review. | Update summary only after a replacement ADR is accepted. |
| `AGENTS.md` 7.6 | ARS-Codex is only a clean-room reference. | Makes clean-room mandatory for Codex tasks. | Replace with reuse-mode and license-verification rules after formal policy changes. |
| `docs/SECURITY_AND_OPEN_SOURCE.md`, root license/ARS status | Upstream content must not be copied before a policy review and is described as research-only. | Blanket posture conflicts with licensed selective copy, Fork or Vendor use. | Keep review gate; remove categorical research-only conclusion. |
| `docs/security/OPEN_SOURCE_GOVERNANCE.md` 46.6 | No Prompt, code, script or test material is copied; future copying is exceptional. | New policy explicitly permits those forms when license conditions are met. | Replace with incorporation prerequisites and reuse modes. |
| `docs/decisions/ADR-001-ARS-CODEX-USAGE.md` Decision and Risk controls | No runtime/build/package/container dependency; no wholesale copying; clean-room wording and implementation. | This is the primary accepted decision that must be superseded, not edited silently. | Create a later ADR that supersedes ADR-001 and records the purpose declaration and constraints. |
| `docs/source-research/academic-research-skills-codex.md` metadata and 4.1 | `research-and-independent-reimplementation`, copied content `none`, Prompt copying prohibited. | No longer represents the target policy if content is incorporated. | Update the source ledger only when the reuse decision and exact copied files are known. Preserve historical review facts. |
| Architecture/development Adapter rules | Third-party behavior is generally expected to pass through an Adapter. | New direction permits direct integration for stable small-interface libraries. | Make Adapter conditional using the decision rule in section 6. |
| Testing and roadmap clean-room references | Similarity, clean-room and independent reimplementation are treated as default gates for ARS-derived work. | New policy makes clean-room optional. | Replace only the ARS-specific gate; preserve M0 infrastructure clean-room acceptance, which is unrelated. |
| Broad repository-copying cautions in open-source governance | Whole-repository import is treated as an exceptional high-risk path. | Fork/Vendor/Submodule are now valid first-class modes. | Retain license/security review and provenance, remove the presumption that selective reimplementation is always preferable. |

Important distinction: the repository contains two unrelated uses of
“clean-room.” The **M0 infrastructure clean-room acceptance** is a required CI
and environment-isolation test and must remain unchanged. Only **ARS-Codex
clean-room reimplementation** changes from mandatory to optional.

## 6. Adapter Rule Inventory and Proposed Decision Rule

Adapter is currently treated as a broad architectural default or near-absolute
boundary in:

- `docs/ARCHITECTURE.md`, section 5.4 and execution order summaries;
- `docs/architecture/DATA_FLOWS_AND_ADAPTERS.md`;
- `docs/architecture/SYSTEM_COMPONENTS_AND_MODULES.md`, section 11.6;
- `docs/API_AI_TOOL_CONTRACTS.md` and
  `docs/contracts/COMMON_API_JOB_AND_SSE_CONTRACTS.md`;
- `docs/development/BACKEND_DATA_AND_ASYNC_RULES.md`;
- `docs/security/SECURITY_CONTROLS.md` and
  `docs/security/OPEN_SOURCE_GOVERNANCE.md`;
- Adapter contract tests and multiple milestone implementation sequences.

The useful boundary is not “all third-party code requires an Adapter.” The
target rule should be:

### Adapter required

Use an Adapter when one or more of these conditions apply:

1. an external API is unstable, remote, quota-bound or likely to be replaced;
2. third-party response objects must not leak into the domain layer;
3. Mock, recorded, offline or local fallback implementations are required;
4. license isolation or a meaningful security boundary is required;
5. multiple implementations provide the same capability;
6. failure/degradation conversion must be normalized across providers.

### Direct integration allowed

Direct library integration is allowed when all relevant conditions hold:

1. the library is stable, mature and license-compatible for the declared use;
2. the interface surface is small;
3. library-specific objects do not become persisted domain contracts;
4. there is no realistic replacement or offline-provider requirement;
5. direct use materially reduces development cost;
6. direct use has lower testing and maintenance cost than a wrapper;
7. authorization, validation and high-risk approval still remain in Services.

An Adapter decision should be recorded in the dependency/source review or ADR;
it should not require an ADR for every small stable utility library. Direct
integration never authorizes a library to bypass Service, project isolation,
immutability, approval, schema or audit boundaries.

## 7. ARS-Codex Current State and Target Strategy

### 7.1 Current prohibitions

The accepted ADR and source record currently prohibit or constrain:

1. runtime, build, package, container and deployment dependency use;
2. direct or wholesale copying of Prompts, schemas, scripts and test corpora;
3. Vendor or Fork incorporation as a product component;
4. independently stateful multi-role Agents;
5. Agent-session or Material-Passport ownership of business truth;
6. model replacement of deterministic computation and parsing;
7. external cross-model transfer without separate consent/data decisions;
8. distinctive wording reuse rather than clean-room independent authorship;
9. adding a notice for idea-level research where no content is incorporated.

Items 4-7 remain valid RECA architecture/security controls. Items 1-3 and 8
are the restrictions that the target reuse policy changes. Item 9 remains a
correct distinction: notices should describe actual incorporation or
distribution, not mere reading.

### 7.2 Target permitted uses

After a replacement ADR and license review, RECA may permit:

- selective copying of Prompts;
- copying workflow templates;
- copying scripts;
- copying test structures and test materials;
- vendoring the whole project;
- Forking and modifying the project;
- keeping it as a development-time reference asset;
- using it as a runtime component after an explicit architecture decision.

### 7.3 Mandatory prerequisites

Before any direct ARS-Codex incorporation:

1. record purpose status as `NONCOMMERCIAL_INTENT_DECLARED`;
2. verify the exact upstream CC BY-NC 4.0 license text and pinned commit;
3. preserve the CC BY-NC 4.0 notice and required attribution;
4. record the upstream repository, commit and incorporated file list;
5. record modifications to copied files or the Fork;
6. keep differently licensed content identifiable and separable;
7. do not state that the future RECA root license covers upstream content;
8. update `THIRD_PARTY_NOTICES.md` and distribute required license material
   when copyrightable content is actually incorporated or distributed;
9. re-review if commercialization, sponsorship, public productization,
   distribution or intended use changes;
10. retain RECA's database state, single orchestrator, deterministic tools,
    Service authorization, approval and evidence-chain boundaries.

`NONCOMMERCIAL_INTENT_DECLARED` records the project owner's intended use. This
report does **not** conclude that a school competition is legally non-commercial
under CC BY-NC 4.0, and it does not use or imply
`LEGALLY_CONFIRMED_NONCOMMERCIAL`.

## 8. Proposed Policy Framework

This section is a Phase 1 design. It is not yet authoritative policy.

### Policy A: Competition Minimum Safeguards

1. Secrets must not enter source code, frontend bundles or ordinary logs.
2. Original PDF, data and DOCX files must not be overwritten.
3. Formal statistical values must come only from deterministic programs.
4. Literature, `EvidenceSpan` and citations must not be fabricated.
5. Uploaded files must not execute.
6. Paths and file names must not affect arbitrary host paths.
7. High-risk data operations require confirmation.
8. An Agent cannot self-approve or execute arbitrary code.
9. Failure or degradation must not be disguised as formal success.
10. A third-party license must be confirmed before content is copied.
11. Attribution, upstream commit and modification records must be preserved.
12. No-license or unknown-source material must not be copied.
13. Third-party contributions must not be described as wholly original.
14. Demo data must not contain unlicensed real sensitive data.

### Policy B: Competition Recommended

The following do not block school-competition development: fine-grained RBAC,
login rate limiting, antivirus scanning, signed URLs, automatic SBOM, automatic
blocking of medium/low vulnerabilities, comprehensive model-data
classification, read-only containers, advanced network policy, formal backup
exercises and a complete deletion workflow.

### Policy C: Future Production

Enterprise authorization, regulatory compliance, formal retention, staffed
incident response, disaster recovery, DLP, advanced key management,
comprehensive vulnerability governance, enterprise supply-chain governance and
formal security monitoring belong to a future production profile.

### Policy D: Effect-First Open-Source Reuse

Permitted reuse modes are:

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

`CLEAN_ROOM_REIMPLEMENTATION` is an optional risk-management mode, not the
default. The selected mode does not remove license verification, attribution,
commit pinning, modification tracking, security review or RECA's domain and
research-integrity boundaries.

## 9. Files Affected in Later Phases

### 9.1 Phase 2: formal policy and decision alignment

Phase 2 should modify the authoritative policy, repository rules and accepted
decision documents, at minimum:

```text
docs/SECURITY_AND_OPEN_SOURCE.md
docs/security/SECURITY_CONTROLS.md
docs/security/FILE_MODEL_AND_AGENT_SECURITY.md
docs/security/OPERATIONS_DATA_AND_INCIDENTS.md
docs/security/OPEN_SOURCE_GOVERNANCE.md
README.md
AGENTS.md
docs/decisions/ADR-001-ARS-CODEX-USAGE.md (supersede, do not erase history)
docs/source-research/academic-research-skills-codex.md
docs/ARCHITECTURE.md
docs/architecture/DATA_FLOWS_AND_ADAPTERS.md
docs/architecture/OPERATIONS_DEPLOYMENT_AND_ADRS.md
docs/development/BACKEND_DATA_AND_ASYNC_RULES.md
docs/TEST_AND_ACCEPTANCE.md
docs/IMPLEMENTATION_ROADMAP.md
docs/roadmap/RISK_SCOPE_AND_RELEASE.md
```

The accepted ADR should preferably be superseded by a new ADR rather than
rewritten as though the earlier decision never existed. Source-research facts
should preserve their historical review date and distinguish old copied-content
status from a later incorporation decision.

### 9.2 Phase 3: contract, approval, test and milestone alignment

After policy decisions are authoritative, align detailed requirements,
contracts, tests and milestone gates in:

```text
docs/product/PROJECT_AND_RESEARCH_REQUIREMENTS.md
docs/product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md
docs/product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md
docs/product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md
docs/data-model/FOUNDATION_AND_PROJECT_MODELS.md
docs/data-model/STATE_MACHINES_AND_INVARIANTS.md
docs/API_AI_TOOL_CONTRACTS.md
docs/contracts/PROJECT_RESEARCH_AND_LITERATURE_API.md
docs/contracts/DATA_ANALYSIS_AND_FIGURE_API.md
docs/contracts/MANUSCRIPT_EVIDENCE_AND_EXPORT_API.md
docs/contracts/AGENT_TOOL_CONTRACTS.md
docs/testing/CONTRACT_INTEGRATION_AND_SECURITY_TESTS.md
docs/testing/E2E_ACCEPTANCE_AND_RELEASE_GATES.md
docs/testing/M0_REGRESSION_BASELINE.md
docs/roadmap/milestones/M1_FOUNDATION.md
docs/roadmap/milestones/M2_RESEARCH_AND_LITERATURE.md
docs/roadmap/milestones/M4_DATA_QUALITY.md
docs/roadmap/milestones/M5_ANALYSIS_AND_FIGURES.md
docs/roadmap/milestones/M6_MANUSCRIPT_AND_CLAIMS.md
docs/roadmap/milestones/M8_AGENT.md
docs/roadmap/milestones/M9_DEMO_AND_RELEASE.md
```

`THIRD_PARTY_NOTICES.md` belongs in Phase 3 only if content is actually copied,
vendored, forked, distributed, or added as a runtime dependency. A policy change
alone must not add a notice claiming incorporation that has not happened.

## 10. Unresolved Legal and Licensing Questions

The following questions require project-owner input, exact license review or
legal advice. This report does not resolve them:

1. Whether the specific school competition, prizes, sponsorship, publication,
   hosting and distribution plan qualifies as NonCommercial under CC BY-NC 4.0.
2. Whether public repository distribution, a downloadable demo, judging access
   or later portfolio use changes the CC BY-NC analysis.
3. Whether all files in the pinned ARS-Codex repository are covered by the same
   license or contain separately licensed vendored material, datasets, fixtures
   or upstream subprojects.
4. Which attribution form, license copy, change notice and linking mechanism is
   required for each selected reuse mode.
5. Whether a Fork, Vendor copy or runtime component can remain sufficiently
   separated from code later covered by the RECA root license.
6. Whether future commercial, sponsored or public-product use requires removal,
   relicensing or replacement of incorporated CC BY-NC 4.0 material.
7. Which root license RECA will eventually adopt. It remains
   `PENDING_GOVERNANCE_DECISION`.
8. Whether competition-provided datasets, PDFs, logos, screenshots and model
   outputs permit redistribution in source archives and reproducibility packs.

Until these are resolved, the policy may authorize a reuse mode in principle,
but actual copying still requires the exact-source license check and
incorporation record.

## 11. Phase Boundary and Validation Contract

- Formal policy modified: **no**.
- Documentation approval status changed: **no**; it remains
  `Conditional Approval`.
- Root license selected: **no**; it remains
  `PENDING_GOVERNANCE_DECISION`.
- Third-party Prompt, code, script, test or fixture copied: **no**.
- Dependency, Vendor, Submodule or runtime component added: **no**.
- M0 infrastructure clean-room gate changed: **no**.
- Phase 2 executed: **no**.

The only permitted repository change for this phase is this report.
