# RECA M3 Implementation Plan

```text
Plan status: FROZEN FOR M3 IMPLEMENTATION
Stage prepared: M3-0
Branch: feat/m2-research-literature
Planning HEAD: 0e3c39dde65feaa8f784fd5fcfb1055cb557bb3c
Migration head: 0012_document_upload
M3 Entry: ALLOWED
Formal M3 business implementation started: NO
```

本计划把本地权威文档、M2 已验收实现、迁移、测试和 Stage 0 Spike 收敛为单一
开发计划。发生事实变化时，以当前仓库和权威优先级为准，并先更新
`M3_ISSUE_REGISTER.md`。

## 1. Frozen M2 Inputs

M3 直接复用，不建立第二套对象或生命周期：

- `ResearchQuestionVersion`、`QueryPlan`；
- `LiteratureSearchRun`、`LiteratureSearchCandidate`、`LiteratureRecord`；
- immutable PDF `Artifact`、`Document`、`DocumentPage`、`DocumentChunk`；
- `Job`、`ProcessingRun`、`ModelInvocation`、`ArtifactRelation`、`AuditLog`；
- project membership/action projection、no-disclosure 404、`If-Match`、
  `Idempotency-Key`、request ID、error envelope；
- generated client、adapter、ViewModel、Container、typed fixture、production mock guard、
  UI boundary guard 和现有 Playwright shell；
- Recorded OpenAlex/GROBID inputs、授权 PDF fixture、Job/ProcessingRun test helpers。

必须保持：Candidate != LiteratureRecord；Document != LiteratureRecord；upload success !=
parse success；Page/Chunk != EvidenceSpan；Recorded/Cache/Degraded/Live 不合并；pypdf
保持 LOW 且不伪造 section/coordinates；未知状态、权限、action 和 retryability fail closed。

## 2. Ownership and Exact Code Locations

### Backend

M3 领域代码统一落在新目录 `backend/app/evidence/`，避免继续扩大现有
`literature/service.py`，同时不引入 Repository 框架或第二个 Router 系统：

```text
backend/app/evidence/__init__.py
backend/app/evidence/schemas.py          # strict public/internal RECA DTOs
backend/app/evidence/locator.py          # deterministic page/text/hash/offset validation
backend/app/evidence/retrieval.py        # project-scoped native chunk retrieval + packing
backend/app/evidence/extraction.py       # LiteratureExtraction Service
backend/app/evidence/review.py           # field correction, verification, decisions, matrix
backend/app/evidence/analysis.py         # summaries and topic generation
backend/app/api/routes/evidence.py       # protocol/auth context/response mapping only
```

共享持久化继续使用 `backend/app/models.py`。迁移固定为当前 head 的单一后继，预期：

```text
backend/app/alembic/versions/0013_m3_evidence_matrix.py
down_revision = 0012_document_upload
```

若 Stage 1 开始时 head 已变化，文件名和 down_revision 以实际唯一 head 更新，并先记
Issue。Router 在 `backend/app/api/main.py` 只注册一次。Worker 继续扩展
`backend/app/workers/jobs.py` 的 handler registry；Celery task 仍是 `reca.execute_job`。

现有 `JobTaskType.LITERATURE_EXTRACT` 和 `LITERATURE_SUMMARIZE` 复用；新增且仅新增
`TOPIC_GENERATE` 以避免把 topic generation 伪装成 summary。不得创建 M3 专用 Job 表、
Celery app 或状态机。

### Backend tests

```text
backend/tests/evidence/test_models.py
backend/tests/evidence/test_schemas.py
backend/tests/evidence/test_locator.py
backend/tests/evidence/test_extraction_workflow.py
backend/tests/evidence/test_retrieval.py
backend/tests/evidence/test_analysis.py
backend/tests/evidence/test_topic_generation.py
backend/tests/api/routes/test_evidence.py
backend/tests/alembic/test_migrations.py       # extend existing migration assertions
backend/tests/alembic/test_migration_runtime.py
```

不得创建第二套 auth fixture、database fixture、Recorded provider 或 E2E framework。

### Frontend

M2 的 `/projects/$projectId/literature` 保持唯一 Literature/PDF 工作台 route；M3 不新增
平行产品壳。Stage 5 冻结 search params：

```text
view=matrix|analysis|topics
documentId
extractionId
fieldId
evidenceSpanId
summaryId
topicRunId
```

