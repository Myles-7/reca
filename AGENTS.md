# AGENTS.md

> 研证链 AI（RECA）仓库级智能体开发规范
> Research Evidence Chain Agent
> 适用于 Codex、代码智能体、自动化重构工具与参与本仓库开发的人工贡献者

---

## 文档信息

| 项目     | 内容                                                                                                                                                                                                   |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 文档名称   | `AGENTS.md`                                                                                                                                                                                          |
| 文档版本   | 1.0.0                                                                                                                                                                                                |
| 适用项目版本 | RECA 0.1 Competition Edition                                                                                                                                                                         |
| 文档状态   | Approved                                                                                                                                                                                             |
| 文档位置   | 仓库根目录                                                                                                                                                                                                |
| 主要读者   | Codex、代码智能体、开发人员、测试人员、代码审查人员                                                                                                                                                                         |
| 负责人    | RECA Team                                                                                                                                                                                            |
| 最后更新时间 | 2026-07-29                                                                                                                                                                                           |
| 上位文档   | 无                                                                                                                                                                                                    |
| 关联文档   | `README.md`、`docs/PRODUCT_REQUIREMENTS.md`、`docs/ARCHITECTURE.md`、`docs/DATA_MODEL_AND_WORKFLOW.md`、`docs/API_AI_TOOL_CONTRACTS.md`、`docs/TEST_AND_ACCEPTANCE.md`、`docs/SECURITY_AND_OPEN_SOURCE.md` |

---

# 1. 文件目的

本文件用于约束所有在 RECA 仓库中执行开发任务的代码智能体。

任何智能体在修改代码前，必须先理解：

1. RECA 是什么；
2. 当前比赛版本做什么；
3. 哪些需求已经冻结；
4. 哪些技术选型已经冻结；
5. 哪些领域对象不可变；
6. 哪些操作必须经过用户审批；
7. 哪些结果必须由确定性程序产生；
8. 哪些文件和数据绝不能覆盖；
9. 哪些模块可以互相依赖；
10. 一个开发任务达到什么条件才算完成。

本文件不是普通代码风格说明。

它同时定义：

* 仓库工作协议；
* 架构保护规则；
* 安全保护规则；
* 科研可信保护规则；
* 测试和发布门禁；
* Codex 的任务执行方式；
* 禁止行为；
* 交付说明格式。

违反本文件中的强制规则，即使代码可以运行，也不能视为有效实现。

---

# 2. 项目定位

## 2.1 项目名称

```text
研证链 AI
RECA
Research Evidence Chain Agent
```

## 2.2 产品定位

RECA 是一个面向高校学生和教师的可信科研工作流智能体。

它将以下过程连接为统一、可追踪、可复现的科研链路：

```text
研究想法
→ 结构化研究问题
→ 真实文献检索
→ PDF原文证据
→ 文献证据矩阵
→ 当前证据集合分析
→ 候选研究问题
→ 数据身份证与版本
→ 数据质量检查
→ 人工批准的数据处理
→ 确定性统计分析
→ 科研图表
→ DOCX论文质控
→ Claim证据链
→ 科研复现包
```

## 2.3 产品核心原则

所有实现必须遵守：

> AI 负责建议，确定性工具负责计算，用户负责确认。

对应边界：

| 能力         |     AI |   确定性程序 |   用户 |
| ---------- | -----: | ------: | ---: |
| 研究问题结构化    |      是 |      校验 |   确认 |
| 查询词生成      |      是 |    转换查询 |   调整 |
| 真实文献检索     |      否 |       是 |   选择 |
| PDF 字段抽取   |      是 |   解析和定位 |   修正 |
| 文献纳入决策     |     推荐 |    保存历史 | 最终决定 |
| 数据质量识别     |    可解释 |       是 |   确认 |
| 数据处理       |   生成建议 |      执行 |   批准 |
| 统计方法       |     推荐 |   校验与计算 |   批准 |
| 正式统计数字     |      否 |       是 |   查看 |
| 科研图表       |   推荐类型 |      渲染 |   确认 |
| 论文问题       | 辅助语义审核 | 数字和格式检查 |   采纳 |
| Claim 证据审核 |      是 |    来源校验 |   确认 |

---

# 3. 指令优先级

智能体必须按照以下顺序处理约束：

1. 当前用户明确要求；
2. 本文件 `AGENTS.md`；
3. `docs/PRODUCT_REQUIREMENTS.md`；
4. `docs/ARCHITECTURE.md`；
5. `docs/DATA_MODEL_AND_WORKFLOW.md`；
6. `docs/API_AI_TOOL_CONTRACTS.md`；
7. `docs/TEST_AND_ACCEPTANCE.md`；
8. `docs/SECURITY_AND_OPEN_SOURCE.md`；
9. 当前代码与测试；
10. 历史设计文档和归档材料。

若代码与正式文档冲突，不得默认以代码为准。

应先判断：

* 代码未完成；
* 代码过时；
* 文档过时；
* 迁移中；
* 或存在明确架构决策变更。

无法判断时，选择不破坏现有数据和安全边界的实现方式，并在交付说明中明确记录冲突。

---

# 4. 修改前必须阅读的文件

## 4.1 所有任务

至少阅读：

```text
AGENTS.md
README.md
```

## 4.2 后端任务

额外阅读：

```text
docs/ARCHITECTURE.md
docs/DATA_MODEL_AND_WORKFLOW.md
docs/API_AI_TOOL_CONTRACTS.md
docs/TEST_AND_ACCEPTANCE.md
docs/SECURITY_AND_OPEN_SOURCE.md
```

## 4.3 前端任务

额外阅读：

```text
docs/PRODUCT_REQUIREMENTS.md
docs/API_AI_TOOL_CONTRACTS.md
docs/TEST_AND_ACCEPTANCE.md
```

涉及权限、上传、下载或敏感数据时，还需阅读：

```text
docs/SECURITY_AND_OPEN_SOURCE.md
```

## 4.4 AI 或 Agent 任务

必须阅读：

```text
docs/API_AI_TOOL_CONTRACTS.md
docs/DATA_MODEL_AND_WORKFLOW.md
docs/SECURITY_AND_OPEN_SOURCE.md
docs/TEST_AND_ACCEPTANCE.md
```

## 4.5 数据库任务

必须阅读：

```text
docs/DATA_MODEL_AND_WORKFLOW.md
docs/ARCHITECTURE.md
docs/SECURITY_AND_OPEN_SOURCE.md
```

## 4.6 测试任务

必须阅读：

```text
docs/TEST_AND_ACCEPTANCE.md
docs/API_AI_TOOL_CONTRACTS.md
```

## 4.7 第三方依赖任务

必须阅读：

