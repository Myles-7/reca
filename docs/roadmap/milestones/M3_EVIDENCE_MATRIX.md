# M3_EVIDENCE_MATRIX

- 所属入口文档：[IMPLEMENTATION_ROADMAP.md](../../IMPLEMENTATION_ROADMAP.md)
- 文档状态：Conditional Approval
- Migration status: COMPLETE
- Milestone ID: M3

## 权威范围

本文件是 M3 目标、依赖、范围、交付、测试、安全、门禁、阻塞和降级要求的详细路线图。产品范围、字段、API 契约和测试指标仍由对应权威文档定义。

## 不负责的内容

本文件不改变 M1–M9 顺序，不新增 P0，不把 P1 升级，不降低 Competition Core，也不覆盖其他里程碑或公共交付规则。

## 文档导航

- 返回 [IMPLEMENTATION_ROADMAP.md](../../IMPLEMENTATION_ROADMAP.md)
- [DELIVERY_WORKFLOW.md](../DELIVERY_WORKFLOW.md)
- [RISK_SCOPE_AND_RELEASE.md](../RISK_SCOPE_AND_RELEASE.md)
- [M0 Regression Baseline](../../testing/M0_REGRESSION_BASELINE.md)

## 开源复用与安全分层

本里程碑允许选择成熟开源实现，不要求先自行重写或预建复杂 Adapter。依赖、服务、Fork、Vendor、Submodule 或选择性复制必须在同一 PR 完成许可证核验、上游 Commit/Tag、归属和修改记录；无许可证或来源不明内容不得复制。企业生产强化不阻塞 Competition Core，Competition Edition 最小护栏仍必须满足。实际复制 ARS-Codex 内容需要单独记录许可证、归属和架构决定，且不提前 M8 或改变单总控 Agent 边界。

## 里程碑契约覆盖索引

| 必需内容 | 本文件权威位置 |
| --- | --- |
| 目标 | 11.1 |
| 前置依赖 | 11.2 |
| Competition Core | 11.3 中属于 P0-Must / Competition Core 的条目；不得重新分类 |
| P0-Full | 11.3 中明确标为 P0-Full 的条目；未标记者以 PRD 为准 |
| 明确不做 | 11.4 |
| 数据模型 | 11.5 / 11.7 |
| API | 11.8 |
| 前端 | 11.6 |
| 测试 | 11.10 |
| 安全 | 11.11 |
| Prompt / AI | 11.9；无模型任务时不得擅自新增 |
| Codex 推荐任务顺序 | 11.16 |
| 可并行任务 | 11.14 |
| Entry Gate | 11.2 + 公共 Entry Gate |
| Exit Gate | 11.13 + 公共 Exit Gate |
| 阻塞问题 | 11.15 |
| 风险与降级 | 本里程碑原章节 + [RISK_SCOPE_AND_RELEASE.md](../RISK_SCOPE_AND_RELEASE.md) |

M0 Regression Baseline 适用于本里程碑，任何交付不得使 M0 已验收能力退化。以下正文由原路线图对应章节机械迁入，原顺序、依赖和语义不变。

<a id="milestone-m3"></a>

# 11. M3：文献矩阵与 EvidenceSpan

## 11.1 目标

将真实 PDF 转换为可核验、可修正、可筛选的文献证据矩阵，形成第一个完整对外演示闭环。M3 增加 literature-extraction 与 evidence-set-summary Prompt、来源校验和 EvidenceSpan 定位失败测试；模型或解析失败不得伪造 EvidenceSpan。

## 11.2 前置依赖

M2 完成。

## 11.3 本阶段范围

```text
LiteratureExtraction
LiteratureExtractionField
EvidenceSpan
LiteratureDecision
TopicGenerationRun
TopicCandidate
```

固定十字段：

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

## 11.4 明确不做

* 不宣称覆盖所有文献字段；
* 不自动替用户排除文献；
* 不把模型抽取视为正式事实；
* 不宣称当前集合代表整个学术界；
* 不做大规模系统综述；
* 不做复杂引文网络。

## 11.5 后端交付物

### 文献抽取

* 创建 LiteratureExtraction；
* 十字段候选结果；
* 字段级置信度；
* Schema 校验；
* 来源校验；
* 用户修正；
* 修正历史；
* 确认状态。

### EvidenceSpan

至少保存：

```text
document_id
page_number
source_text
section
start_offset
end_offset
bounding_box
confidence
confirmation_status
```

必须支持：

* 字段与 EvidenceSpan 关联；
* 页码跳转；
* 原文高亮；
* 无证据时明确为空；
* 用户确认或驳回；
* 证据失效。

### 文献决策

状态：

```text
INCLUDED
EXCLUDED
UNCERTAIN
```

记录：

* 决策人；
* 决策时间；
* 理由；
* AI 推荐；
* 修改历史。

### 当前证据集合分析

输出：

* 共识；
* 争议；
* 反例；
* 方法差异；
* 样本差异；
* 当前证据不足；
* 待补文献；
* 限制说明。