精确落点：

```text
frontend/src/features/evidence-matrix/
frontend/src/features/evidence-analysis/
frontend/src/features/topic-candidates/
frontend/src/features/evidence-matrix/ui/PdfEvidenceViewer.tsx
frontend/src/routes/_layout/projects.$projectId_.literature.tsx
frontend/tests/projects-m3-frontend-contracts.spec.ts
frontend/tests/projects-m3-evidence.spec.ts
frontend/tests/m3-stage7-vertical.spec.ts
```

每个 feature 使用现有 `model.ts`、`mappers.ts`、`queries.ts`、`mutations.ts`、
`containers/`、`ui/contracts.ts`、`fixtures/` 模式。`features/literature` 作为 M2/M3 父级
工作台组合层，不复制 API client 或 server state store。

## 3. Persistence Freeze

### Six core entities

1. `LiteratureExtraction`: project/literature/document composite scope、version、schema、
   status、confidence、ModelInvocation、ProcessingRun、lock_version、timestamps。
2. `LiteratureExtractionField`: project/extraction、固定 field_code、原始 model value、
   current projected value、confidence score/level、current EvidenceSpan、confirmation、
   evidence status、lock_version、timestamps；每 extraction/field_code 唯一。
3. `EvidenceSpan`: project/document/page/chunk、真实 source text/context/hash、offset、
   boxes、type、confidence、parser/model provenance、location/review/coverage/read scope、
   invalidation timestamps。
4. `LiteratureDecision`: append-only project/literature decision event、reason、AI advisory、
   `decided_by_user_id`、supersedes、created_at。当前值由确定性最新有效投影获得；
   `LiteratureRecord.current_decision` 仅作事务内维护的缓存投影。
5. `TopicGenerationRun`: project/RQ version/evidence summary、constraints、ModelInvocation、
   Job/ProcessingRun、status、created_at。
6. `TopicCandidate`: project/run、order 1..3、AI Schema 全部结构字段、status、created_at；
   `(run_id, candidate_order)` 唯一。

### Required supporting persistence

- `LiteratureExtractionFieldRevision`: append-only；保存 field/project、revision number、
  old/new text、old/new JSON、old/new EvidenceSpan、old/new confirmation/evidence status、
  actor、reason、source model invocation/AI version、created_at。
- `EvidenceSpanVerificationRecord`: append-only；保存 span/project、actor type/id、目标
  location status、read scope、reviewed pages、note、当时 source hash、created_at。
- `TopicCandidateEvidence`: candidate/project，恰好一个 literature_record_id 或
  evidence_span_id，relation type、explanation；用于强制来源绑定。
- `EvidenceSetSummary`: 建独立支持表以满足稳定 `summary_id` GET；保存 project、Job/
  ProcessingRun/ModelInvocation、included literature snapshot、scope statement、严格结果
  JSON、status、created_at。结果 JSON 必须通过注册 Schema，来源 ID 仍由 Service/DB
  验证；它不是任意 JSON 状态仓库。

所有跨对象关系使用 composite FK 或同事务 Service 校验 `project_id`。历史对象
`ondelete=RESTRICT`；删除/失效不级联抹除科研历史。核心对象有 UUID 和 created_at；
可编辑投影有 lock_version。

## 4. Contract Freeze

### Fixed field and confidence enums

```text
LiteratureFieldCode:
TITLE AUTHORS YEAR RESEARCH_OBJECT SAMPLE_SIZE CORE_VARIABLES
RESEARCH_DESIGN ANALYSIS_METHOD MAIN_CONCLUSION LIMITATION

ConfidenceLevel:
HIGH MEDIUM LOW UNKNOWN
```

AI Schema 的 0..1 `confidence` 原值保存为 `confidence_score`；Domain 同时保存由版本化、
确定性阈值映射得到的 `confidence_level`。不得把模型分数解释为统计概率。

### Extraction and field enums

```text
LiteratureExtractionStatus:
DRAFT EXTRACTING NEEDS_REVIEW CONFIRMED SUPERSEDED INVALIDATED FAILED

FieldConfirmationStatus:
UNREVIEWED CONFIRMED REJECTED

FieldEvidenceStatus:
UNASSESSED LOCATED LOCATION_UNCERTAIN NO_LOCATED_EVIDENCE
```