```text
docs/SECURITY_AND_OPEN_SOURCE.md
THIRD_PARTY_NOTICES.md
```

---

# 5. 已冻结的技术决策

除非用户明确要求修改架构文档，否则不得擅自替换以下选型。

## 5.1 前端

```text
React
Vite
TypeScript
Tailwind CSS
TanStack Table
PDF.js
React Flow
Playwright
```

不得擅自替换为：

* Next.js；
* Vue；
* Angular；
* Svelte；
* 另一套完整 UI 技术栈。

## 5.2 后端

```text
FastAPI
Pydantic
SQLModel
Alembic
Celery
```

不得擅自替换为：

* Django；
* Flask；
* NestJS；
* Spring；
* 多语言后端。

## 5.3 数据和存储

```text
PostgreSQL
pgvector
MinIO / S3 Adapter
Valkey
```

不得在 P0 擅自增加：

* MongoDB；
* Elasticsearch；
* Neo4j；
* Milvus；
* Kafka；
* 独立向量数据库。

## 5.4 科研处理

```text
GROBID
pypdf
pandas
NumPy
Pandera
SciPy
statsmodels
Matplotlib
python-docx
lxml
```

## 5.5 Agent

```text
单科研总控 Agent
白名单工具
结构化 Schema
Guardrail
ToolCall 审计
ApprovalRecord
```

不得改成：

* 自由多 Agent 对话；
* Agent 自行审批；
* Agent 任意代码执行；
* Agent 直接写数据库。

## 5.6 部署

```text
Docker Compose
模块化单体
一个 FastAPI API
一个或多个同代码 Worker
有限独立服务
```

P0 不引入：

* Kubernetes；
* 服务网格；
* 大量微服务；
* 分布式事务平台。

---

# 6. P0 功能范围

智能体应优先实现以下 P0 主链。

## 6.1 研究问题

* 自然语言输入；
* 结构化字段；
* 版本；
* 用户确认。

## 6.2 文献

* OpenAlex/PyAlex 真实检索；
* 查询规划；
* DOI 验证；
* 去重；
* PDF 上传；
* GROBID 解析；
* pypdf 回退；
* 十字段文献矩阵；
* EvidenceSpan；
* 纳入、排除、待确认；
* 当前证据集合内的共识、争议和证据不足。

## 6.3 候选研究问题

* 固定 3 个候选；
* 文献依据；
* 数据要求；
* 方法难度；
* 风险；
* 用户采用。

## 6.4 数据

* CSV；
* XLSX；
* 数据身份证；
* DatasetVersion；
* 字段字典；
* 数据质量；
* CleaningPlan；
* 预览；
* ApprovalRecord；
* DataTransformation；
* 新版本。

## 6.5 统计

仅支持：

```text
DESCRIPTIVE_STATISTICS
INDEPENDENT_TWO_GROUP
PAIRED_TWO_GROUP
PEARSON_CORRELATION
SPEARMAN_CORRELATION
SIMPLE_LINEAR_REGRESSION
```

必须包含统计前提检查。

## 6.6 图表

仅支持：

```text
HISTOGRAM
BOXPLOT
SCATTER
GROUP_COMPARISON
CORRELATION_MATRIX
```

## 6.7 论文

仅支持 DOCX。

检查：

* 引用；
* 数字；
* 因果语言；
* 样本外推；
* 术语；
* 基础格式。

## 6.8 证据链

* Claim；
* ClaimEvidenceLink；
* AuditResult；
* React Flow 展示；
* 上游失效传播。

## 6.9 导出

* ReproPackage；
* Manifest；
* 文件哈希；
* 数据和许可证检查；
* 复现说明。

---

# 7. 明确不做的内容

除非用户明确调整 P0 范围，否则不得投入大量时间实现：

* 自建学术搜索引擎；
* 自训练 PDF 模型；
* 完整查重系统；
* 自动生成完整论文；
* 任意统计方法；
* 多元复杂回归；
* 结构方程模型；
* 深度学习训练平台；
* 实时多人编辑；
* 图数据库；
* 大规模微服务；
* 任意代码执行；
* 用户自定义 Python；
* 在线 Notebook；
* 付费论文绕过；
* 自动伦理审批；
* 自动导师决策。

若用户提出范围外功能，应：

1. 明确标记为 P1 或非目标；
2. 不破坏 P0；
3. 提供最小接口预留；
4. 不提前构建复杂基础设施。

---

# 8. 仓库结构约束

目标结构：

```text
reca/
├── README.md
├── AGENTS.md
├── LICENSE
├── SECURITY.md
├── THIRD_PARTY_NOTICES.md
├── docker-compose.yml
├── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── routes/
│   │   ├── features/
│   │   ├── components/
│   │   ├── api/
│   │   ├── hooks/
│   │   ├── schemas/
│   │   ├── state/
│   │   └── vendor-integrations/
│   └── tests/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── domain/
│   │   ├── modules/
│   │   ├── services/
│   │   ├── adapters/
│   │   ├── tools/
│   │   ├── agents/
│   │   ├── quality_rules/
│   │   ├── chart_templates/
│   │   ├── manuscript_rules/
│   │   ├── ooxml_helpers/
│   │   ├── workers/
│   │   └── shared/
│   ├── migrations/
│   └── tests/
│
├── tests/
│   ├── fixtures/
│   ├── golden/
│   ├── integration/
│   └── e2e/
│
├── docs/
├── vendor/
└── scripts/
```

## 8.1 禁止随意增加顶级目录

新增顶级目录前必须说明：

* 目录职责；
* 为什么现有目录不能容纳；
* 对构建和部署的影响；
* 是否需要更新架构文档。

## 8.2 禁止模糊目录

不得创建：

```text
backend/app/utils_everything/
backend/app/common_business/
backend/app/misc/
frontend/src/helpers/all.ts
```

## 8.3 `shared/` 使用限制

`shared/` 只能包含：

* 通用 ID；
* 时间工具；
* 哈希；
* 分页；
* 通用错误；
* 通用 DTO；
* 日志上下文。

不得把具体业务逻辑放入 `shared/`。

---

# 9. 模块边界

后端核心模块：

```text
projects
research_questions
artifacts
literature
datasets
analysis
figures
manuscripts
evidence
approvals
jobs
agents
exports
```

## 9.1 模块内建议结构

```text
module/
├── models.py
├── schemas.py
├── repository.py
├── service.py
├── policies.py
├── state_machine.py
├── router.py
└── tests/
```

不要求机械生成空文件。

只有存在清晰职责时才创建。

## 9.2 依赖方向

推荐：

```text
API
→ Application Service
→ Domain Policy
→ Repository / Adapter
→ Database / External Service
```

## 9.3 禁止依赖

禁止：

