# RECA M3 Issue Register

本文件是 M3 实施问题与阶段证据台账，不替代产品、数据模型、API、AI Schema、
测试或里程碑权威文档。

## Baseline

```text
Stage: M3-0
Date: 2026-08-03 (Asia/Shanghai)
Branch: feat/m2-research-literature
HEAD: 0e3c39dde65feaa8f784fd5fcfb1055cb557bb3c
Remote relation: ahead of origin by 8 commits
Migration head: 0012_document_upload
Tracked diff at entry: none
Protected untracked files: .playwright-cli/**, frontend/.tanstack/**
M2 Exit Gate: PASS
M3 Entry: ALLOWED
```

迁移 head 由 `backend/app/alembic/versions/*.py` 的 revision/down_revision 图确认；
本机缺少可用的 Python 3.14 仓库虚拟环境且 Docker daemon 未运行，见
`M3-ISSUE-0005`。

## Status Summary

| ID | Stage | Severity | Status | Area | Blocks current stage | Blocks M3 Exit |
| --- | --- | --- | --- | --- | --- | --- |
| M3-ISSUE-0001 | M3-0 | MEDIUM | RESOLVED | API contract | NO | NO |
| M3-ISSUE-0002 | M3-0 | MEDIUM | RESOLVED | state machine | NO | NO |
| M3-ISSUE-0003 | M3-0 | HIGH | RESOLVED | persistence/history | NO | NO |
| M3-ISSUE-0004 | M3-0 | MEDIUM | RESOLVED | enum contract | NO | NO |
| M3-ISSUE-0005 | M3-0 | LOW | RESOLVED | local verification environment | NO | NO |
| M3-ISSUE-0006 | M3-0 | LOW | RESOLVED | source-research/UI registry freshness | NO | NO |
| M3-ISSUE-0007 | M3-0 | MEDIUM | RESOLVED | decision API path | NO | NO |
| M3-ISSUE-0008 | M3-0 | MEDIUM | RESOLVED | EvidenceSpan read API | NO | NO |
| M3-ISSUE-0009 | M3-1 | MEDIUM | RESOLVED | migration identifiers | NO | NO |
| M3-ISSUE-0010 | M3-2 | MEDIUM | RESOLVED | AI schema boundary | NO | NO |
| M3-ISSUE-0011 | M3-2 | MEDIUM | RESOLVED | transaction/provenance | NO | NO |
| M3-ISSUE-0012 | M3-3 | MEDIUM | RESOLVED | extraction provider wiring | NO | NO |
| M3-ISSUE-0013 | M3-4 | MEDIUM | RESOLVED | topic limitation persistence | NO | NO |
| M3-ISSUE-0014 | M3-5 | MEDIUM | RESOLVED | topic read projection | NO | NO |
| M3-ISSUE-0015 | M3-5 | MEDIUM | RESOLVED | frontend capability projection | NO | NO |
| M3-ISSUE-0016 | M3-5 | MEDIUM | RESOLVED | async API response contract | NO | NO |
| M3-ISSUE-0017 | M3-6 | MEDIUM | RESOLVED | Open Design delivery | NO | NO |
| M3-ISSUE-0018 | M3-6 | LOW | RESOLVED | frontend test type-check baseline | NO | NO |
| M3-ISSUE-0019 | M3-7 | LOW | OPEN | formal literature golden set | NO | NO |
| M3-ISSUE-0020 | M3-7 | HIGH | RESOLVED | recorded analysis provenance | NO | NO |
| M3-ISSUE-0021 | M3-9 | LOW | OPEN | frontend supply chain | NO | NO |
| M3-ISSUE-0022 | M3-9 | HIGH | RESOLVED | EvidenceSpan database constraint | NO | NO |
| M3-ISSUE-0023 | M3-8 | MEDIUM | RESOLVED | no-coordinate verification capability | NO | NO |
| M3-ISSUE-0024 | M3-9 | HIGH | RESOLVED | confirmed-question test provenance | NO | NO |
| M3-ISSUE-0025 | M3-9 | HIGH | RESOLVED | recorded model source provenance | NO | NO |
| M3-ISSUE-0026 | M3-9 | MEDIUM | RESOLVED | clean-room test inputs and dirty-worktree guard | NO | NO |
| M3-ISSUE-0027 | M3-9 | MEDIUM | RESOLVED | verification/retry regression fixtures | NO | NO |

## Issues

### M3-ISSUE-0001

- stage: `M3-0`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `API contract`
- authoritative_requirement: 正式端点名称由
  `docs/contracts/PROJECT_RESEARCH_AND_LITERATURE_API.md` 17.6-18.4 定义。
- observed_behavior: M3 里程碑摘要写为
  `POST /api/v1/documents/{document_id}/extractions`，API 子契约写为
  `POST /api/v1/documents/{document_id}/literature-extractions`。
- evidence: `docs/roadmap/milestones/M3_EVIDENCE_MATRIX.md:239`；
  `docs/contracts/PROJECT_RESEARCH_AND_LITERATURE_API.md:960`。
- root_cause: 里程碑摘要在正式 API 子契约命名冻结前保留了旧简称。
- affected_files: M3 Router、OpenAPI、generated client、frontend mutations、contract tests。
- blocks_current_stage: `NO`
- blocks_m3_exit_gate: `NO`，前提是只实现正式名称且不添加兼容别名。
- safe_continuation: 以 API 子契约为准，所有阶段仅使用
  `/literature-extractions`。
- resolution: 已在 `M3_IMPLEMENTATION_PLAN.md` 冻结正式端点；不实现
  `/extractions` 别名。
- focused_verification: Stage 3 OpenAPI operation/path assertion、generated-client
  consistency、旧别名 404 测试。
- next_milestone_impact: M6/M7 只消费冻结的 M3 DTO/端点，不感知旧简称。

### M3-ISSUE-0002

- stage: `M3-0`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `state machine`
- authoritative_requirement: 状态转换由
  `docs/data-model/STATE_MACHINES_AND_INVARIANTS.md` 第 32 章定义。
- observed_behavior: 模型摘要仅列出 `DRAFT`、`NEEDS_REVIEW`、`CONFIRMED`、
  `SUPERSEDED`、`INVALIDATED`；正式状态机还包含 `EXTRACTING`、`FAILED`。
- evidence: `LITERATURE_AND_EVIDENCE_MODELS.md:357-363`；
  `STATE_MACHINES_AND_INVARIANTS.md:482-505`。
- root_cause: 模型对象摘要未同步完整运行状态。
- affected_files: model enum、migration enum、Service transition table、Job/Worker、
  API DTO、frontend fail-closed mapping、tests。
- blocks_current_stage: `NO`
- blocks_m3_exit_gate: `NO`
- safe_continuation: 采用更具体的正式状态机全集，不新增其他状态。
- resolution: 冻结为 `DRAFT|EXTRACTING|NEEDS_REVIEW|CONFIRMED|SUPERSEDED|INVALIDATED|FAILED`。
- focused_verification: Stage 1 enum/migration test；Stage 2 合法和非法转换表驱动测试。
- next_milestone_impact: M6/M7 可明确区分失败、失效和已确认抽取。

### M3-ISSUE-0003

- stage: `M3-0`
- severity: `HIGH`
- status: `RESOLVED`
- area: `persistence/history`
- authoritative_requirement: LIT-P0-013 要求字段修正保存原值、新值、actor、时间、
  原因、原/新证据和 AI 版本；API 17.9A 要求 EvidenceSpan verification record
  保存 actor、时间、页码、note 和当时 source hash，且历史不可覆盖。
- observed_behavior: M3 六核心实体清单没有给出两个历史对象的持久化形态。
- evidence: `LITERATURE_AND_EVIDENCE_REQUIREMENTS.md:386-397`；
  `PROJECT_RESEARCH_AND_LITERATURE_API.md:1039-1054`；
  `M3_EVIDENCE_MATRIX.md:71-80`。
- root_cause: 里程碑摘要只列主业务实体，未列 append-only 支撑实体。
- affected_files: `models.py`、0013 migration、field correction Service、verification
  Service、Audit、API tests。
- blocks_current_stage: `NO`
- blocks_m3_exit_gate: `NO` after Stage 1 implementation; would be `YES` if omitted.
- safe_continuation: 在 0013 中建立独立 append-only 表，不用 JSON 大包或覆盖当前行代替。
- resolution: 冻结 `LiteratureExtractionFieldRevision` 和
  `EvidenceSpanVerificationRecord`；当前行只保存投影，历史行是权威记录。
- focused_verification: Stage 1 FK/append-only/current-projection tests；Stage 3 API
  correction/verification history tests。
- next_milestone_impact: M6/M7 能消费可追溯证据验证与字段来源，不依赖 UI 历史。