修正是 revision event，不占用 confirmation 枚举；修正后可保持 `UNREVIEWED` 或由用户
显式设为 `CONFIRMED/REJECTED`。没有真实候选片段时只能
`NO_LOCATED_EVIDENCE` 且 `evidence_span_id=null`。有真实候选但唯一定位不足时才允许
`LOCATION_UNCERTAIN`。

### Evidence enums

```text
EvidenceType:
FIELD_SUPPORT CLAIM_SUPPORT CLAIM_CONTRADICTION METHOD_DESCRIPTION
SAMPLE_DESCRIPTION LIMITATION OTHER

LocationVerificationStatus:
EXTRACTED LOCATED VERIFIED LOCATION_UNCERTAIN

EvidenceReviewStatus:
UNREVIEWED REVIEWED CONFIRMED REJECTED

ParserCoverage:
UNKNOWN PARTIAL_TEXT FULL_TEXT

UserDeclaredReadScope:
UNKNOWN ABSTRACT SECTIONS FULL_TEXT_DECLARED
```

`ParserCoverage` 是机器覆盖，`UserDeclaredReadScope` 是用户声明，二者互不推断。
`VERIFIED` 只能由 verification record 触发，且需页文本、页码、真实 source text/hash
和可验证定位信息；pypdf 无坐标不得伪造 boxes。

### Decision and topic enums

```text
LiteratureDecisionStatus: INCLUDED EXCLUDED UNCERTAIN
LiteratureDecisionReason:
RELEVANT_OBJECT_AND_METHOD
OBJECT_MISMATCH VARIABLE_MISMATCH METHOD_MISMATCH TYPE_MISMATCH YEAR_MISMATCH
DUPLICATE FULL_TEXT_UNAVAILABLE QUALITY_ISSUE OTHER

TopicCandidateStatus: PROPOSED SHORTLISTED ADOPTED REJECTED EXPIRED
TopicEvidenceRelation: BASIS SUPPORT CONTRADICTION LIMITATION
```

AI/ASReview 只能写 advisory fields/strict payload，不能填写 `decided_by_user_id` 或创建
最终 decision。

### Formal endpoints

只实现 API 子契约名称：

```text
POST /api/v1/documents/{document_id}/literature-extractions
GET  /api/v1/literature-extractions/{extraction_id}
PATCH /api/v1/literature-extraction-fields/{field_id}
POST /api/v1/documents/{document_id}/evidence-spans
GET  /api/v1/evidence-spans/{evidence_span_id}
POST /api/v1/evidence-spans/{evidence_span_id}/verification-records
POST /api/v1/literature/{literature_id}/decisions
GET  /api/v1/literature/{literature_id}/decisions
GET  /api/v1/projects/{project_id}/literature-matrix
POST /api/v1/projects/{project_id}/evidence-search
POST /api/v1/projects/{project_id}/evidence-set-summaries
GET  /api/v1/evidence-set-summaries/{summary_id}
POST /api/v1/projects/{project_id}/topic-generation-runs
```

decision endpoint 由 API 16.11-16.12 冻结为既有 `/literature` namespace；不实现
`/literature-records` 别名。API 17.9A 已冻结 `/evidence-spans/{id}` namespace，而当前阶段
明确要求单项读取，因此 `M3-ISSUE-0008` 将最小读取路径冻结为
`GET /api/v1/evidence-spans/{id}`。Stage 3 仍需按全文复核 operation ID，不创建语义重复
端点。所有写操作处理 action permission、同项目、
`If-Match`/lock version、`Idempotency-Key`、Audit、replay/conflict。非成员读取和枚举 ID
攻击返回 no-disclosure 404。

## 5. Candidate-to-Evidence Boundary

稳定内部/响应边界保持 `EvidenceCandidateDTO`：

```text
candidate_id, project_id, literature_record_id, document_id, chunk_id,
page_number, source_text/quoted_text, source_text_hash, retrieval_run_id,
keyword_score, vector_score, fused_rank, rerank_score, limitations,
validated_evidence_span_id/evidence_span_id
```

流程唯一为：

```text
project-scoped DocumentChunk candidate
-> reload immutable Document, DocumentPage and Chunk
-> exact page/source substring validation
-> server-computed SHA-256 validation
-> offset and optional coordinate validation
-> create EvidenceSpan, or record no span with an explicit limitation
```