* Router 直接执行统计；
* Router 直接调用 PyAlex；
* Router 直接调用 MinIO SDK；
* Router 直接解析 PDF；
* Agent Tool 直接操作数据库 Session；
* Statistics 模块调用模型；
* Frontend 自行推断证据关系；
* Figure 模块修改 AnalysisResult；
* Manuscript 模块覆盖原 DOCX；
* Adapter 返回第三方原始对象给前端。

## 9.4 跨模块调用

跨模块逻辑优先通过：

* Application Service；
* Protocol；
* Query Service；
* 领域事件；
* 共享对象 ID。

不得通过随意导入另一个模块的 Repository 绕过业务规则。

---

# 10. 领域模型保护规则

## 10.1 项目作用域

所有核心科研对象必须属于 `ResearchProject`。

查询核心对象时必须校验：

```text
resource.project_id == authorized_project_id
```

## 10.2 逻辑对象与版本对象分离

必须保留：

```text
ResearchQuestion / ResearchQuestionVersion
Dataset / DatasetVersion
Manuscript / ManuscriptVersion
```

不得为简化实现而将版本字段直接覆盖在逻辑对象上。

## 10.3 原始对象不可变

以下内容不可原地修改：

* 原始 Artifact；
* Original DatasetVersion；
* Original ManuscriptVersion；
* 完成的 AnalysisRun；
* AnalysisResult；
* 已决策 ApprovalRecord；
* 已完成 ToolCall；
* 已完成 ModelInvocation；
* ReproPackage。

## 10.4 计划与执行分离

必须区分：

```text
CleaningPlan
DataTransformation
DatasetVersion
```

必须区分：

```text
AnalysisPlan
AnalysisRun
AnalysisResult
```

不得使用一个状态字段和一个 JSON 同时代替全部对象。

## 10.5 失效不删除

统计或证据错误通常使用：

```text
INVALIDATED
```

而不是删除。

必须保留：

* 原始结果；
* 失效原因；
* 失效人；
* 失效时间；
* 下游影响。

## 10.6 用户确认

用户确认必须保存为：

```text
ApprovalRecord
```

聊天消息、前端布尔值和 Agent 文本都不能代替审批记录。

---

# 11. 数据库开发规则

## 11.1 模型修改

修改数据库模型时，必须同时检查：

* SQLModel；
* Pydantic Schema；
* Alembic Migration；
* Repository；
* Service；
* API；
* 前端类型；
* 测试；
* 文档。

## 11.2 迁移要求

任何数据库结构修改必须创建 Alembic Migration。

禁止：

* 只修改模型不迁移；
* 依赖开发数据库手工改表；
* 在启动代码中执行临时 ALTER TABLE；
* 为修复测试直接删除迁移历史。

## 11.3 新增非空字段

推荐流程：

1. 新增可空字段；
2. 回填；
3. 增加约束；
4. 更新模型；
5. 更新测试。

## 11.4 枚举

修改枚举时同步更新：

* 数据库；
* Domain Enum；
* API Schema；
* 前端；
* 状态机；
* 契约测试；
* 文档。

## 11.5 外键删除行为

核心领域对象默认使用：

```text
RESTRICT
NO ACTION
```

不使用大规模级联删除。

## 11.6 JSONB

JSONB 只能保存：

* 可变参数；
* 扩展信息；
* 第三方摘要；
* 方法特定结果。

不得用 JSONB 逃避正式建模核心关系。

## 11.7 索引

新增高频查询必须考虑：

* `project_id`；
* `status`；
* `created_at`；
* 业务外键；
* 唯一性；
* 幂等键。

---

# 12. API 开发规则

## 12.1 API 前缀

```text
/api/v1
```

## 12.2 契约优先

实现前先确认：

```text
docs/API_AI_TOOL_CONTRACTS.md
```

若端点未定义，先判断：

* 是否遗漏；
* 是否可复用已有端点；
* 是否需要正式扩展契约。

不得随意创造重复端点。

## 12.3 Router 职责

Router 只负责：

* 身份认证；
* 请求 Schema；
* 权限；
* 调用 Service；
* HTTP 状态；
* DTO。

不得包含复杂业务计算。

## 12.4 公共错误

使用统一错误结构。

不得返回：

```json
{"detail": "something went wrong"}
```

作为正式业务错误。

必须包含：

* code；
* message；
* request_id；
* retryable；
* 必要 details。

## 12.5 权限

所有资源 API 必须校验：

1. 用户；
2. 项目成员；
3. 资源项目归属；
4. 操作权限；
5. 项目状态；
6. 对象状态。

## 12.6 幂等

涉及异步或正式副作用的接口必须支持：

```http
Idempotency-Key
```

## 12.7 乐观锁

可编辑业务对象使用：

```http
If-Match
```

冲突返回：

```text
409 RESOURCE_VERSION_CONFLICT
```

## 12.8 分页

列表接口统一使用：

```text
page
page_size
sort
order
```

不得在同一项目中混用多个分页协议。

## 12.9 前端类型

前端 API Client 应从 OpenAPI 生成。

不得手工维护与后端冲突的重复类型。

---

# 13. 异步任务规则

## 13.1 必须异步的任务

* PDF 解析；
* 文献字段抽取；
* Embedding；
* 批量总结；
* 数据质量；
* 数据转换；
* 统计运行；
* 图表生成；
* DOCX 检查；
* 复现包导出。

## 13.2 API 不执行长任务

API 应：

1. 校验；
2. 创建业务对象；
3. 创建 Job；
4. 提交队列；
5. 返回 202。

## 13.3 Job 与 ProcessingRun 分离

Job 负责：

* 调度；
* 进度；
* 重试；
* 取消。

ProcessingRun 负责：

* 输入；
* 参数；
* 引擎；
* 输出；
* 业务运行。

## 13.4 幂等

任务幂等键至少包含：

```text
task_type
resource_id
input_version
parameters_hash
```

## 13.5 Worker 重新校验

Worker 不信任队列消息。

执行前重新校验：

* 对象存在；
* 项目一致；
* 状态允许；
* Approval 有效；
* 输入版本有效；
* 幂等结果不存在。

## 13.6 失败处理

失败时：

* 不创建正式结果；
* 不标记 COMPLETED；
* 保留错误码；
* 保留日志；
* 保留原始文件；
* 标记是否可重试。

## 13.7 取消

取消必须是协作式。

不得强制中止数据库事务后留下半成品。

---

# 14. 文件与 Artifact 规则

## 14.1 所有文件使用 Artifact

包括：

* PDF；
* CSV；
* XLSX；
* DOCX；
* PNG；
* SVG；
* 图表 PDF；
* 分析代码；
* 日志；
* JSON；
* ZIP；
* Manifest。

## 14.2 原文件不可覆盖

任何“修改”必须：