### M3-ISSUE-0004

- stage: `M3-0`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `enum contract`
- authoritative_requirement: confirmation、field evidence、EvidenceSpan location/review、
  parser coverage 与 user-declared read scope 必须可严格校验且未知值 fail closed。
- observed_behavior: 权威文档定义了语义但没有为 `confirmation_status`、
  `evidence_status`、`review_status`、`parser_coverage` 完整列出值集合。
- evidence: `LITERATURE_AND_EVIDENCE_MODELS.md:367-474`；
  `PROJECT_RESEARCH_AND_LITERATURE_API.md:993-1054`。
- root_cause: 字段表和 API 示例只展示部分值，缺少统一枚举清单。
- affected_files: model/migration enum、Pydantic/OpenAPI、frontend known-status mapping、
  golden/contract tests。
- blocks_current_stage: `NO`
- blocks_m3_exit_gate: `NO`
- safe_continuation: 使用满足已写语义的最小闭合集合；任何未列值拒绝，不做 adapter
  猜测。
- resolution: 完整枚举已冻结在 `M3_IMPLEMENTATION_PLAN.md` 的 Contract Freeze。
- focused_verification: Stage 1 metadata/DB enum tests；Stage 3 OpenAPI enum completeness；
  Stage 5 unknown fail-closed mapper tests。
- next_milestone_impact: M6/M7 获得稳定验证和阅读范围枚举。

### M3-ISSUE-0005

- stage: `M3-0`
- severity: `LOW`
- status: `RESOLVED`
- area: `local verification environment`
- authoritative_requirement: pgvector adoption must be tested against the exact Python,
  Psycopg, PostgreSQL and pgvector server stack; migrations require empty/repeated upgrade.
- observed_behavior: host has Python 3.13, the checked `.venv` is not a usable Windows
  environment, and Docker Desktop daemon is not running. A real PostgreSQL `EXPLAIN` and
  extension round-trip could not run in Stage 0.
- evidence: host tool probe; repository requires Python `>=3.14,<4.0`; Compose CLI exists
  but cannot connect to `dockerDesktopLinuxEngine`.
- root_cause: non-repository host/runtime availability.
- affected_files: none in Stage 0; Stage 1 migration and any later vector persistence/query.
- blocks_current_stage: `NO`
- blocks_m3_exit_gate: `NO`
- safe_continuation: rely on static migration-head graph and isolated package/SQL compilation
  now; do not adopt `pgvector-python` until a real DB-backed focused test is needed and passes.
- resolution: Docker Desktop/PostgreSQL were restored. Stage 9 passed isolated empty/repeated
  upgrades, pgvector smoke, `alembic check`, the complete database suite and clean-room service
  recovery without using the developer database or default Compose volumes.
- focused_verification: exact Compose image, `CREATE EXTENSION`, `VECTOR(n)` insert/query,
  wrong dimension, cross-project negative, `EXPLAIN`, empty/repeated migration.
- next_milestone_impact: no M3 Competition Core impact because Stage 0 freezes lexical/native
  chunk retrieval as the first implementation and vector retrieval as optional.

### M3-ISSUE-0006

- stage: `M3-0`
- severity: `LOW`
- status: `RESOLVED`
- area: `source-research/UI registry freshness`
- authoritative_requirement: current local code and lock files override stale historical
  implementation-status prose; Open Design ownership rules remain authoritative.
- observed_behavior: TanStack source research says the package is not added, but
  `@tanstack/react-table` 8.21.3 is in `frontend/package.json` and `bun.lock`; the UI registry
  still marks Literature/PDF route and ViewModel as `TBD/NOT_STARTED`, while M2 has real
  literature/document routes and features.
- evidence: `docs/source-research/projects/tanstack-table.md`; `frontend/package.json`;
  `frontend/src/routes/_layout/projects.$projectId_.literature.tsx`;
  `docs/development/FRONTEND_DESIGN_INTEGRATION_RULES.md:385`.
- root_cause: implementation advanced after the research/status snapshot.
- affected_files: source-research current-state prose and UI Contract Registry.
- blocks_current_stage: `NO`
- blocks_m3_exit_gate: `NO`
- safe_continuation: use actual v8.21.3 lock and current M2 route/features; Stage 5 creates the
  M3 handoff and updates registry facts without changing ownership rules.
- resolution: Stage 5 updated the UI Contract Registry and created
  `docs/acceptance/M3_OPEN_DESIGN_HANDOFF.md` with actual package, route, feature and ownership facts;
  no dependency change was required.
- focused_verification: package/lock consistency, existing table construction smoke, route tree
  and UI boundary guards.
- next_milestone_impact: none if Stage 5 handoff records actual paths and ownership.

### M3-ISSUE-0007

- stage: `M3-0`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `decision API path`
- authoritative_requirement: 正式端点名称以
  `PROJECT_RESEARCH_AND_LITERATURE_API.md` 的 Documents 前置 Literature API 为准。
- observed_behavior: 阶段提示摘要写为
  `/api/v1/literature-records/{id}/decisions`，正式 API 子契约写为
  `POST/GET /api/v1/literature/{literature_id}/decisions`。
- evidence: `PROJECT_RESEARCH_AND_LITERATURE_API.md:833-861`。
- root_cause: 阶段摘要使用领域对象全名，既有 API namespace 使用稳定的
  `/literature` 资源名。
- affected_files: M3 Router、OpenAPI、generated client、frontend mutation/query、tests。
- blocks_current_stage: `NO`
- blocks_m3_exit_gate: `NO`
- safe_continuation: 复用既有 `/literature` namespace，不添加重复别名。
- resolution: 冻结 POST/GET `/api/v1/literature/{literature_id}/decisions`。
- focused_verification: Stage 3 OpenAPI path/operation assertions、decision history tests、
  `/literature-records/...` 404。
- next_milestone_impact: M6/M7 使用稳定 literature decision history endpoint。

### M3-ISSUE-0008

- stage: `M3-0`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `EvidenceSpan read API`
- authoritative_requirement: 当前阶段要求正式 EvidenceSpan 单项读取；API 17.9A 已冻结
  `/api/v1/evidence-spans/{evidence_span_id}/verification-records` namespace。
- observed_behavior: API 17.6-18.4 未显式列出 EvidenceSpan 单项 GET 路径。
- evidence: `PROJECT_RESEARCH_AND_LITERATURE_API.md:1017-1054`；M3 阶段 3 要求。
- root_cause: 创建和 verification 子契约已迁入，单项读取摘要遗漏。
- affected_files: Router、OpenAPI、generated client、PDF deep-link/query、tests。
- blocks_current_stage: `NO`
- blocks_m3_exit_gate: `NO`
- safe_continuation: 使用已冻结 resource namespace 的最小 REST 读取端点，不增加列表或
  第二种读取协议。
- resolution: 冻结 `GET /api/v1/evidence-spans/{evidence_span_id}`；返回 project-scoped
  RECA DTO，非成员 404。
- focused_verification: Stage 3 detail/no-disclosure/cross-project/OpenAPI tests；Stage 6
  deep-link refresh test。
- next_milestone_impact: M6/M7 可按稳定 span ID 获取证据来源和验证状态。

### M3-ISSUE-0009

- stage: `M3-1`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `migration identifiers`
- authoritative_requirement: Alembic migration and SQLModel metadata must follow the
  repository naming convention and compile for PostgreSQL, whose identifiers are limited to
  63 bytes.
- observed_behavior: the first offline DDL compilation found an auto-generated field revision
  user FK name and an auto-generated field revision index name longer than PostgreSQL permits.
- evidence: `alembic upgrade head --sql` raised `sqlalchemy.exc.IdentifierError` for the two
  generated names before the migration could finish compiling.
- root_cause: the long supporting-table name combined with SQLModel's automatic FK/index naming.
- affected_files: `backend/app/models.py` and
  `backend/app/alembic/versions/0013_m3_evidence_matrix.py`.
- blocks_current_stage: `NO`
- blocks_m3_exit_gate: `NO`
- safe_continuation: use explicit concise FK/index names for long M3 supporting-table columns;
  validate every metadata identifier against the PostgreSQL dialect and compile the complete
  migration graph offline.
- resolution: replaced the generated names with explicit `fk_field_revisions_*` and
  `ix_field_revisions_*` names; full offline upgrade SQL now compiles successfully.
- focused_verification: PostgreSQL dialect validated all 292 metadata identifiers; all 122 named
  constraints/indexes on M3 tables were found in the offline head SQL.
- next_milestone_impact: none; later migrations should retain explicit short names on long tables.

### M3-ISSUE-0010