PaperQA Context、向量距离、PDF.js selection/DOM offset、TEI node 和模型引用都不是证据
真相。`source_text` 必须存在于当前页文本。没有真实候选片段时不创建 Span；真实片段
存在但定位不足时才可创建/保持 `LOCATION_UNCERTAIN`，并禁止升级 `VERIFIED`。

## 6. Job, Provenance, Artifact and Audit Reuse

- 创建抽取/summary/topic 请求时先持久化 domain run + existing Job；同步响应返回真实 Job，
  不返回 optimistic success 或仅靠 HTTP 202 推断业务完成。
- Worker claim 创建新 `ProcessingRun`；retry 复用 Job、新建 ProcessingRun；duplicate
  delivery 不重复正式结果。
- 每次模型调用创建独立 `ModelInvocation`，记录 Prompt/schema hash、requested/max/effective
  access、输入来源和失败；PDF 是不可信内容，模型只接收最小必要 page/chunk 片段。
- 原始 PDF 和 GROBID TEI/模型输出继续使用 immutable Artifact；候选 packing 可保存为
  versioned JSON Artifact 或 ProcessingRun output，不能成为第二事实源。
- 所有状态转换、field revision、verification、decision、failure、retry、invalidation
  追加 AuditLog。Router 不直接写数据库。
- 不接入 Agent runtime、Tool runtime 或 Agent session；M8 边界保持不变。

## 7. Stage 0 Technology Decisions

### pgvector / pgvector-python

Stage 0 isolated compile spike passed with `pgvector-python 0.5.0`, SQLModel 0.0.39,
SQLAlchemy 2.0.51 and Psycopg 3.3.4. Generated PostgreSQL SQL contains mandatory
`WHERE project_id = ...` before exact cosine `ORDER BY embedding <=> ...`.

Decision: **do not add pgvector-python in Stage 0**. M3 Competition Core starts with native
project-scoped text/DocumentChunk retrieval because embeddings have no frozen model/dimension/
lineage production pipeline yet. Existing nullable `DocumentChunk.embedding` remains untouched.
If Stage 4 measurements require vector retrieval, adopt 0.5.0 only after exact Compose DB,
dimension, migration, cross-project and `EXPLAIN` tests; HNSW remains deferred.

### Native retrieval and PaperQA2

Baseline is PostgreSQL/project filter + document filter + deterministic lexical/text ranking over
existing chunks, followed by bounded deduplication/source-preserving packing. The Stage 0 spike
preserved project scope, returned no-evidence explicitly and created zero EvidenceSpan rows.

Decision: **do not install PaperQA2 runtime**. Reuse only design ideas: bounded packing,
deduplication, source keys, conflict preservation, no-evidence behavior and focused test patterns.
Any later copied code/Prompt requires exact upstream path/Commit, Apache-2.0 attribution and
THIRD_PARTY_NOTICES in the adoption stage.

### ASReview

Decision: **not adopted for Competition Core**. It remains optional advice/P1. Manual
LiteratureDecision is always available and cannot be blocked by missing seeds/model/runtime.
Any later ranking uses confirmed decisions only, fixed seed/version and a read-only recommendation
payload with no decision write path.

### PDF.js

Isolated browser build passed for `pdfjs-dist 6.2.108` + Vite 8.1.5 and emitted a matching
`pdf.worker.min-*.mjs` asset. The modern build expects browser DOM APIs and is not imported in
backend/Node SSR paths.

Decision: version/path is approved for Stage 6 browser adoption, but **not installed in Stage 0**.
Stage 6 will add the exact dependency, lock change, Apache-2.0 notice/source/fallback record and
focused browser tests in the same change. Use `pdfjs-dist` display API plus matching
`pdf.worker.min.mjs?url`; PDF.js is display/interaction only.

### TanStack Table

The repository already locks stable `@tanstack/react-table` 8.21.3. A current Bun/React headless
construction smoke passed with stable row IDs. Reuse directly; do not adopt v9 beta or create a
table state store that acts as business truth.

## 8. Open Design and Codex Handoff

Codex owns `backend/**`, OpenAPI, `frontend/src/api/generated/**` generation,
`frontend/src/api/adapter/**`, routes/search params, feature model/mappers/queries/mutations/
containers, typed fixtures and integration/E2E tests.