```text
原 Artifact
→ 处理
→ 新 Artifact
```

## 14.3 文件路径

对象存储键由系统生成。

不得使用用户文件名拼接真实路径。

## 14.4 上传验证

至少检查：

* 大小；
* 扩展名；
* MIME；
* 文件头；
* 实际解析；
* 哈希。

## 14.5 临时文件

必须：

* 使用临时目录；
* 任务完成清理；
* 失败可补偿清理；
* 不写入仓库；
* 不写入固定公共目录。

## 14.6 DOCX 和 ZIP

必须防止：

* ZIP Slip；
* 压缩炸弹；
* 外部关系自动访问；
* 宏执行。

## 14.7 CSV 导出

注意公式注入。

不可信文本以 `= + - @` 开头时，应采用明确的安全策略。

---

# 15. 文献模块规则

## 15.1 文献真实性

LiteratureRecord 只能来自：

* OpenAlex；
* DOI 导入；
* 用户上传并人工录入；
* 明确缓存；
* 手工元数据。

AI 不得生成正式文献记录。

## 15.2 DOI

必须：

* 规范化；
* 去除 URL 前缀；
* 去除 `doi:`；
* 小写比较；
* 同项目去重。

## 15.3 PDF 与元数据分离

必须保留：

```text
LiteratureRecord
Document
Artifact
```

三个概念。

不得把 PDF 文件直接等同于文献元数据。

## 15.4 解析器

主解析：

```text
GROBID
```

回退：

```text
pypdf
```

回退后必须标记低置信度。

## 15.5 EvidenceSpan

EvidenceSpan 必须来自真实文档。

至少保存：

* document_id；
* page_number；
* source_text；
* section；
* 坐标或字符范围；
* 置信度；
* 确认状态。

不得让模型生成不存在的原文。

## 15.6 文献矩阵

P0 固定十字段：

```text
TITLE
AUTHORS
YEAR
RESEARCH_OBJECT
SAMPLE_SIZE
CORE_VARIABLES
RESEARCH_DESIGN
ANALYSIS_METHOD
MAIN_CONCLUSION
LIMITATION
```

新增字段不得破坏固定字段兼容性。

## 15.7 当前证据范围

总结必须明确：

```text
基于当前纳入的文献集合
```

不得写：

* 学术界从未研究；
* 已证明没有研究；
* 所有研究一致；
* 整个领域已经形成共识；

除非存在足够、明确且经过人工确认的依据。

---

# 16. 数据模块规则

## 16.1 支持格式

P0：

```text
CSV
XLSX
```

## 16.2 数据身份证

Dataset 应记录：

* 来源；
* 发布者；
* 平台；
* 标识；
* DOI；
* 获取日期；
* 许可证；
* 推荐引用；
* 限制。

## 16.3 Original DatasetVersion

必须：

* `version_type=ORIGINAL`；
* 无父版本；
* 无 Transformation；
* Artifact 不可变；
* 文件哈希存在。

## 16.4 数据质量

确定性规则负责：

* 缺失；
* 重复；
* 常量列；
* 混合类型；
* 类别不一致；
* 越界；
* 极端值；
* 分组不平衡；
* 敏感字段。

AI 可解释，不负责计算检出数量。

## 16.5 CleaningPlan

CleaningPlan 只允许白名单操作。

不得保存：

* Python；
* SQL；
* Shell；
* 任意表达式语言；
* 无法审计的 Lambda。

## 16.6 异常值

不得默认删除异常值。

必须：

* 标记；
* 解释；
* 预览；
* 请求确认。

## 16.7 执行

只有 `APPROVED` 的 CleaningPlan 可以执行。

成功后必须生成：

* DataTransformation；
* 新 DatasetVersion；
* 新 Artifact；
* 处理日志；
* 父版本关系。

---

# 17. 统计分析规则

## 17.1 正式数字来源

所有正式数字只能由：

```text
SciPy
statsmodels
NumPy
pandas
```

等确定性工具计算。

模型不得：

* 计算 p 值；
* 修改系数；
* 修改样本量；
* 判断不存在于结果中的显著性；
* 生成虚构置信区间。

## 17.2 AnalysisPlan

必须绑定：

* ResearchQuestionVersion；
* DatasetVersion；
* 变量；
* 方法；
* 缺失策略；
* 参数；
* 前提检查；
* ApprovalRecord。

## 17.3 运行前检查

至少检查：

* 数据类型；
* 样本量；
* 缺失；
* 配对关系；
* 独立性确认；
* 正态性或适用提示；
* 方差；
* 线性；
* 极端值。

## 17.4 运行结果

AnalysisRun 完成后不可修改。

修正方式：

```text
旧 Run INVALIDATED
→ 新 AnalysisPlan 或新 Run
```

## 17.5 相关与因果

相关分析结果必须包含：

```text
相关关系不等于因果关系。
```

## 17.6 AI 解释

AI 解释中的每个数字必须能够映射到：

```text
AnalysisResult 字段路径
```

---

# 18. 图表模块规则

## 18.1 图表来源

Figure 至少绑定：

```text
DatasetVersion
```

涉及统计结果时必须绑定：

```text
AnalysisRun
AnalysisResult
```

## 18.2 图像与代码

每张正式 Figure 至少产生：

* 图像 Artifact；
* 代码 Artifact；
* 参数；
* 图注；
* 版本来源。

## 18.3 不覆盖旧图

参数变更后创建新 Figure。

不得覆盖旧图像文件。

## 18.4 图表规范

检查器独立于 Renderer。

渲染成功不代表规范通过。

## 18.5 数值

图表中的均值、误差线、拟合结果必须从确定性数据读取。

---

# 19. 论文模块规则

## 19.1 支持格式

P0 只支持：

```text
DOCX
```

## 19.2 原文保护

原 ManuscriptVersion 不可覆盖。

自动修复必须产生新版本。

## 19.3 检查器

建议独立实现：

* InTextCitationChecker；
* ReferenceListChecker；
* NumericConsistencyChecker；
* CausalLanguageChecker；
* TerminologyChecker；
* CaptionChecker；
* BasicStyleChecker。

## 19.4 数字核对

数字必须从结构化 AnalysisResult 对比。

不得让模型通过自然语言记忆判断正式数字。

## 19.5 高风险问题

以下不得自动修复：

* 因果表述；
* 样本外推；
* 学术共识表述；
* 统计数字；
* 引用内容；
* 研究结论。

## 19.6 低风险修复

可考虑：

* 空格；
* 简单标点；
* 基础单位格式；
* 明确编号格式。

仍需生成新 ManuscriptVersion。

---

# 20. 证据链规则

## 20.1 证据链是后端数据

React Flow 只负责展示。

前端不得写死节点和关系。