- stage: `M3-2`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `AI schema boundary`
- authoritative_requirement: `AI_SCHEMA_CONTRACTS.md` names the public
  `LiteratureExtractionOutput@1.0` field reference as `evidence_span_ids`; Stage 0 and the
  Stage 2 prompt require model-provided source candidates to pass the deterministic locator
  before any EvidenceSpan ID can exist.
- observed_behavior: the strict pre-locator provider payload is currently named
  `LiteratureExtractionOutput` and uses `evidence_candidates`, while the immutable artifact is
  correctly marked as requiring locator validation and is never returned as public DTO truth.
- evidence: `backend/app/evidence/schemas.py`,
  `backend/app/agents/prompts/literature-extraction-1.0.0.txt`, and
  `docs/contracts/AI_SCHEMA_CONTRACTS.md` section 32.2.
- root_cause: the authority describes the post-validation result shape but does not name the
  required pre-validation candidate envelope.
- affected_files: evidence schemas, prompt manifest, Stage 3 response DTO/OpenAPI, contract tests.
- blocks_current_stage: `NO`
- blocks_m3_exit_gate: `YES`, until the internal candidate envelope and public post-locator DTO
  have distinct frozen names or the authority explicitly adopts the two-step shape.
- safe_continuation: keep `evidence_candidates` internal, validate every candidate, persist only
  server-created `evidence_span_id`, and do not expose the raw provider artifact through Stage 3.
- resolution: Stage 8 froze `LiteratureExtractionCandidateOutput@1.0` as the raw provider shape
  containing only `evidence_candidates`, while `LiteratureExtractionOutput@1.0` is the post-locator
  shape containing server-created `evidence_span_ids`. The AI authority, prompt, manifest and schema
  names now express the same two-step trust boundary.
- focused_verification: schema/prompt/manifest focused regression PASS (`17 passed`); raw provider
  candidates cannot submit trusted span IDs. Prompt manifest SHA-256 is
  `6c1b36bb38afd0ac9be9c2ea26a4f420caf85b4981a09ab6480aa86e134c8349`.
- next_milestone_impact: M6/M7 must consume the post-locator public DTO, never model candidate IDs.

### M3-ISSUE-0011

- stage: `M3-2`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `transaction/provenance`
- authoritative_requirement: Service owns the transaction and must create the domain request,
  Job, ModelInvocation, Audit, and idempotency result without leaving a partial request graph.
- observed_behavior: existing `create_model_invocation` commits internally. The Stage 2 request
  Service must therefore commit the new extraction before Job dispatch and cannot provide one
  database transaction across extraction, Job, invocation, and idempotency persistence.
- evidence: `backend/app/agents/service.py:create_model_invocation` and
  `backend/app/evidence/extraction.py:request_extraction_job`.
- root_cause: the reused M1/M2 ModelInvocation Service owns its own commit boundary.
- affected_files: agents service, existing AI callers, evidence extraction request Service, and
  failure-injection tests.
- blocks_current_stage: `NO`; deterministic locator/Worker execution and terminal provenance are
  independent and implemented.
- blocks_m3_exit_gate: `YES`; partial-create compensation or caller-owned transaction support is
  required before the final gate.
- safe_continuation: do not add a second invocation store; retain explicit failure states and Audit,
  and defer shared transaction-boundary refactoring to Stage 8 with all existing callers covered.
- resolution: `create_model_invocation` now supports caller-owned transactions with `commit=False`.
  M3 extraction, summary and topic request Services commit the domain object, ModelInvocation, Job,
  Audit and initial idempotency row together before dispatch. Dispatch failure terminalizes both the
  invocation and domain resource, and idempotency results are updated through the owning Service.
- focused_verification: PostgreSQL failure-injection regression PASS (`5 passed`) across invocation,
  Job and idempotency rollback points plus dispatch terminalization.
- next_milestone_impact: M6/M7 benefit from one reusable caller-owned AI transaction contract.

### M3-ISSUE-0012

- stage: `M3-3`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `extraction provider wiring`
- authoritative_requirement: 外部模型不可用时必须明确失败或进入人工复核，不得伪装成功；
  正式抽取端点必须通过受治理的 provider identity 创建 Job/ModelInvocation。
- observed_behavior: Stage 3/4 Router 已提供正式抽取、summary 和 topic POST 以及可替换
  provider identity 边界，但生产默认 factory 尚未绑定具体 provider，调用会明确返回
  `503 MODEL_PROVIDER_UNCONFIGURED`；Recorded/MOCK identity 仅由测试注入。
- evidence: `backend/app/api/routes/evidence.py:107-118`；
  `backend/tests/api/routes/test_evidence.py:test_extraction_request_and_openapi_contract`。
- root_cause: M3 尚未冻结生产模型 provider/configuration；阶段 2 只要求确定性
  Recorded/Fake 测试边界，且禁止把 fixture 放入生产路径。
- affected_files: extraction/analysis Router provider factories、Settings/provider adapter、
  部署配置、provider failure tests。
- blocks_current_stage: `NO`；其余同步 review API、OpenAPI 和明确失败契约可独立完成。
- blocks_m3_exit_gate: `YES`；M3 最终验收前正式抽取请求必须可进入受治理 Job，或权威
  配置明确采用无外部模型的受支持运行模式。
- safe_continuation: 保留 fail-closed 503 默认值；测试仅 monkeypatch 受治理 MOCK identity，
  不把 Recorded fixture 或环境猜测接入生产路径。
- resolution: Stage 8 added one OpenAI-compatible HTTP provider adapter using existing `httpx`,
  governed `LIVE` execution identity, and all-or-nothing `MODEL_BASE_URL`, `MODEL_API_KEY` and
  `MODEL_NAME` settings. Routers return explicit 503 when configuration is absent; Workers bind and
  verify the persisted identity. No Agent runtime, Recorded fixture production path or dependency was
  added.
- focused_verification: provider/config/OpenAPI no-database regression PASS (`16 passed`), LIVE
  invocation PostgreSQL regression PASS (`1 passed`), provider factory regression PASS (`5 passed`),
  and focused mypy PASS for the six affected source files.
- next_milestone_impact: 阶段 5/6 UI 必须把 503 映射为明确不可用状态，不得显示抽取成功；
  M6/M7 只能消费已持久化、已定位的抽取结果。

### M3-ISSUE-0013

- stage: `M3-4`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `topic limitation persistence`
- authoritative_requirement: TopicCandidate 每项必须独立保存并展示限制；模型原始输出和
  科研来源不可因当前投影缺列而覆盖或丢失。
- observed_behavior: `TopicGenerationOutput@1.0` 已严格要求每个候选的 `limitations`，但
  Stage 1 `topic_candidates` 表只有 `major_risks`，没有语义独立的 limitations 列。
- evidence: `AI_SCHEMA_CONTRACTS.md:495-542`；M3 阶段 4 当前提示；
  `backend/app/models.py:1930-2008`。
- root_cause: Stage 1 模型按早期字段表建立，未把阶段 4/里程碑中的“限制”与
  `major_risks` 分离持久化。
- affected_files: `backend/app/models.py`、后继 Alembic migration、TopicCandidate DTO/
  Service、metadata/migration/API tests。
- blocks_current_stage: `NO`；正式 Stage 4 POST 只返回 Job，Worker 将完整且已校验的
  TopicGenerationOutput 保存为 immutable MODEL_OUTPUT Artifact，同时领域行保存其余冻结字段
  和全部来源关联，不伪造或折叠 limitations。
- blocks_m3_exit_gate: `YES`；进入最终 UI/Exit Gate 前必须增加独立列并从验证输出事务性投影。
- safe_continuation: 不把 limitations 塞入 `major_risks` 或 `user_constraints`，不暴露不完整
  TopicCandidate public endpoint；Stage 8 添加单一后继迁移和 focused backfill/projection test。
- resolution: Stage 9 added non-null `topic_candidates.limitations` persistence to the unreleased
  0013 migration and SQLModel, persisted model output, exposed it in the public DTO, regenerated the
  client, and removed the frontend unavailable placeholder.
- focused_verification: schema/OpenAPI golden checks, generated-client check, production TypeScript,
  build and Playwright PASS; database runtime remains covered by M3-ISSUE-0005.
- focused_verification: migration/metadata 一致；每个 candidate limitations round-trip；
  retry 不丢失；public DTO 明确分离 risks/limitations；Artifact 与领域投影 hash 对齐。
- next_milestone_impact: Stage 5 topic UI integration 必须等待 Stage 8 正式列，不得从
  `major_risks` 猜测限制。

## Stage 0 Evidence