所有输出必须绑定来源文献 ID 或 EvidenceSpan ID。

### 候选研究问题

固定生成 3 个候选项。

每个候选项包含：

* 研究问题；
* 研究对象；
* 核心变量；
* 文献依据；
* 当前证据；
* 数据要求；
* 推荐方法；
* 方法难度；
* 数据可获得性；
* 伦理风险；
* 主要限制；
* 导师确认事项。

## 11.6 前端交付物

* 文献矩阵；
* TanStack Table；
* 固定十字段；
* 字段置信度；
* 低置信度筛选；
* PDF.js 双栏或侧栏；
* 页码跳转；
* 原文高亮；
* 字段修正；
* 字段确认；
* 文献纳入、排除、待确认；
* 当前证据分析页；
* 3 个候选问题卡片。

## 11.7 数据库与迁移

至少创建：

```text
literature_extractions
literature_extraction_fields
evidence_spans
literature_decisions
topic_generation_runs
topic_candidates
```

关键约束：

* EvidenceSpan 必须绑定真实 Document；
* 页码必须在 Document 页数范围内；
* LiteratureDecision 同一文献保留历史；
* 当前决策可查询；
* 字段修正不覆盖原始模型输出；
* 所有对象属于同一项目。

## 11.8 API 与契约

核心端点：

```text
POST   /api/v1/documents/{document_id}/extractions
GET    /api/v1/literature-extractions/{literature_extraction_id}
PATCH  /api/v1/literature-extraction-fields/{field_id}
POST   /api/v1/literature-extraction-fields/{field_id}/confirm

GET    /api/v1/evidence-spans/{evidence_span_id}
POST   /api/v1/evidence-spans/{evidence_span_id}/confirm
POST   /api/v1/evidence-spans/{evidence_span_id}/reject

POST   /api/v1/literature-records/{literature_record_id}/decisions
GET    /api/v1/projects/{project_id}/literature-matrix
POST   /api/v1/projects/{project_id}/evidence-set-analysis
POST   /api/v1/projects/{project_id}/topic-generation-runs
```

## 11.9 确定性工具与 AI

确定性程序负责：

* PDF 位置；
* 页码；
* 字符范围；
* 坐标；
* 字段 Schema；
* 来源存在性；
* 文献集合筛选；
* 文献 ID 和证据 ID 校验。

AI 负责：

* 字段候选抽取；
* 相关性解释；
* 共识和争议建议；
* 候选研究问题。

AI 不得：

* 生成不存在的原文；
* 修改 PDF 页码；
* 生成正式文献；
* 替用户完成文献决策。

## 11.10 测试要求

必须建立文献黄金集。

至少测试：

* 十字段准确性；
* 样本量；
* 研究设计；
* 分析方法；
* 主要结论；
* 局限；
* EvidenceSpan 原文存在；
* 页码准确；
* 高亮坐标可用；
* 无证据正确标空；
* 用户修正历史；
* 文献决策；
* 当前证据范围限定；
* 3 个候选问题固定数量；
* 模型虚构原文数量为 0。

## 11.11 安全要求

* PDF 内容视为不可信；
* EvidenceSpan 不执行任何文档指令；
* 模型仅接收必要片段；
* 不向模型发送无关项目文档；
* 字段修改必须记录用户；
* 文献决策不能由 Agent 最终批准。

## 11.12 演示成果

完整展示：

```text
研究问题
→ 真实文献
→ PDF
→ 文献矩阵
→ 点击结论
→ 跳转 PDF 页码
→ 高亮原文
→ 用户修正字段
→ 用户纳入文献
→ 当前证据集合分析
→ 3 个候选问题
```

## 11.13 完成条件

1. 十字段矩阵可用；
2. EvidenceSpan 来自真实 PDF；
3. 页码可跳转；
4. 用户可修正和确认；
5. 文献最终决策由用户完成；
6. 总结限定当前文献集合；
7. 3 个候选问题有文献依据；
8. 黄金集达到 P0-Must 演示要求；
9. 第一个对外演示闭环稳定。

## 11.14 可并行任务

* 抽取 Schema；
* EvidenceSpan 定位；
* PDF.js 高亮；
* 文献矩阵；
* 文献决策；
* 黄金集标注。

## 11.15 阻塞下一阶段的缺陷

* 虚构原文；
* 页码大量错误；
* 字段无法回到 PDF；
* 用户修正覆盖原模型结果；
* Agent 自动排除文献；
* 当前证据分析使用未纳入文献。

## 11.16 Codex 推荐任务顺序

1. LiteratureExtraction 模型；
2. 十字段 Schema；
3. EvidenceSpan 模型；
4. PDF 定位服务；
5. 抽取 Worker；
6. 字段确认 API；
7. 文献决策；
8. 文献矩阵 API；
9. PDF.js 联动；
10. 证据集合分析；
11. 候选问题；
12. 黄金集测试；
13. M3 E2E。

---