## 20.2 Claim

Claim 是需要被支持、反对或限定的科研论述。

## 20.3 Link

ClaimEvidenceLink 可表示：

```text
SUPPORTED_BY
CONTRADICTED_BY
QUALIFIED_BY
DERIVED_FROM
TRANSFORMED_FROM
ANALYZED_BY
PRODUCED_BY
VISUALIZED_AS
CONFIRMED_BY
AUDITED_BY
INVALIDATED_BY
```

## 20.4 同项目约束

任何证据关系不得跨项目。

## 20.5 失效传播

上游失效时，下游：

* 不删除；
* 标记失效或待审核；
* 保留关系历史；
* 重新生成 AuditResult。

## 20.6 完整度

完整度仅表示流程证据覆盖。

不得将其展示为科研质量评分或论文得分。

---

# 21. AI Schema 开发规则

## 21.1 所有关键输出结构化

必须使用 Pydantic Schema。

不得解析自由文本来驱动正式业务操作。

## 21.2 公共 Envelope

AI 输出应包含：

* schema_version；
* task_type；
* result；
* source_ids；
* confidence；
* limitations；
* warnings；
* requires_human_review；
* model_metadata。

## 21.3 来源

需要证据的输出必须包含真实 Source ID。

若缺失来源：

* 不落为正式结论；
* 返回需要复核；
* 记录错误。

## 21.4 Prompt 版本

每个 Prompt 必须有版本。

修改 Prompt 时：

* 提高版本；
* 运行黄金测试；
* 记录变化；
* 不静默覆盖。

## 21.5 模型失败

允许受控重试。

不得无限重试或隐藏失败。

## 21.6 模型边界

不得向模型发送：

* API Key；
* Token；
* `.env`；
* 完整 L3 数据；
* 其他项目内容；
* 不相关文件；
* 完整数据表。

---

# 22. Agent 工具规则

## 22.1 工具白名单

只允许正式定义的工具。

未知工具拒绝。

## 22.2 工具上下文

以下字段由系统注入：

* project_id；
* user_id；
* agent_run_id；
* request_id。

模型不能提供或覆盖。

## 22.3 Agent Tool 不直接访问数据库

工具应调用 Application Service。

不得：

```python
def tool(..., session: Session):
    session.add(...)
```

## 22.4 有副作用工具

执行前校验：

* 权限；
* 项目；
* 状态；
* Approval；
* 快照哈希；
* 幂等；
* 输入版本。

## 22.5 禁止注册的工具

```text
execute_shell
execute_python
execute_sql
run_arbitrary_code
overwrite_dataset
delete_original_file
modify_analysis_result
approve_on_behalf_of_user
bypass_permission
download_paid_fulltext
generate_complete_thesis
```

## 22.6 Agent 失败

工具失败时，Agent 必须明确说明失败。

不得将失败结果包装为成功回答。

---

# 23. 安全规则

## 23.1 默认拒绝

任何未明确允许的操作默认拒绝。

## 23.2 跨项目访问

所有对象查询必须检查项目归属。

不得只按 UUID 查询后返回。

## 23.3 提示注入

PDF、DOCX、CSV 和外部 API 内容都是不可信文本。

文档中的指令不得改变：

* 系统规则；
* 工具权限；
* Approval；
* 项目范围。

## 23.4 日志

不得记录：

* 密码；
* JWT；
* API Key；
* Secret；
* 完整敏感字段；
* 完整数据表；
* 未脱敏全文。

## 23.5 密钥

真实密钥只能放：

* 环境变量；
* Secret 管理；
* 本地未提交配置。

## 23.6 导出

ReproPackage 不得包含：

* `.env`；
* Secret；
* 数据库密码；
* 其他项目文件；
* 默认 L3 数据；
* 未授权 PDF。

## 23.7 任意网络请求

P0 不允许用户或 Agent 提供任意 URL 由后端抓取。

---

# 24. 开源与依赖规则

## 24.1 新增依赖前

必须确认：

1. 是否必要；
2. 是否已有依赖可完成；
3. 官方来源；
4. 当前版本；
5. 许可证；
6. 漏洞；
7. 活跃度；
8. 传递依赖；
9. 安装脚本；
10. 替代方案。

## 24.2 不得凭记忆填写许可证

必须以所锁定版本的官方许可证文件为准。

## 24.3 无许可证仓库

可以学习一般思想。

不得直接复制代码或文档。

## 24.4 强 Copyleft

GPL、AGPL 等必须专项审查。

未经确认不得进入核心代码路径。

## 24.5 Third Party Notices

新增需要声明的依赖时同步更新：

```text
THIRD_PARTY_NOTICES.md
```

## 24.6 Vendor

Vendor 文件必须记录：

* 来源；
* 版本；
* 哈希；
* 许可证；
* 是否修改。

---

# 25. 前端开发规则

## 25.1 页面是科研工作台

不得把整个产品简化成聊天页面。

核心数据使用：

* 表格；
* 表单；
* 卡片；
* PDF；
* 图表；
* 图谱；
* 审批面板。

Agent 面板只辅助下一步。

## 25.2 服务端状态

服务端是业务事实来源。

前端不得自行决定：

* 资源状态；
* 是否已批准；
* Claim 是否可信；
* Job 是否完成；
* EvidenceLink 是否存在。

## 25.3 `allowed_actions`

前端优先使用后端返回的：

* allowed_actions；
* permissions；
* blocking_reasons；
* warnings。

## 25.4 API 类型

优先使用自动生成的 Client 和类型。

不得复制后端枚举后长期独立维护。

## 25.5 错误展示

应展示：

* 用户可理解消息；
* Request ID；
* 是否可重试；
* 下一步建议。

不得展示后端堆栈。

## 25.6 PDF.js

EvidenceSpan 高亮失败时：

* 回退到页码；
* 显示原文上下文；
* 不伪造高亮。

## 25.7 React Flow

节点详情和关系来源于后端 API。

## 25.8 可访问性

状态不能只通过颜色表示。

表单必须有标签，交互必须支持键盘基本操作。

---

# 26. 测试要求

## 26.1 所有改动必须测试

不得以“改动很小”为由跳过测试。

## 26.2 最低测试范围

每个功能至少包含：

* 正常路径；
* 非法输入；
* 无权限；
* 错误状态；
* 外部失败；
* 幂等或重复提交；
* 必要审计。

## 26.3 缺陷修复

修复缺陷时，必须先或同时添加能够复现问题的回归测试。

## 26.4 单元测试

重点覆盖：

* 领域规则；
* 状态机；
* 去重；
* 哈希；
* 统计；
* 数据质量；
* 引用匹配；
* EvidenceLink；
* Approval；
* 权限。

## 26.5 契约测试

重点覆盖：