```text
Migration revision graph: PASS, unique head 0012_document_upload
Tracked git diff at entry: empty
Untracked preservation: PASS, no files modified or removed
pgvector-python isolated compile spike: PASS
  pgvector-python 0.5.0
  SQLModel 0.0.39
  SQLAlchemy 2.0.51
  Psycopg 3.3.4
  VECTOR(3) compiled
  WHERE project_id precedes exact cosine ORDER BY <=> in generated SQL
Real PostgreSQL/pgvector execution: NOT RUN, M3-ISSUE-0005
Native lexical/chunk retrieval and bounded source-preserving packing spike: PASS
  cross-project candidates: 0
  EvidenceSpan writes: 0
  PaperQA runtime: NOT ADOPTED
ASReview runtime: NOT ADOPTED; manual LiteratureDecision remains mandatory
pdfjs-dist 6.2.108 + Vite 8.1.5 browser build: PASS
  emitted main bundle and matching pdf.worker.min asset
  modern build in Node/Bun without DOM APIs: expected failure; browser-only boundary frozen
TanStack Table 8.21.3 current-stack construction smoke: PASS
```

## Stage 0 Changes and Focused Tests

Modified files:

```text
docs/acceptance/M3_ISSUE_REGISTER.md
docs/acceptance/M3_IMPLEMENTATION_PLAN.md
```

Focused checks are listed in Stage 0 Evidence. No backend suite, full frontend build,
Playwright, clean-room, migration, OpenAPI generation, dependency lock change, or formal M3
business implementation was performed.

```text
STAGE_RESULT=PASS_WITH_ISSUES
NEXT_STAGE_EXECUTED=NO
```

## Stage 1 Changes and Focused Tests

Stage 1 established the database truth only. No Worker, API, generated client, Router or frontend
business implementation was added.

Modified/created files:

```text
backend/app/models.py
backend/app/alembic/versions/0013_m3_evidence_matrix.py
backend/tests/conftest.py
backend/tests/evidence/test_models.py
backend/tests/evidence/test_database_constraints.py
backend/tests/alembic/test_migrations.py
backend/tests/alembic/test_migration_runtime.py
docs/acceptance/M3_ISSUE_REGISTER.md
```

Focused verification:

```text
Python syntax compile: PASS
Ruff check and format check for touched non-migration Python: PASS
M3 metadata/model tests: PASS (3)
Migration graph/static tests: PASS (15)
PostgreSQL offline upgrade SQL through 0013: PASS
PostgreSQL identifier validation: PASS (292 metadata identifiers)
M3 metadata names present in offline SQL: PASS (122/122)
Database constraint test collection: PASS (1 test)
Real PostgreSQL empty/repeated upgrade and alembic check: NOT RUN (M3-ISSUE-0005)
Real PostgreSQL Check/Unique/FK/cross-project/append-only negatives: NOT RUN
Safe temporary-database downgrade to 0012 and re-upgrade: NOT RUN
Full backend, Playwright, clean-room and supply-chain suites: NOT RUN by stage policy
```

Current migration head: `0013_m3_evidence_matrix`.

```text
STAGE_RESULT=PASS_WITH_ISSUES
NEXT_STAGE_EXECUTED=NO
```

## Stage 2 Changes and Focused Tests

Stage 2 implemented only deterministic evidence location, strict ten-field extraction,
LiteratureExtraction Service/Worker execution, and provenance. No Router, frontend, evidence-set
summary, retrieval/embedding stage, TopicCandidate, PaperQA runtime, or Agent runtime was added.

Modified/created files:

```text
backend/app/agents/service.py
backend/app/agents/prompts/literature-extraction-1.0.0.txt
backend/app/agents/prompts/prompt-manifest.yaml
backend/app/evidence/__init__.py
backend/app/evidence/schemas.py
backend/app/evidence/locator.py
backend/app/evidence/extraction.py
backend/app/workers/jobs.py
backend/tests/evidence/test_schemas.py
backend/tests/evidence/test_locator.py
backend/tests/evidence/test_extraction_workflow.py
docs/acceptance/M3_ISSUE_REGISTER.md
```

Focused verification:

```text
Python syntax compile for touched Python: PASS
Ruff format/check for touched Stage 2 Python: PASS
Strict schema, locator, M3 metadata, and prompt manifest tests: PASS (21)
Workflow test definitions: PASS syntax compile (3 tests)
Real workflow collection/execution on repository Python 3.14 + PostgreSQL: NOT RUN
  Host only has Python 3.13; Docker daemon is unavailable (M3-ISSUE-0005)
Full backend, full build, Playwright, clean-room and supply-chain suites: NOT RUN by stage policy
```

```text
STAGE_RESULT=PASS_WITH_ISSUES
NEXT_STAGE_EXECUTED=NO
```

## Stage 3 Changes and Focused Tests

Stage 3 implemented only the core extraction, field correction, EvidenceSpan review,
LiteratureDecision history and literature-matrix Service/API contracts. Evidence-set summaries,
TopicCandidate, retrieval, visual frontend and Agent runtime were not started.

Modified/created files:

```text
backend/app/evidence/schemas.py
backend/app/evidence/extraction.py
backend/app/evidence/review.py
backend/app/api/routes/evidence.py
backend/app/api/main.py
backend/app/main.py
backend/tests/api/routes/test_evidence.py
backend/tests/api/routes/test_evidence_openapi.py
frontend/openapi.json
frontend/src/api/generated/index.ts
frontend/src/api/generated/sdk.gen.ts
frontend/src/api/generated/types.gen.ts
docs/acceptance/M3_ISSUE_REGISTER.md
```

Focused verification:

```text
Python syntax/import/OpenAPI generation: PASS
Ruff check for Stage 3 backend and tests: PASS
Pure schema/locator/model/OpenAPI contract tests: PASS (16)
Stage 3 database API test collection: PASS (4 tests)
Stage 3 database API execution: NOT RUN (PostgreSQL/Docker unavailable, M3-ISSUE-0005)
OpenAPI required paths, headers, no alias/confirm duplicate, unique operation IDs: PASS
Formal generated-client flow: PASS (4 generated files)
Generated-client consistency check: PASS
Frontend TypeScript no-emit check: PASS
OpenAPI JSON repository formatting: PASS
git diff --check: PASS
Full backend, build, Playwright, clean-room and supply-chain suites: NOT RUN by stage policy
```

Current migration head remains `0013_m3_evidence_matrix`.

### M3-ISSUE-0019

- stage: `M3-7`
- severity: `LOW`
- status: `OPEN`
- area: `formal literature golden set`
- authoritative_requirement: `GOLDEN_SETS_AND_METRICS.md` requires 10-20 real papers with
  human-reviewed literature fields and EvidenceSpan annotations; Stage 7 permits a documented
  minimum reusable subset but must not invent real papers or treat model output as annotation truth.
- observed_behavior: the repository contains no authorized real-paper M3 collection or double-review
  records. The only existing PDF is a technical minimal PDF fixture and cannot be represented as a
  real publication. Stage 7 added one explicitly synthetic, repository-authored deterministic subset
  for structural and locator regression only.
- evidence: `tests/golden/m3_literature_evidence/v1/README.md`, `manifest.json`, existing
  `frontend/tests/fixtures/minimal.pdf`, and the pre-Stage-7 `tests/golden/` inventory.
- root_cause: authorized paper acquisition, redistribution review, annotation staffing and
  disagreement adjudication have not been completed for M3.
- affected_files: formal M3 golden corpus, source/license manifest, dual-review records, metric
  calculation and Stage 9 scientific acceptance.
- blocks_current_stage: `NO`; the documented synthetic subset supports deterministic contract and
  locator tests without impersonating scientific ground truth.
- blocks_m3_exit_gate: `NO`; the project owner authorized engineering closeout without inventing
  scientific metrics. The deterministic Competition Core is accepted, while human accuracy metrics
  remain explicitly `NOT MEASURED`.
- safe_continuation: use the synthetic subset only for code correctness, provenance, failure and
  workflow regression; report all scientific extraction accuracy metrics as `NOT MEASURED` until an
  authorized real-paper collection is reviewed.
- resolution: deferred as a transparent scientific-validation follow-up. The repository synthetic
  corpus remains limited to deterministic correctness and is never reported as real-paper ground
  truth. Acquire lawful papers and dual-review annotations before any extraction-accuracy claim or
  external scientific benchmark publication.
- focused_verification: source/license audit, two-person annotation records, exact ten-field and
  EvidenceSpan checks, and metric computation over the formal real-paper corpus.
- next_milestone_impact: does not block M4 data-quality development. M6/M7 may consume the verified
  source contract, but must not claim corpus-level extraction accuracy until this issue is resolved.

### M3-ISSUE-0020

