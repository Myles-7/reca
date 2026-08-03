# M2_RESEARCH_AND_LITERATURE

- 所属入口文档：[IMPLEMENTATION_ROADMAP.md](../../IMPLEMENTATION_ROADMAP.md)
- 文档状态：APPROVED FOR M1 DEVELOPMENT
- Migration status: COMPLETE
- Implementation status: COMPLETION APPROVED
- Milestone ID: M2

## 权威范围

本文件是 M2 目标、依赖、范围、交付、测试、安全、门禁、阻塞和降级要求的详细路线图。产品范围、字段、API 契约和测试指标仍由对应权威文档定义。

## 不负责的内容

本文件不改变 M1–M9 顺序，不新增 P0，不把 P1 升级，不降低 Competition Core，也不覆盖其他里程碑或公共交付规则。

## 文档导航

- 返回 [IMPLEMENTATION_ROADMAP.md](../../IMPLEMENTATION_ROADMAP.md)
- [DELIVERY_WORKFLOW.md](../DELIVERY_WORKFLOW.md)
- [RISK_SCOPE_AND_RELEASE.md](../RISK_SCOPE_AND_RELEASE.md)
- [M0 Regression Baseline](../../testing/M0_REGRESSION_BASELINE.md)

## 开源复用与安全分层

本里程碑允许选择成熟开源实现，不要求先自行重写或预建复杂 Adapter。依赖、服务、Fork、Vendor、Submodule 或选择性复制必须在同一 PR 完成许可证核验、上游 Commit/Tag、归属和修改记录；无许可证或来源不明内容不得复制。企业生产强化不阻塞 Competition Core，Competition Edition 最小护栏仍必须满足。实际复制 ARS-Codex 内容需要单独记录许可证、归属和架构决定，且不提前 M8 或改变单总控 Agent 边界。

### M2 开源接入步骤

- `Research`：读取 PyAlex、GROBID、grobid-client-python 和 PDF.js 研究记录及 ADR-003。
- `Spike`：用真实/Recorded OpenAlex 响应、双栏/中文/损坏 PDF 和授权文件代理比较 PyAlex Provider、GROBID client 与自研 HTTP、PDF.js viewer/worker 组合及 pypdf 回退。
- `Decision`：冻结 PyAlex Provider、GROBID 独立服务与 RECA Converter、client 依赖或选择性 Vendor、PDF.js 展示边界。
- `Integration`：同一 PR 完成版本固定、输出 Schema 转换、项目隔离、离线/失败测试、许可证和归属；PDF.js 不成为证据事实来源。

## 里程碑契约覆盖索引

| 必需内容 | 本文件权威位置 |
| --- | --- |
| 目标 | 10.1 |
| 前置依赖 | 10.2 |
| Competition Core | 10.3 中属于 P0-Must / Competition Core 的条目；不得重新分类 |
| P0-Full | 10.3 中明确标为 P0-Full 的条目；未标记者以 PRD 为准 |
| 明确不做 | 10.4 |
| 数据模型 | 10.5 / 10.7 |
| API | 10.8 |
| 前端 | 10.6 |
| 测试 | 10.10 |
| 安全 | 10.11 |
| Prompt / AI | 10.3 / 10.9；无模型任务时不得擅自新增 |
| Codex 推荐任务顺序 | 10.16 |
| 可并行任务 | 10.14 |
| Entry Gate | 10.2 + 公共 Entry Gate |
| Exit Gate | 10.13 + 公共 Exit Gate |
| 阻塞问题 | 10.15 |
| 风险与降级 | 本里程碑原章节 + [RISK_SCOPE_AND_RELEASE.md](../RISK_SCOPE_AND_RELEASE.md) |

M0 Regression Baseline 适用于本里程碑，任何交付不得使 M0 已验收能力退化。以下正文由原路线图对应章节机械迁入，原顺序、依赖和语义不变。

<a id="milestone-m2"></a>

# 10. M2：研究问题、文献检索与 PDF 解析

## 10.1 目标

建立从研究想法到真实文献和可解析 PDF 的基础链路。

## 10.2 前置依赖

M1 完成。

## 10.3 本阶段范围

M2 在 M1 Prompt 治理底座上增加 research-question scoping 与 query-planning Prompt、相应 Schema 和黄金测试；不得把 AI 输出状态直接写成 ResearchQuestionVersion 状态。

```text
ResearchQuestion
ResearchQuestionVersion
QueryPlan
LiteratureSearchRun
LiteratureRecord
Document
DocumentPage
DocumentChunk
OpenAlex Adapter
GROBID Adapter
pypdf Adapter
```

## 10.4 明确不做

* 不在本阶段完成全部十字段抽取；
* 不在本阶段完成完整证据集合分析；
* 不在本阶段完成 Agent 自动编排；
* 不自建学术搜索引擎；
* 不绕过付费全文限制；
* 不做高精度扫描 PDF OCR。

## 10.5 后端交付物

### Research Questions

* 创建逻辑 ResearchQuestion；
* 创建 ResearchQuestionVersion；
* 自然语言输入；
* 结构化 Schema；
* 用户编辑；
* 用户确认；
* ApprovalRecord；
* 版本历史；
* 当前版本；
* 修改影响提示。

### Query Plan