* REST API；
* AI Schema；
* Agent Tool；
* Adapter。

## 26.6 集成测试

重点覆盖：

* PostgreSQL；
* MinIO；
* Valkey；
* Celery；
* GROBID；
* OpenAlex Mock；
* 全栈文件流。

## 26.7 E2E

主链必须使用 Playwright 覆盖。

## 26.8 黄金测试

修改以下内容时必须运行对应黄金集：

* 文献抽取；
* EvidenceSpan；
* 数据质量；
* 统计；
* 图表；
* 论文问题；
* AI Prompt；
* Claim Audit。

## 26.9 零容忍

测试中必须保证：

```text
虚构文献 = 0
虚构 DOI = 0
虚构 EvidenceSpan = 0
模型生成正式统计数字 = 0
原始文件覆盖 = 0
未批准操作执行 = 0
Agent 自行审批 = 0
跨项目访问成功 = 0
```

---

# 27. 推荐测试命令

以仓库实际脚本为准。

## 27.1 后端

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

## 27.2 后端分层

```bash
cd backend
uv run pytest tests/unit
uv run pytest tests/contract
uv run pytest tests/integration
```

## 27.3 前端

```bash
cd frontend
npm ci
npm run lint
npm run typecheck
npm run test
npm run build
```

## 27.4 E2E

```bash
cd frontend
npm run test:e2e
```

## 27.5 Docker

```bash
docker compose config
docker compose up -d --build
docker compose ps
```

## 27.6 数据库迁移

```bash
docker compose exec api alembic upgrade head
```

## 27.7 完整测试

若仓库提供：

```bash
./scripts/run_tests.sh
```

则优先使用统一脚本。

## 27.8 不得伪造测试结果

无法运行某项测试时，必须明确说明：

* 未运行的命令；
* 原因；
* 已运行的替代检查；
* 潜在风险。

不得写“所有测试通过”，除非实际执行并确认。

---

# 28. Codex 标准工作流程

## 28.1 第一步：理解任务

提取：

* 用户目标；
* 涉及模块；
* 是否改变正式契约；
* 是否改变数据库；
* 是否涉及安全；
* 是否涉及模型；
* 是否涉及文件；
* 是否涉及第三方依赖。

## 28.2 第二步：读取上下文

读取：

* 正式文档；
* 相关代码；
* 相关测试；
* 最近迁移；
* 相关配置。

## 28.3 第三步：定位现有实现

搜索：

* 模型；
* Schema；
* Service；
* Router；
* Tool；
* Worker；
* Test；
* Frontend Feature。

不得在未搜索现有实现前创建平行模块。

## 28.4 第四步：定义最小改动

优先：

* 修复现有抽象；
* 扩展已有 Adapter；
* 添加已有状态机动作；
* 添加兼容字段；
* 添加测试。

避免：

* 大规模重写；
* 顺手重构无关模块；
* 替换整个技术栈；
* 新建重复服务。

## 28.5 第五步：先实现领域和测试

推荐顺序：

```text
Domain / Schema
→ Service
→ Repository / Adapter
→ Migration
→ API / Tool / Worker
→ Frontend
→ Tests
→ Docs
```

## 28.6 第六步：运行测试

至少运行与修改范围直接相关的测试。

必要时运行完整测试。

## 28.7 第七步：检查差异

检查：

* 是否修改无关文件；
* 是否生成临时文件；
* 是否泄露 Secret；
* 是否改变锁文件；
* 是否漏迁移；
* 是否漏文档；
* 是否破坏 API；
* 是否覆盖原始文件逻辑。

## 28.8 第八步：交付说明

说明：

* 修改了什么；
* 为什么；
* 关键文件；
* 测试；
* 未测试项；
* 风险或已知限制。

---

# 29. 任务拆分规则

## 29.1 单任务推荐范围

一个实现任务应尽量聚焦一个可验收结果，例如：

* 实现 DatasetVersion 模型和迁移；
* 实现 CleaningPlan Preview；
* 实现 Pearson Correlation Engine；
* 实现 PDF EvidenceSpan API；
* 实现文献矩阵页面。

## 29.2 避免超大任务

避免单个任务同时包含：

* 全部数据模型；
* 全部 API；
* 全部前端；
* 全部 Agent；
* 全部测试；
* 部署。

## 29.3 跨层任务

必要跨层任务应明确列出：

```text
数据模型
API
Worker
前端
测试
文档
```

## 29.4 顺序依赖

推荐开发顺序：

1. 工程底座；
2. Projects、Artifact、Job；
3. ResearchQuestion；
4. Literature；
5. Dataset；
6. Approval；
7. Analysis；
8. Figure；
9. Manuscript；
10. Evidence；
11. Agent；
12. Export；
13. 完整 E2E。

---

# 30. 代码修改原则

## 30.1 保持改动聚焦

不得无理由：

* 重命名大量文件；
* 全局格式化；
* 重排所有 import；
* 升级全部依赖；
* 改变无关 API；
* 修改无关 UI。

## 30.2 避免重复

新增功能前搜索现有：

* Enum；
* Schema；
* Error Code；
* Service；
* Permission；
* Utility；
* Test Fixture。

## 30.3 避免过早抽象

只有出现明确重复和稳定边界时再抽象。

不得为了“未来可能”创建复杂框架。

## 30.4 避免魔法行为

业务逻辑应显式。

例如数据处理不应根据模型文字隐式选择操作。

## 30.5 注释

注释解释：

* 为什么；
* 科研限制；
* 安全边界；
* 兼容原因。

不要逐行翻译代码。

## 30.6 类型

后端和前端尽量保持严格类型。

不得大量使用：

```text
Any
dict
unknown
```

绕过正式 Schema。

---

# 31. 错误处理规则

## 31.1 领域错误

使用明确错误类型和错误码。

例如：

```text
ANALYSIS_PLAN_NOT_APPROVED
DATASET_VERSION_INVALIDATED
EVIDENCE_LOCATION_FAILED
```

## 31.2 不捕获后静默

禁止：

```python
try:
    ...
except Exception:
    pass
```

## 31.3 外部错误映射

Adapter 将第三方错误转换为内部错误。

不得把第三方堆栈直接返回前端。

## 31.4 可重试性

错误必须明确：

```text
retryable = true / false
```

## 31.5 文件失败

文件处理失败时：

* 原文件保留；
* Job FAILED；
* 不产生正式结果；
* 记录错误。

---

# 32. 配置规则

## 32.1 环境变量

配置集中在：

```text
backend/app/core/config.py
```

或仓库实际统一配置模块。

## 32.2 不写死

不得写死：

* 密钥；
* 数据库地址；
* MinIO 密钥；
* 模型 Key；
* 外部 API Key；
* 用户密码；
* 生产域名。