- stage: `M3-7`
- severity: `HIGH`
- status: `RESOLVED`
- area: `recorded analysis provenance`
- authoritative_requirement: Recorded/fixed model inputs must be repeatable and provenance-bound;
  reviewed recording hash and provider identity must match the output used for Summary and Topic
  persistence, as already enforced by LiteratureExtraction.
- observed_behavior: `execute_summary_job` and `execute_topic_job` accept an injected provider,
  validate only output Schema/source IDs, and persist the result without checking that the provider
  identity matches the ModelInvocation or that `canonical_hash(raw)` equals `recording_hash` in
  RECORDED mode. A substituted fixed output could retain the original invocation provenance.
- evidence: `backend/app/evidence/analysis.py` summary execution around `provider.summarize` and topic
  execution around `provider.generate_topics`; contrast with
  `backend/app/evidence/extraction.py` `MODEL_RECORDING_HASH_MISMATCH` enforcement.
- root_cause: Stage 4 analysis execution did not reuse the extraction provider-identity and recorded
  hash guard.
- affected_files: `backend/app/evidence/analysis.py`, analysis workflow tests, ModelInvocation and
  generated Artifact provenance assertions.
- blocks_current_stage: `NO`; Stage 7 can define the fixed fixture and tests while clearly recording
  that analysis tamper detection is not yet evidence.
- blocks_m3_exit_gate: `YES`
- safe_continuation: use the Stage 7 fixed provider only for deterministic structure/source tests and
  do not claim Recorded integrity; retain immutable raw output Artifacts for later comparison.
- resolution: Stage 9 enforces exact provider identity equality with ModelInvocation and validates
  `canonical_hash(raw)` against `recording_hash` in RECORDED mode for Summary and Topic before
  Schema validation or persistence. Focused database regressions assert failure and zero persisted
  Summary conclusions/Topic candidates for substituted identity or payload.
- focused_verification: Ruff, mypy and no-database gates PASS; focused regression definitions compile;
  PostgreSQL execution remains unavailable under M3-ISSUE-0005.
- focused_verification: mismatched provider identity and changed RECORDED payload must fail without
  persisting Summary conclusions or TopicCandidate rows; matching recordings must preserve hash,
  invocation, ProcessingRun and Artifact provenance.
- next_milestone_impact: Stage 8 repair is required before Stage 9 Recorded vertical evidence can be
  accepted.

## Stage 7 Changes and Focused Tests

Stage 7 added only golden material, deterministic golden/vertical test definitions, the production
browser E2E contract, one small Playwright collection fix, and acceptance documentation. It did not
repair M3 business defects or start Stage 8.

Modified/created files:

```text
tests/golden/m3_literature_evidence/v1/README.md
tests/golden/m3_literature_evidence/v1/manifest.json
backend/tests/golden/test_m3_literature_evidence_golden.py
backend/tests/integration/test_m3_vertical_demo.py
frontend/tests/m3-stage7-vertical.spec.ts
frontend/playwright.shell.config.ts
docs/acceptance/M3_VERTICAL_INTEGRATION_REPORT.md
docs/acceptance/M3_ISSUE_REGISTER.md
```

Focused verification:

```text
Golden manifest JSON/count/hash/offset/included-source check: PASS
Python syntax compile for new golden/integration tests: PASS
Ruff check/format for new backend tests: PASS
Backend golden pytest runtime: NOT RUN (Python 3.14 dependencies unavailable, M3-ISSUE-0005)
PostgreSQL recorded vertical integration: NOT RUN (Docker/PostgreSQL unavailable, M3-ISSUE-0005)
Production frontend TypeScript: PASS
Generated-client consistency: PASS
UI boundary guard: PASS (4)
Production mock guard: PASS (6)
M3 fixture contract tests: PASS (5)
Focused M3 browser failure/degradation tests: PASS (4)
Real production Stage 7 browser vertical: SKIPPED (fresh server fixture absent and M3-ISSUE-0014)
Full build, full Playwright and clean-room: NOT RUN by Stage 7 policy
```

Current migration head remains `0013_m3_evidence_matrix`.

```text
STAGE_RESULT=PASS_WITH_ISSUES
NEXT_STAGE_EXECUTED=NO
```

### M3-ISSUE-0014

- stage: `M3-5`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `topic read projection`
- authoritative_requirement: Stage 5 requires a TopicCandidate frontend feature based on Stage 4
  formal DTOs, and Topic candidates must remain exactly three with LiteratureRecord/EvidenceSpan
  sources.
- observed_behavior: the backend defines `TopicGenerationRunPublic` and `TopicCandidatePublic`, but
  OpenAPI exposes only `POST /projects/{project_id}/topic-generation-runs` returning `JobEnvelope`;
  there is no formal GET operation that projects the completed run and candidates.
- evidence: `backend/app/evidence/schemas.py`, `backend/app/api/routes/evidence.py`,
  `frontend/openapi.json`, and `frontend/src/api/generated/types.gen.ts`.
- root_cause: Stage 4 persisted and serialized the topic result internally but omitted its read API.
- affected_files: topic Router/OpenAPI/generated client, topic query/container, contract/E2E tests.
- blocks_current_stage: `NO`
- blocks_m3_exit_gate: `YES`
- safe_continuation: freeze the pure `TopicCandidatesViewModel`, exactly-three/source guards and
  fixtures; keep the production container empty/fail-closed until a generated read DTO exists.
- resolution: Stage 9 added `GET /api/v1/topic-generation-runs/{run_id}` through the existing Service,
  no-disclosure authorization and formal DTO. Generated client, adapter, query and container now
  restore `topicRunId` deep links from server state.
- focused_verification: OpenAPI/generated-client, production TypeScript/build, focused M2/M3
  Playwright (11) and complete shell Playwright (118 passed, 1 environment skip) PASS.
- focused_verification: future GET role/no-disclosure tests, generated-client consistency, mapper
  exact-count/source/unknown-state tests and Job-to-run projection tests.
- next_milestone_impact: Stage 6 can implement pure UI; production topic viewing and Stage 7 vertical
  integration remain blocked until resolved.

### M3-ISSUE-0015

- stage: `M3-5`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `frontend capability projection`
- authoritative_requirement: UI must emit only operations allowed by a server-projected capability;
  unknown permissions fail closed.
- observed_behavior: Matrix and completed Summary responses expose `allowed_actions`, but there is no
  server projection for a user's ability to start Evidence Search or create the first Summary.
- evidence: `LiteratureMatrixEnvelope.allowed_actions`, `EvidenceSetSummaryPublic.allowed_actions`,
  Stage 4 OpenAPI paths and `backend/app/evidence/analysis.py`.
- root_cause: the create/search endpoints authorize internally but no project-level M3 capability
  envelope was added for frontend discovery.
- affected_files: project/M3 workspace projection, OpenAPI/generated client, analysis mapper/container
  and role/capability tests.
- blocks_current_stage: `NO`
- blocks_m3_exit_gate: `YES`
- safe_continuation: typed fixtures may model explicit capabilities for Open Design; production
  analysis mapping keeps search and initial summary creation disabled rather than deriving from role.
- resolution: the existing Literature Matrix envelope now projects `evidence.search` and
  `evidence_summary.create` only for OWNER/EDITOR. The frontend uses an independent matrix-backed
  capability query for first-summary creation and continues to use summary-projected actions for
  topic generation/retry; unknown permissions remain fail-closed.
- focused_verification: backend role projection regression PASS (`1 passed`); frontend lint,
  production TypeScript and generated-client guard PASS; M3 fixture contracts PASS (`5 passed`).
- next_milestone_impact: pure UI is unblocked; production search/first-summary actions are not wired.

### M3-ISSUE-0016

- stage: `M3-5`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `async API response contract`
- authoritative_requirement: M3 must not use HTTP 202 or accepted/local state as business success;
  long work reuses Job/ProcessingRun and success comes from authoritative terminal projection.
- observed_behavior: Topic generation OpenAPI currently returns HTTP 202 `JobEnvelope`.
- evidence: `backend/app/api/routes/evidence.py:459`, `frontend/openapi.json` topic-generation response,
  and generated SDK response type.
- root_cause: Stage 4 copied the existing accepted-Job response convention despite the M3 global
  no-202 constraint.
- affected_files: topic Router/OpenAPI/generated client, mutation/container and API contract tests.
- blocks_current_stage: `NO`
- blocks_m3_exit_gate: `YES`
- safe_continuation: Stage 5 treats the response only as pending Job identity and never projects
  candidates or success from HTTP acceptance.
- resolution: M3 extraction, summary and topic request resources now return `201 Created` Job
  envelopes. Business success remains derived only from terminal server projections; OpenAPI tests
  assert that these M3 operations do not expose 202.
- focused_verification: OpenAPI contract, generated-client, production TypeScript/build and complete
  Playwright PASS.