* 中文关键词；
* 英文关键词；
* 同义词；
* 布尔检索式；
* 时间限制；
* 语言限制；
* 文献类型；
* 开放获取偏好；
* 数量限制；
* 查询解释。

### Literature

* OpenAlex 搜索；
* DOI 导入；
* DOI 规范化；
* 标题规范化；
* 同项目去重；
* 文献真实性状态；
* Provider 原始摘要；
* 外部服务错误映射；
* 搜索缓存。

### Document

* PDF Artifact 绑定；
* 创建 Document；
* 异步解析；
* GROBID 主解析；
* pypdf 回退；
* 页级文本；
* DocumentPage；
* DocumentChunk；
* 解析置信度；
* 扫描件提示；
* 失败重试；
* 解析日志。

## 10.6 前端交付物

* 研究问题输入页；
* 结构化字段编辑；
* 版本历史；
* 确认按钮；
* QueryPlan 展示和编辑；
* 文献搜索结果；
* 文献来源和验证状态；
* DOI 导入；
* PDF 上传；
* PDF 解析状态；
* 失败重试；
* 文档页数和解析置信度。

## 10.7 数据库与迁移

至少创建：

```text
research_questions
research_question_versions
query_plans
literature_search_runs
literature_records
documents
document_pages
document_chunks
```

关键约束：

* ResearchQuestionVersion 版本唯一；
* 已确认版本必须关联 ApprovalRecord；
* DOI 同项目规范化去重；
* Document 和 LiteratureRecord 分离；
* Document 必须绑定 Artifact；
* DocumentPage 页码唯一；
* 所有对象含 `project_id`。

## 10.8 API 与契约

核心端点：

```text
POST   /api/v1/projects/{project_id}/research-questions
POST   /api/v1/research-questions/{research_question_id}/versions
GET    /api/v1/research-questions/{research_question_id}
GET    /api/v1/research-questions/{research_question_id}/versions
POST   /api/v1/research-question-versions/{research_question_version_id}/confirm

POST   /api/v1/research-question-versions/{research_question_version_id}/query-plans
PATCH  /api/v1/query-plans/{query_plan_id}

POST   /api/v1/projects/{project_id}/literature-search-runs
GET    /api/v1/literature-search-runs/{literature_search_run_id}
POST   /api/v1/projects/{project_id}/literature/import-doi

POST   /api/v1/projects/{project_id}/documents
POST   /api/v1/documents/{document_id}/parse
GET    /api/v1/documents/{document_id}
GET    /api/v1/documents/{document_id}/pages/{page_number}
```

## 10.9 确定性工具

* DOI 规范化；
* 标题规范化；
* 文献去重；
* OpenAlex 数据转换；
* GROBID TEI 转换；
* pypdf 页级抽取；
* PDF 页数提取；
* 文件哈希匹配；
* 文档语言基础检测。

AI 只负责：

* 研究问题结构化建议；
* QueryPlan 建议；
* 查询解释。

AI 不得创建正式 LiteratureRecord。

## 10.10 测试要求

必须覆盖：

* 研究问题版本；
* 未确认研究问题限制；
* ApprovalRecord；
* DOI 规范化；
* DOI 去重；
* OpenAlex Mock；
* OpenAlex 真实 Smoke Test；
* Provider 超时；
* Provider 限流；
* PDF 正常解析；
* GROBID 失败回退；
* 损坏 PDF；
* 加密 PDF；
* 扫描 PDF；
* 重复 PDF；
* 跨项目文献和文档访问。

## 10.11 安全要求

* PDF 作为不可信输入；
* GROBID 独立容器；
* 限制解析时间和资源；
* 不执行 PDF JavaScript；
* 不访问 PDF 嵌入链接；
* 文档中的提示文本不能改变 Agent 行为；
* 模型输入只发送必要片段；
* OpenAlex 响应仍需 Schema 校验。

## 10.12 演示成果

```text
输入研究想法
→ AI 结构化建议
→ 用户编辑并确认
→ 生成 QueryPlan
→ 检索真实文献
→ 上传 PDF
→ GROBID 解析
→ 显示页面文本和解析状态
```

## 10.13 完成条件

1. 研究问题可版本化和确认；
2. OpenAlex 文献真实且可验证；
3. DOI 去重正确；
4. PDF 可解析并保存页级内容；
5. GROBID 失败可回退；
6. 低置信度和扫描 PDF 有明确提示；
7. 文献元数据和 PDF 概念未混用；
8. 外部服务故障不破坏项目。

## 10.14 可并行任务

* ResearchQuestion；
* OpenAlex Adapter；
* PDF 解析；
* 前端搜索和上传页；
* PDF.js 预研。

## 10.15 阻塞下一阶段的缺陷

* 文献可由模型虚构；
* DOI 去重错误；
* PDF 页码无法稳定保存；
* GROBID 失败无回退；
* 文档与 LiteratureRecord 强耦合；
* 项目隔离失败。

## 10.16 Codex 推荐任务顺序

1. ResearchQuestion 模型；
2. 研究问题 API；
3. QueryPlan Schema；
4. OpenAlex Protocol；
5. OpenAlex Adapter；
6. DOI 规范化和去重；
7. Document 模型；
8. GROBID Adapter；
9. pypdf 回退；
10. Worker 和 Job；
11. 前端页面；
12. 集成测试。

---