## 32.3 `.env.example`

新增配置时同步更新 `.env.example`。

只写安全占位符。

## 32.4 默认值

安全相关默认值采用保守策略。

例如：

```text
MODEL_ALLOW_SENSITIVE_DATA=false
```

## 32.5 Demo Mode

Demo Mode 必须明确区分：

* 实时结果；
* 缓存结果；
* 预处理结果。

---

# 33. Git 工作规则

## 33.1 不修改无关历史

不得：

* 重写主分支历史；
* 强推；
* 删除他人提交；
* 修改未要求的历史迁移。

除非用户明确要求并说明风险。

## 33.2 不提交生成物

除项目明确要求外，不提交：

* 本地数据库；
* MinIO 数据；
* 临时 PDF；
* 用户数据；
* `.env`；
* 日志；
* 缓存；
* 测试截图垃圾文件；
* Python 缓存；
* Node 构建缓存。

## 33.3 依赖锁文件

新增或更新依赖时必须更新对应锁文件。

不得无理由刷新全部版本。

## 33.4 Commit 范围

Commit 应保持单一目的。

建议格式：

```text
feat(literature): add evidence span extraction
fix(analysis): prevent unapproved runs
test(dataset): cover cleaning plan idempotency
docs(api): define manuscript check contract
refactor(artifacts): isolate storage adapter
security(agent): block project id override
```

## 33.5 不虚构 Commit

若未实际提交，不要声称已经提交。

## 33.6 分支

不得擅自覆盖用户当前分支策略。

执行前检查：

```bash
git status
git branch --show-current
```

## 33.7 工作区已有改动

若存在用户未提交修改：

* 不删除；
* 不覆盖；
* 不回滚；
* 避免修改同一区域；
* 在交付中说明。

---

# 34. Pull Request 规则

PR 说明至少包含：

## 34.1 Summary

修改内容。

## 34.2 Motivation

为何需要。

## 34.3 Scope

涉及模块和文件。

## 34.4 Data Model Changes

是否有迁移、字段或状态机变化。

## 34.5 API Changes

是否改变 OpenAPI、AI Schema 或 Tool Contract。

## 34.6 Security Impact

是否涉及：

* 权限；
* 上传；
* 下载；
* 模型数据；
* Agent；
* Secret；
* 导出。

## 34.7 Tests

列出实际运行命令和结果。

## 34.8 Known Limitations

未完成或已知边界。

## 34.9 Third-Party Changes

新增依赖、许可证和声明。

---

# 35. 文档同步规则

以下变化必须同步文档。

## 35.1 产品范围变化

更新：

```text
docs/PRODUCT_REQUIREMENTS.md
```

## 35.2 架构变化

更新：

```text
docs/ARCHITECTURE.md
```

## 35.3 表、字段、状态机变化

更新：

```text
docs/DATA_MODEL_AND_WORKFLOW.md
```

## 35.4 API、AI Schema、工具变化

更新：

```text
docs/API_AI_TOOL_CONTRACTS.md
```

## 35.5 测试和门禁变化

更新：

```text
docs/TEST_AND_ACCEPTANCE.md
```

## 35.6 权限、安全、依赖、许可证变化

更新：

```text
docs/SECURITY_AND_OPEN_SOURCE.md
THIRD_PARTY_NOTICES.md
```

## 35.7 开发规则变化

更新：

```text
AGENTS.md
```

---

# 36. 禁止行为总表

所有代码智能体不得：

1. 伪造已执行的测试；
2. 伪造已完成的功能；
3. 将 Mock 声称为真实能力；
4. 将缓存声称为实时结果；
5. 生成虚构文献；
6. 生成虚构 DOI；
7. 生成虚构 EvidenceSpan；
8. 让模型计算正式统计数字；
9. 修改 AnalysisResult；
10. 覆盖原始 PDF；
11. 覆盖 Original DatasetVersion；
12. 覆盖 Original ManuscriptVersion；
13. 绕过 ApprovalRecord；
14. 让 Agent 批准自身建议；
15. 注册 Shell 工具；
16. 注册任意 Python 工具；
17. 注册任意 SQL 工具；
18. 让 Agent 直接访问数据库；
19. 让 Agent 构造任意外部请求；
20. 只在前端实施权限；
21. 仅按 UUID 返回资源；
22. 跨项目建立 EvidenceLink；
23. 在日志写入 Secret；
24. 在前端打包后端 Key；
25. 将 `.env` 放入导出包；
26. 将其他项目文件放入复现包；
27. 未经审查引入强 Copyleft；
28. 复制无许可证仓库代码；
29. 删除第三方版权声明；
30. 为通过测试删除测试；
31. 为通过测试降低核心断言；
32. 捕获异常后静默；
33. 删除用户未提交代码；
34. 大规模修改无关文件；
35. 擅自替换技术栈；
36. 擅自拆分微服务；
37. 擅自增加数据库；
38. 自动生成完整论文并宣称可提交；
39. 把相关关系表述为因果；
40. 把当前文献集合结论扩大为整个领域事实。

---

# 37. 任务完成定义

一个任务只有满足适用的以下条件才算完成。

## 37.1 需求

* 功能与正式需求一致；
* 未扩展无关范围；
* 已知限制明确。

## 37.2 架构

* 模块边界正确；
* 未引入循环依赖；
* 第三方能力经过 Adapter；
* 未破坏模块化单体。

## 37.3 数据

* 模型和字段正确；
* 迁移完整；
* 版本规则正确；
* 项目作用域正确；
* 原始对象未覆盖。

## 37.4 API

* 请求和响应 Schema 完整；
* 权限完整；
* 错误码完整；
* 幂等完整；
* 乐观锁适用时完整；
* OpenAPI 更新。

## 37.5 AI 与 Agent

* 输出结构化；
* 来源可追踪；
* Prompt 版本化；
* Tool 在白名单；
* Approval 不可绕过；
* ToolCall 可审计。

## 37.6 安全

* 输入校验；
* 项目隔离；
* 日志脱敏；
* 无 Secret；
* 文件安全；
* 敏感数据边界；
* 无任意代码执行。

## 37.7 测试

* 单元测试；
* 契约测试；
* 必要集成测试；
* 缺陷回归；
* 实际执行并记录结果。

## 37.8 前端

* 加载；
* 空状态；
* 错误状态；
* 权限状态；
* Job 进度；
* 可访问性基础；
* 不自行推断业务事实。

## 37.9 文档

* 相关正式文档已同步；
* README 必要时更新；
* 新依赖已登记。

## 37.10 交付

* 修改摘要；
* 关键文件；
* 测试命令；
* 未执行项；
* 风险；
* 后续步骤。

---

# 38. Codex 交付回复格式

完成代码任务后，回复建议使用：