Open Design owns pure `ui/**`, CSS, responsive composition and design-preview presentation after
Stage 5 freezes `ViewModel`, Props, Events and fixtures. Open Design must not call APIs, change
route semantics, modify generated/adapter/business model files, infer permission/state, or make
fixture success look like production success. PDF viewer events emit selection/jump intent only;
backend validation alone creates/validates EvidenceSpan.

Stage 5 creates `docs/acceptance/M3_OPEN_DESIGN_HANDOFF.md` and marks readiness explicitly.
Stage 6 does not invent a replacement visual system if Open Design output is absent.

## 9. Stage Dependency Plan

### Stage 1 - models and migration

Implement all persistence in section 3 and frozen enums/constraints in section 4 in one successor
migration. Focused tests: metadata/migration agreement, empty/repeated upgrade, `alembic check`,
Check/Unique/composite FK/cross-project negatives, append-only history/current projection.

### Stage 2 - locator and extraction Worker

Implement strict ten-field schema, `EvidenceCandidateDTO`, minimal page/chunk context, deterministic
locator, extraction transitions, Job/ProcessingRun/ModelInvocation/Artifact/Audit. Focused tests:
correct/wrong page, text, hash, offset, duplicate text, cross-project, pypdf LOW, no evidence,
model fabrication, failure/retry/duplicate delivery.

### Stage 3 - core API and generated client

Implement extraction, field revision/confirmation, manual Span, verification, decision history and
matrix endpoints. Router remains mapping-only. Run role/no-disclosure, If-Match, idempotency,
history, verification refusal/upgrade, decision current projection, matrix pagination/filter,
OpenAPI generation and generated-client checks.

### Stage 4 - retrieval, summaries and exactly three topics

Implement native retrieval first. Summary input is server-intersected with current INCLUDED
decisions and must retain counterexamples/scope limitations. Topic result must contain exactly
three unique candidates and valid LiteratureRecord/EvidenceSpan associations. Focused tests cover
scope, empty evidence, invalid source IDs, cautious language, count != 3, duplicates, provenance,
idempotency and failure.

### Stage 5 - frontend contracts and Open Design handoff

Create three feature boundaries, ViewModels, mappings, queries/mutations/containers, typed fixtures,
route/search contract and handoff. Run TypeScript/build minimum, generated-client, UI boundary,
production mock and fixture contract tests; no full Playwright.

### Stage 6 - production UI and PDF.js

Adopt approved PDF.js dependency with license/lock/fallback record, connect generated client to the
existing literature route, implement server-authoritative refresh/deep links, table/PDF workspace,
safe no-coordinate degradation, conflict/permission/unknown states and exactly-three display.
Run only high-value desktop/mobile focused Playwright.

### Stage 7 - golden set and vertical evidence

Create authorized 10-20 paper golden material or documented minimum reusable subset, annotations,
real vertical M2->M3 chain and issue collection. Do not broadly fix business defects here.

### Stage 8 - centralized repair

Resolve all BLOCKER/HIGH and grouped root causes from the Issue Register; add focused regression
per root cause. Deferred LOW must retain safe degradation and next milestone impact.

### Stage 9 - M3 Exit Gate

Run complete backend, migration, OpenAPI/client, frontend, Playwright, clean-room and supply-chain
gates. Hard metrics include 100% real-PDF evidence, >=90% page accuracy, >=95% correct empty
evidence, zero fabricated EvidenceSpan/cross-project source, 100% user final decisions, included-only
summary with counterexamples and exactly three sourced topics. Only Stage 9 may declare M3 complete.

## 10. Stage 0 Completion Record

```text
Created/modified:
- docs/acceptance/M3_ISSUE_REGISTER.md
- docs/acceptance/M3_IMPLEMENTATION_PLAN.md

Focused checks:
- git baseline/diff/untracked inventory: PASS
- migration revision graph: PASS (0012_document_upload)
- pgvector-python isolated SQLModel/SQL compile: PASS
- real PostgreSQL pgvector round-trip: NOT RUN (M3-ISSUE-0005)
- native retrieval/packing spike: PASS
- pdfjs-dist/Vite worker asset build: PASS
- TanStack Table current-stack construction: PASS

Dependency/lock/NOTICE changes: none
Formal M3 business code, migration, API, generated client or UI: not started
Next stage executed: NO
```