- focused_verification: response-code/OpenAPI assertion and UI test proving only terminal server data
  produces ready candidates.
- next_milestone_impact: Open Design is unblocked; production topic request semantics need correction
  before Stage 7/9 acceptance.

## Stage 5 Changes and Focused Tests

Stage 5 added only frontend business boundaries, typed fixtures, minimal contract previews, adapter
methods, route/search draft and the Open Design handoff. It did not redesign the visual workspace,
wire the production route, run Playwright, or start Stage 6.

Modified/created files:

```text
docs/acceptance/M3_OPEN_DESIGN_HANDOFF.md
docs/acceptance/M3_ISSUE_REGISTER.md
docs/development/FRONTEND_DESIGN_INTEGRATION_RULES.md
frontend/package.json
frontend/scripts/check-m3-fixtures.test.mjs
frontend/src/api/adapter/index.ts
frontend/src/design-preview/DesignPreviewWorkbench.tsx
frontend/src/features/literature/m3-route-contract.ts
frontend/src/features/evidence-matrix/**
frontend/src/features/evidence-analysis/**
frontend/src/features/topic-candidates/**
```

Focused verification:

```text
TypeScript no-emit: PASS
M3 fixture contract tests: PASS (5)
UI ownership boundary guard: PASS
Production mock guard: PASS
Generated-client consistency: PASS
Biome check for Stage 5 files: PASS
git diff --check: PASS
Full frontend build and Playwright: NOT RUN by Stage 5 policy
```

Current migration head remains `0013_m3_evidence_matrix`.

```text
READY_FOR_OPEN_DESIGN=YES
STAGE_RESULT=PASS_WITH_ISSUES
NEXT_STAGE_EXECUTED=NO
```

### M3-ISSUE-0021

- ID: `M3-ISSUE-0021`
- stage: `M3-9`
- severity: `LOW`
- status: `OPEN`
- area: `frontend supply chain`
- authoritative_requirement: Stage 9 must run the Bun audit and record all remaining dependency
  advisories without silently widening versions or accepting an untested major build-chain upgrade.
- observed_behavior: `bun audit` reports GHSA-4x5r-pxfx-6jf8 for development-only
  `@babel/core@7.28.6`; the advisory affects versions through 7.29.0. No patched 7.x release exists,
  while the available fixed line is Babel 8 and is outside a safe M3 patch.
- evidence: Stage 9 `bun audit`; root `package.json` override and `bun.lock`.
- root_cause: TanStack router build tooling still depends on Babel 7 and the repository pins the last
  compatible reviewed line.
- affected_files: `package.json`, `bun.lock`, frontend build toolchain.
- blocks_current_stage: `NO`
- blocks_m3_exit_gate: `NO`; development-only LOW advisory with no production runtime exposure.
- safe_continuation: retain the exact pin, do not process untrusted source maps in privileged build
  environments, and schedule a tested Babel 8/router-plugin upgrade separately.
- resolution: open until the compatible build chain can move to a fixed Babel release.
- focused_verification: Python audit PASS; Secret scan PASS; frontend build PASS; Bun audit reports
  exactly one LOW advisory.
- next_milestone_impact: M4 may proceed with the same build pin; release engineering must reassess
  before M9 distribution.

### M3-ISSUE-0022

- ID: `M3-ISSUE-0022`
- stage: `M3-9`
- severity: `HIGH`
- status: `RESOLVED`
- area: `EvidenceSpan database constraint`
- authoritative_requirement: EvidenceSpan without coordinates must remain valid for pypdf and other
  degraded parser paths; missing coordinates must not be replaced by fabricated rectangles.
- observed_behavior: PostgreSQL rejects a valid EvidenceSpan whose `bounding_boxes` Python value is
  `None` with `ck_evidence_spans_boxes_array`, before later append-only and current-projection
  constraint assertions can run.
- evidence: focused PostgreSQL test
  `backend/tests/evidence/test_database_constraints.py::test_m3_database_checks_unique_scope_and_append_only_guards`;
  Psycopg bound `bounding_boxes` as JSONB `null`, while the database constraint permits only SQL
  `NULL` or `jsonb_typeof(...) = 'array'`.
- root_cause: `EvidenceSpan.bounding_boxes` uses the default PostgreSQL JSONB None serialization,
  which persists Python `None` as JSON `null`; the model and 0013 constraint assume SQL `NULL`.
- affected_files: `backend/app/models.py`,
  `backend/app/alembic/versions/0013_m3_evidence_matrix.py`, database constraint tests and all
  pypdf/no-coordinate EvidenceSpan persistence paths.
- blocks_current_stage: `NO`
- blocks_m3_exit_gate: `NO`
- safe_continuation: migration graph, empty/repeated upgrade, Alembic check and unrelated metadata
  checks may continue; do not claim PostgreSQL EvidenceSpan persistence or the real vertical as
  passed, and do not fabricate coordinates to bypass the constraint.
- resolution: configured `EvidenceSpan.bounding_boxes` with `JSONB(none_as_null=True)`, preserving
  SQL NULL for coordinate-free spans while retaining the 0013 array constraint. No schema revision
  was needed.
- focused_verification: require a no-coordinate span to persist as the intended null representation;
  reject JSON objects/scalars; retain valid coordinate arrays; rerun cross-project, hash,
  verification and append-only negative assertions.
- focused_verification: PostgreSQL constraint regression PASS (1); complete isolated backend suite
  PASS (310 passed, 2 skipped); empty/repeated 0013 upgrade and `alembic check` PASS.
- next_milestone_impact: M6/M7 may consume pypdf/degraded spans with explicit LOW/no-coordinate
  state; VERIFIED still requires a formal verification record and deterministic location.

## Stage 8/9 Consolidated Repair and Exit Evidence

Stage 9 absorbed the unexecuted Stage 8 repair work only where a root-cause fix was locally
verifiable. It resolved M3-ISSUE-0013, 0014, 0016 and 0020; repaired the M2 literature-route
regression discovered by complete Playwright; and did not fabricate the missing real-paper corpus,
Open Design output, provider configuration or database infrastructure.

```text
Backend Ruff format/check: PASS
Backend mypy: PASS (102 source files)
Backend no_database: PASS (102 passed, 2 skipped)
Focused M3 golden/schema/locator/OpenAPI: PASS (28)
Migration graph head: PASS (0013_m3_evidence_matrix)
PostgreSQL migration/runtime/backend suite: NOT RUN (M3-ISSUE-0005)
Frontend format/lint/generated/boundary/mock/fixture/build: PASS
Complete shell Playwright: PASS (118 passed, 1 real-API vertical skipped)
Repository-wide test TypeScript: FAIL (M3-ISSUE-0018)
Python audit and repository Secret scan: PASS
Bun audit: PASS_WITH_LOW_ADVISORY (M3-ISSUE-0021)
Clean-room: FAIL at build-images; Docker daemon unavailable
Formal 10-20 real-paper dual-reviewed metrics: NOT MEASURED (M3-ISSUE-0019)
STAGE_RESULT=BLOCKED
NEXT_STAGE_EXECUTED=NO
```

## Stage 4 Changes and Focused Tests

Stage 4 implemented only project-scoped native Evidence Search, current-included-literature
EvidenceSetSummary, and exactly-three TopicCandidate backend pipelines/APIs. No vector/PaperQA
runtime, Agent runtime, Topic adoption, or visual frontend was added.

Modified/created files:

```text
backend/app/agents/prompts/evidence-set-summary-1.0.0.txt
backend/app/agents/prompts/topic-candidate-generation-1.0.0.txt
backend/app/agents/prompts/prompt-manifest.yaml
backend/app/evidence/schemas.py
backend/app/evidence/retrieval.py
backend/app/evidence/analysis.py
backend/app/api/routes/evidence.py
backend/app/workers/jobs.py
backend/app/main.py
backend/tests/evidence/test_analysis_schemas.py
backend/tests/evidence/test_retrieval.py
backend/tests/evidence/test_analysis_workflow.py
backend/tests/api/routes/test_evidence.py
backend/tests/api/routes/test_evidence_openapi.py
frontend/openapi.json
frontend/src/api/generated/index.ts
frontend/src/api/generated/sdk.gen.ts
frontend/src/api/generated/types.gen.ts
docs/acceptance/M3_ISSUE_REGISTER.md
```

Focused verification:

```text
Python syntax compile for Stage 4 backend/tests: PASS
Ruff check for affected backend/tests: PASS
Strict schema, prompt, safe-language, source and OpenAPI tests: PASS
Affected pure Stage 1-4 schema/locator/model/OpenAPI tests: PASS (21)
Stage 3/4 database API, retrieval and workflow collection: PASS (9 tests)
Stage 4 database execution: NOT RUN (PostgreSQL/Docker unavailable, M3-ISSUE-0005)
Native retrieval boundary: project filter + formal current decision + bounded top_k/documents
  HYBRID request deterministically falls back to native keyword ranking with limitation
  unverified/hash-mismatched evidence never exposes a trusted EvidenceSpan ID
Summary/topic Job/ProcessingRun/ModelInvocation/Artifact/Audit workflow definitions: PASS
Formal OpenAPI export and generated-client flow: PASS (4 generated files)
Generated-client consistency and frontend TypeScript no-emit: PASS
Required Stage 4 paths, Idempotency-Key and candidate_count min=max=3: PASS
Full backend, build, Playwright, clean-room and supply-chain suites: NOT RUN by stage policy
```

Current migration head remains `0013_m3_evidence_matrix`.

```text
STAGE_RESULT=PASS_WITH_ISSUES
NEXT_STAGE_EXECUTED=NO
```

### M3-ISSUE-0017

- stage: `M3-6`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `Open Design delivery`
- authoritative_requirement: Stage 6 must consume the Stage 5 Open Design handoff without
  inventing a replacement visual system; pure UI, CSS and responsive composition belong to Open
  Design after the Props/Event/fixture contract freeze.
- observed_behavior: the three M3 Workspace files remain the minimal Stage 5 contract previews and
  no additional Open Design UI/CSS output exists in the local worktree.
- evidence: `frontend/src/features/evidence-matrix/ui/EvidenceMatrixWorkspace.tsx`,
  `frontend/src/features/evidence-analysis/ui/EvidenceAnalysisWorkspace.tsx`,
  `frontend/src/features/topic-candidates/ui/TopicCandidatesWorkspace.tsx`, current untracked-file
  inventory and `M3_OPEN_DESIGN_HANDOFF.md`.
- root_cause: Open Design delivery has not been supplied before Stage 6 execution.
- affected_files: the three M3 `ui/**` directories, responsive CSS, design preview and visual
  browser acceptance.
- blocks_current_stage: `NO`
- blocks_m3_exit_gate: `YES`
- safe_continuation: complete Route/Container/mapper/query/mutation/PDF.js integration and focused
  browser-test infrastructure; use only existing RECA visual primitives for a minimal functional
  production surface and do not claim final visual completion.
- resolution: Stage 8 supplied and integrated the pure presentation output in the three frozen M3
  `ui/**` ownership areas. The matrix now has a dense evidence/status hierarchy, stable inspector and
  server-authoritative PDF pane; analysis distinguishes counterexamples, gaps and limitations; topic
  candidates preserve exact server order and source visibility. The shared shell flex child was made
  shrinkable for tablet widths without changing Route, DTO, state or event ownership.
- focused_verification: complete frontend TypeScript PASS; UI boundary (`4 passed`), production mock
  (`6 passed`) and M3 fixture (`5 passed`) guards PASS; focused M3 plus shared-shell Playwright PASS
  (`12 passed`). Visual captures were inspected at 1440x900, 820x1024 and 390x844 with no overlap or
  page-level horizontal overflow; keyboard focus and pypdf text-only degradation passed.
- next_milestone_impact: the M3 visual/responsive gate is unblocked for the next complete Exit Gate;
  no new UI contract is required by M4/M6/M7.

### M3-ISSUE-0023

- ID: `M3-ISSUE-0023`
- stage: `M3-8`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `no-coordinate verification capability`
- authoritative_requirement: pypdf or any EvidenceSpan without trusted coordinates must degrade to
  page/text context and must not offer an operation that upgrades the location to `VERIFIED`.
- observed_behavior: the server action projection could include `evidence_span.verify`, and the
  frontend mapper exposed `canVerify=true` even when `bounding_boxes=[]` and parser type was `PYPDF`.
- evidence: the new 390px pypdf browser assertion initially found the `Verify location` button
  enabled despite zero highlight rectangles.
- root_cause: `mapEvidenceLocation` mapped the server action directly without combining it with the
  frozen coordinate/parser safety prerequisites.
- affected_files: `frontend/src/features/evidence-matrix/mappers.ts` and focused M3 browser tests.
- blocks_current_stage: `NO`; discovered and repaired within this focused visual integration group.
- blocks_m3_exit_gate: `NO`
- safe_continuation: keep the server action necessary but insufficient; the mapper and Container must
  continue to fail closed when coordinates are absent, parser is pypdf, status is unknown or project
  identity does not match.
- resolution: `canVerify` now additionally requires trusted coordinates and a non-pypdf parser; the
  disabled reason explicitly states that trusted coordinates are required.
- focused_verification: 390x844 pypdf Playwright regression PASS with zero highlights, visible
  text-only degradation, disabled verification and zero page overflow; full focused M3 file PASS.
- next_milestone_impact: M6/M7 consumers may display degraded spans but must retain the same
  verification prerequisite.

### M3-ISSUE-0018

- stage: `M3-6`
- severity: `LOW`
- status: `RESOLVED`
- area: `frontend test type-check baseline`
- authoritative_requirement: Stage 6 runs affected frontend checks and Stage 9 must run the complete
  Exit Gate; ordinary missing test utilities and stale DTO contracts must be recorded rather than
  hidden by a narrower successful check.
- observed_behavior: `bunx tsc -p tsconfig.json --noEmit` fails in pre-existing Playwright files due
  to missing `tests/utils/random`, stale `ProjectPermissions.role`, older target use of `Array.at`,
  and unrelated legacy generated/private API expectations. The Stage 6 production source compiles
  with `tsconfig.build.json`, and the new focused test file is accepted and executes successfully.
- evidence: TypeScript diagnostics from `frontend/tests/admin.spec.ts`, `login.spec.ts`,
  `projects-document.spec.ts`, `projects-literature.spec.ts`, `projects-m2-frontend-contracts.spec.ts`,
  `projects-mappers.spec.ts`, `projects-query-plan.spec.ts`, `reset-password.spec.ts`,
  `sign-up.spec.ts`, `user-settings.spec.ts`, and `tests/utils/privateApi.ts` on 2026-08-03.
- root_cause: the repository-wide Playwright TypeScript baseline predates the current generated DTO
  and test utility layout; these files are outside the Stage 6 M3 production-wiring scope.
- affected_files: the listed legacy frontend test files, test utilities, and Stage 9 frontend type
  verification command.
- blocks_current_stage: `NO`
- blocks_m3_exit_gate: `YES`
- safe_continuation: use `tsconfig.build.json` plus M3 fixture/boundary guards and execute the focused
  M3 Playwright file; do not alter unrelated M2/administration tests during Stage 6.
- resolution: Stage 8 restored the missing random-data utility, migrated stale ProjectPermissions
  fixtures, replaced ES2022-only `Array.at` use, introduced a typed deferred test helper, normalized
  generated-client fetch inputs, preserved the deliberate unknown-status fail-closed assertion with
  a narrow test-only cast, and moved the private test helper onto the current generated client.
  Compiler options and generated DTOs were not weakened or edited.
- focused_verification: `bunx tsc -p frontend/tsconfig.json --noEmit` PASS; targeted Biome check for
  the eight affected test/spec files PASS.
- next_milestone_impact: no runtime impact; the complete frontend type gate is unblocked for the next
  full Exit Gate rerun.

## Stage 6 Changes and Focused Tests

Stage 6 wired the existing M3 frontend contracts to the real generated client and API, added the
single production literature workspace route, and integrated `pdfjs-dist@6.2.108` as a display-only
PDF renderer. No Stage 7 work, Agent runtime, second API client, or client-side verification inference
was added. Because no Open Design delivery exists, the UI remains a minimal functional surface built
from existing RECA primitives and is not recorded as final visual completion.

Modified/created files:

```text
THIRD_PARTY_NOTICES.md
bun.lock
docs/source-research/projects/pdfjs.md
docs/acceptance/M3_OPEN_DESIGN_HANDOFF.md
docs/acceptance/M3_ISSUE_REGISTER.md
frontend/package.json
frontend/src/routes/_layout/projects.$projectId_.literature.tsx
frontend/src/features/literature/M3LiteratureWorkspacePage.tsx
frontend/src/features/literature/m3-literature-workspace.css
frontend/src/features/evidence-matrix/**
frontend/src/features/evidence-analysis/**
frontend/src/features/topic-candidates/**
frontend/tests/projects-m3-evidence.spec.ts
```

Focused verification:

```text
Production TypeScript (`tsconfig.build.json`): PASS
Repository-wide test TypeScript (`tsconfig.json`): FAIL, recorded as M3-ISSUE-0018
Generated-client consistency: PASS
UI ownership boundary guard: PASS (4)
Production mock guard: PASS (6)
M3 fixture contract tests: PASS (5)
Stage 6 Biome formatting: PASS
Focused Playwright (`projects-m3-evidence.spec.ts`): PASS (4)
  deep-link/refresh and trusted normalized highlight: PASS
  pypdf no-coordinate degradation and 390px overflow: PASS
  correction conflict and server-refreshed decision: PASS
  unknown fail-closed and exactly-three no-padding: PASS
Full build, full Playwright and clean-room: NOT RUN by Stage 6 policy
```

Current migration head remains `0013_m3_evidence_matrix`.

## Latest Stage Result

After the earlier Stage 9 attempt, a scoped Stage 8 repair rerun resolved issues 0010, 0011, 0012,
0015 and 0018 with one focused regression group per root cause. No full Exit Gate or clean-room was
rerun. M3 remains blocked by unresolved issues including 0019 and 0022, so completion is not
approved.

```text
M3_EXIT=FAIL
M3_COMPLETION=NOT_APPROVED
STAGE_RESULT=PASS_WITH_ISSUES
NEXT_STAGE_EXECUTED=NO
```

## Focused PostgreSQL Re-verification (2026-08-03)

Docker Desktop and PostgreSQL became available after the initial Stage 9 report. Verification used
an isolated `pgvector/pgvector:0.8.2-pg17` container, a random host port, the `reca_test` database and
an isolated Python 3.14 uv environment outside the repository.

```text
0013 empty upgrade from base: PASS
Repeated upgrade to head: PASS
alembic check: PASS (No new upgrade operations detected)
Random empty database upgrade/repeat/check/downgrade/re-upgrade: PASS (1 test)
Migration graph, metadata and model constraint checks: PASS (18 tests)
M3 PostgreSQL constraint test: FAIL (M3-ISSUE-0022)
```

The existing repository `.venv` was not modified. This focused rerun reduces the environment portion
of `M3-ISSUE-0005`, but clean-room, the complete database suite and real API/browser vertical remain
unverified. M3 Exit remains FAIL.

## Stage 8 Scoped Repair Evidence (2026-08-03)

Only `M3-ISSUE-0010`, `0011`, `0012`, `0015` and `0018` were repaired. `M3-ISSUE-0022` and all other
unlisted OPEN issues were deliberately left unchanged for a separately authorized root-cause group.

```text
0010 AI candidate/post-locator schema boundary: PASS (17 tests)
0011 caller-owned transaction and provenance rollback: PASS (5 PostgreSQL tests)
0012 provider/config/OpenAPI: PASS (16 tests)
0012 LIVE invocation: PASS (1 PostgreSQL test)
0012 provider factory: PASS (5 tests); focused mypy PASS
0015 backend role capability projection: PASS (1 test)
0015 frontend lint, production TypeScript, generated-client guard: PASS
0015 M3 fixture contracts: PASS (5 tests)
0018 repository test TypeScript: PASS
0018 targeted Biome check: PASS (8 files)
Full backend, complete Playwright, clean-room and complete Exit Gate: NOT RUN by Stage 8 policy
STAGE_RESULT=PASS_WITH_ISSUES
NEXT_STAGE_EXECUTED=NO
```

### M3-ISSUE-0024

- ID: `M3-ISSUE-0024`
- stage: `M3-9`
- severity: `HIGH`
- status: `RESOLVED`
- area: `confirmed-question test provenance`
- authoritative_requirement: a CONFIRMED ResearchQuestionVersion requires an approved
  ApprovalRecord and must not be inserted by bypassing the state machine.
- observed_behavior: the first clean-room database suite failed when M3 analysis/vertical fixtures
  directly inserted CONFIRMED versions, poisoning the shared test transaction.
- evidence: first clean-room `backend-database-tests.log`; PostgreSQL
  `enforce_research_question_version_history()` rejection.
- root_cause: Stage 4/7 fixtures predated the database confirmation guard.
- affected_files: `backend/tests/evidence/test_analysis_workflow.py`,
  `backend/tests/integration/test_m3_vertical_demo.py`.
- blocks_current_stage: `NO`
- blocks_m3_exit_gate: `NO`
- safe_continuation: none required after repair.
- resolution: fixtures now create, submit and approve the question through the production Services.
- focused_verification: analysis/provenance group PASS; M3 PostgreSQL vertical PASS; complete
  database suite PASS (`310 passed, 2 skipped`).
- next_milestone_impact: M4 tests should continue using production state transitions for shared RQ
  prerequisites.

### M3-ISSUE-0025

- ID: `M3-ISSUE-0025`
- stage: `M3-9`
- severity: `HIGH`
- status: `RESOLVED`
- area: `recorded model source provenance`
- authoritative_requirement: RECORDED execution identity and all allowed project sources must be
  reconstructable from ModelInvocation before output validation.
- observed_behavior: RECORDED `fixture_id` was dropped, and PromptContract could not distinguish
  required LiteratureRecord from optional EvidenceSpan sources.
- evidence: focused Summary/Topic recording-hash tests and M3 vertical source validation failures.
- root_cause: incomplete RECORDED metadata projection and an overloaded source-type field.
- affected_files: `backend/app/agents/service.py`, `backend/app/agents/prompts.py`, prompt manifest.
- blocks_current_stage: `NO`
- blocks_m3_exit_gate: `NO`
- safe_continuation: none required after repair.
- resolution: persisted RECORDED fixture identity and added explicit `optional_source_types`; summary
  requires LiteratureRecord and permits EvidenceSpan without weakening project/source validation.
- focused_verification: prompt/model invocation, Summary/Topic mismatch tests and M3 vertical PASS.
- next_milestone_impact: M4/M5 model tasks can reuse the required/optional source distinction.

### M3-ISSUE-0026

- ID: `M3-ISSUE-0026`
- stage: `M3-9`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `clean-room test inputs and dirty-worktree guard`
- authoritative_requirement: clean-room must run from isolated inputs without changing or rejecting
  a pre-existing user worktree.
- observed_behavior: the database container lacked the repository golden mount/test environment;
  the final guard treated every pre-existing tracked modification as a clean-room mutation.
- evidence: first and second clean-room summaries and focused guard reproduction.
- root_cause: acceptance script assumed a clean tracked baseline and mounted only backend tests.
- affected_files: `scripts/m0-acceptance.ps1`.
- blocks_current_stage: `NO`
- blocks_m3_exit_gate: `NO`
- safe_continuation: preserve untracked/generated user files and compare tracked snapshots only.
- resolution: mounted golden inputs read-only, set the test environment explicitly, and compare
  before/after tracked status snapshots.
- focused_verification: final complete clean-room PASS with exit code 0, including the tracked-state
  snapshot guard and scoped cleanup.
- next_milestone_impact: M4 clean-room can run safely in the current development worktree.

### M3-ISSUE-0027

- ID: `M3-ISSUE-0027`
- stage: `M3-9`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `verification/retry regression fixtures`
- authoritative_requirement: VERIFIED requires an append-only verification record; assertions must
  not depend on unordered SQL results.
- observed_behavior: retrieval tests directly mutated VERIFIED and retry tests assumed row order.
- evidence: complete backend suite failures before transaction cascade.
- root_cause: older test shortcuts did not reflect the M3 persistence invariants.
- affected_files: `backend/tests/evidence/test_retrieval.py`,
  `backend/tests/evidence/test_extraction_workflow.py`.
- blocks_current_stage: `NO`
- blocks_m3_exit_gate: `NO`
- safe_continuation: none required after repair.
- resolution: verification uses the formal Service and retry assertions use explicit invocation IDs.
- focused_verification: focused group PASS (`4 passed`); complete database suite PASS.
- next_milestone_impact: M4 asynchronous regressions inherit deterministic assertion patterns.

## Stage 9 Final Evidence (2026-08-04)

```text
Migration head: 0013_m3_evidence_matrix
Empty and repeated isolated upgrade: PASS
alembic check: PASS
PostgreSQL backend: PASS (310 passed, 2 skipped)
No-database backend: PASS
Ruff format/check: PASS
Mypy: PASS (89 source files)
Frontend format/lint/build: PASS
Generated client/UI boundary/production mock/M3 fixture guards: PASS
Complete shell Playwright: PASS
Secret scan/Python audit: PASS
Bun audit: PASS_WITH_LOW_ADVISORY (M3-ISSUE-0021)
Clean-room functional and scoped cleanup Gate: PASS (formal entry exit code 0)
Formal real-paper scientific accuracy: NOT MEASURED (M3-ISSUE-0019)
M3_EXIT=PASS
M3_COMPLETION=APPROVED
STAGE_RESULT=PASS_WITH_ISSUES
NEXT_STAGE_EXECUTED=NO
```