```markdown
## 完成内容

- ...
- ...

## 关键修改

- `path/to/file.py`：...
- `path/to/test.py`：...

## 测试

- `command`：通过
- `command`：通过

## 数据库或契约变化

- Alembic Migration：有/无
- OpenAPI：有/无
- AI Schema：有/无
- Tool Contract：有/无

## 安全与可信边界

- ...
- ...

## 未完成或已知限制

- ...
```

不得仅回复：

> 已完成。

---

# 39. 无法完成时的处理

若环境、依赖或仓库状态导致无法完成全部任务：

1. 完成能够安全完成的部分；
2. 不破坏现有代码；
3. 不编造结果；
4. 明确列出阻断项；
5. 提供已修改文件；
6. 提供已运行检查；
7. 提供继续实现所需的准确条件。

不得因任务复杂而直接放弃全部实现。

---

# 40. 处理不确定需求

若存在轻微不确定：

* 依据正式文档采用最保守兼容方案；
* 使用清晰占位；
* 不破坏数据；
* 在交付中说明假设。

若不确定涉及以下内容，不得自行猜测高风险语义：

* 是否删除数据；
* 是否发送敏感数据；
* 是否改变许可证；
* 是否公开 PDF；
* 是否允许 Agent 执行；
* 是否修改正式统计；
* 是否绕过审批；
* 是否改变核心架构。

此时应保持现有安全边界，不实施高风险扩展。

---

# 41. 开发阶段建议

## 阶段 0：仓库和工程底座

* Docker Compose；
* 配置；
* PostgreSQL；
* Valkey；
* MinIO；
* API；
* Worker；
* 前端；
* 健康检查；
* CI。

## 阶段 1：项目、文件和任务

* User；
* ResearchProject；
* ProjectMember；
* Artifact；
* Job；
* AuditLog；
* 权限。

## 阶段 2：研究问题和文献

* ResearchQuestion；
* QueryPlan；
* OpenAlex；
* LiteratureRecord；
* Document；
* GROBID；
* EvidenceSpan；
* 文献矩阵。

## 阶段 3：数据

* Dataset；
* DatasetVersion；
* DatasetColumn；
* DataQuality；
* CleaningPlan；
* Approval；
* Transformation。

## 阶段 4：统计和图表

* AnalysisPlan；
* AssumptionCheck；
* AnalysisRun；
* AnalysisResult；
* FigurePlan；
* Figure。

## 阶段 5：论文和证据链

* Manuscript；
* ManuscriptIssue；
* Claim；
* ClaimEvidenceLink；
* AuditResult；
* React Flow。

## 阶段 6：Agent 和复现包

* AgentRun；
* ToolCall；
* ModelInvocation；
* Guardrail；
* Export；
* ReproPackage。

## 阶段 7：比赛打磨

* 黄金集；
* E2E；
* 离线模式；
* 演示项目；
* 性能；
* 安全；
* 开源声明；
* 录屏。

不得在阶段 1 尚未稳定时优先构建复杂多 Agent 或高级图谱。

---

# 42. 架构保护检查表

每次较大修改前后检查：

* [ ] 是否仍为模块化单体；
* [ ] 是否新增不必要服务；
* [ ] 是否新增数据库；
* [ ] 是否绕过 Adapter；
* [ ] 是否让 Router 承担业务；
* [ ] 是否让 Agent 直接写数据库；
* [ ] 是否破坏原始文件不可变；
* [ ] 是否破坏计划、审批、执行分离；
* [ ] 是否让模型生成正式数字；
* [ ] 是否让前端成为事实来源；
* [ ] 是否产生跨项目关系；
* [ ] 是否需要更新架构文档。

---

# 43. 科研可信检查表

实现文献、统计、图表或论文功能时检查：

* [ ] 文献是否来自真实 Provider；
* [ ] DOI 是否验证；
* [ ] 原文是否来自实际 PDF；
* [ ] EvidenceSpan 是否可定位；
* [ ] 总结是否限定当前文献集合；
* [ ] 数据版本是否明确；
* [ ] 处理是否经过批准；
* [ ] 统计是否由程序计算；
* [ ] 分析方法是否在 P0；
* [ ] 相关是否明确非因果；
* [ ] 图表是否绑定正确运行；
* [ ] 论文数字是否关联 AnalysisResult；
* [ ] Claim 是否能返回来源；
* [ ] 限制是否可见。

---

# 44. 安全检查表

* [ ] API 是否校验身份；
* [ ] 是否校验项目权限；
* [ ] 是否校验对象归属；
* [ ] 是否校验状态；
* [ ] 是否校验 Approval；
* [ ] 文件类型是否验证；
* [ ] 文件路径是否系统生成；
* [ ] 是否防止 ZIP Slip；
* [ ] 是否限制文件大小；
* [ ] 是否记录敏感数据；
* [ ] 是否发送模型不必要内容；
* [ ] 是否引入任意代码执行；
* [ ] 是否泄露 Secret；
* [ ] 导出是否混入其他项目；
* [ ] 新依赖是否审查。

---

# 45. 测试检查表

* [ ] 正常路径；
* [ ] 空输入；
* [ ] 非法输入；
* [ ] 无权限；
* [ ] 跨项目；
* [ ] 状态冲突；
* [ ] 幂等；
* [ ] 并发；
* [ ] 外部服务失败；
* [ ] Worker 失败；
* [ ] 原始文件保护；
* [ ] 审计；
* [ ] 回归测试；
* [ ] 相关黄金集；
* [ ] 实际执行测试命令。

---

# 46. 最终仓库原则

所有参与 RECA 开发的智能体必须长期遵守以下原则：

```text
先读正式文档
→ 再读现有代码
→ 搜索现有实现
→ 设计最小改动
→ 保持模块边界
→ 使用正式领域对象
→ 保留版本和血缘
→ 对高风险操作请求审批
→ 使用确定性工具产生数字
→ 对模型输出进行结构化校验
→ 对所有资源实施项目隔离
→ 添加自动化测试
→ 更新正式文档
→ 如实说明测试和限制
```

必须始终保护以下底线：

```text
真实文献
真实原文
真实数据版本
真实程序结果
真实人工确认
真实工具调用
真实测试结果
```

任何实现都不得以更炫的 Agent 表现、更短的开发时间或更方便的演示为由，破坏：

* 文献真实性；
* 统计确定性；
* 数据不可变性；
* 用户审批；
* 项目隔离；
* 安全边界；
* 开源许可证；
* 测试可信性。

RECA 0.1 的开发目标不是创建一个看起来会科研的聊天机器人，而是创建一个能够将研究问题、文献证据、数据版本、确定性分析、科研图表、论文论述和人工确认可靠连接起来的科研工作流系统。
