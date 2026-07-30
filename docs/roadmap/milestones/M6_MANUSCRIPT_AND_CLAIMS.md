# M6_MANUSCRIPT_AND_CLAIMS

- 所属入口文档：[IMPLEMENTATION_ROADMAP.md](../../IMPLEMENTATION_ROADMAP.md)
- 文档状态：Conditional Approval
- Migration status: COMPLETE
- Milestone ID: M6

## 权威范围

本文件是 M6 目标、依赖、范围、交付、测试、安全、门禁、阻塞和降级要求的详细路线图。产品范围、字段、API 契约和测试指标仍由对应权威文档定义。

## 不负责的内容

本文件不改变 M1–M9 顺序，不新增 P0，不把 P1 升级，不降低 Competition Core，也不覆盖其他里程碑或公共交付规则。

## 文档导航

- 返回 [IMPLEMENTATION_ROADMAP.md](../../IMPLEMENTATION_ROADMAP.md)
- [DELIVERY_WORKFLOW.md](../DELIVERY_WORKFLOW.md)
- [RISK_SCOPE_AND_RELEASE.md](../RISK_SCOPE_AND_RELEASE.md)
- [M0 Regression Baseline](../../testing/M0_REGRESSION_BASELINE.md)

## 里程碑契约覆盖索引

| 必需内容 | 本文件权威位置 |
| --- | --- |
| 目标 | 14.1 |
| 前置依赖 | 14.2 |
| Competition Core | 14.3 中属于 P0-Must / Competition Core 的条目；不得重新分类 |
| P0-Full | 14.3 中明确标为 P0-Full 的条目；未标记者以 PRD 为准 |
| 明确不做 | 14.4 |
| 数据模型 | 14.5 / 14.7 |
| API | 14.8 |
| 前端 | 14.6 |
| 测试 | 14.10 |
| 安全 | 14.11 |
| Prompt / AI | 14.9；无模型任务时不得擅自新增 |
| Codex 推荐任务顺序 | 14.16 |
| 可并行任务 | 14.14 |
| Entry Gate | 14.2 + 公共 Entry Gate |
| Exit Gate | 14.13 + 公共 Exit Gate |
| 阻塞问题 | 14.15 |
| 风险与降级 | 本里程碑原章节 + [RISK_SCOPE_AND_RELEASE.md](../RISK_SCOPE_AND_RELEASE.md) |

M0 Regression Baseline 适用于本里程碑，任何交付不得使 M0 已验收能力退化。以下正文由原路线图对应章节机械迁入，原顺序、依赖和语义不变。

<a id="milestone-m6"></a>

# 14. M6：DOCX 与 Claim

`MANU-P0-018` 是 M6 交付：创建 `MANUSCRIPT_REVISION_AUDIT` Job 与 `REVISION_DRIFT_AUDIT` AuditResult。Competition Core 检查数字/统计量、引用删除、因果词升级与 Figure/AnalysisResult/DatasetVersion 不一致；P0-Full 才可加入模型辅助语义漂移。审核只读、输入版本和结果版本可追溯，绝不改写原 DOCX。

## 14.1 目标

检查 DOCX 论文草稿中的核心科研风险，并将论文论述转化为可追踪 Claim。

## 14.2 前置依赖

* M3 完成；
* M5 完成；
* M1 的 Artifact 和 Job 可用。

## 14.3 本阶段范围

```text
Manuscript
ManuscriptVersion
ManuscriptCheckRun
ManuscriptIssue
ManuscriptIssueEvidence
ManuscriptTransformation
Claim
```

P0-Must 检查：

* 文内引用无文末条目；
* 文末条目正文未引用；
* 样本量前后不一致；
* 正文数字与 AnalysisResult 不一致；
* 相关写成因果；
* 结论超出样本；
* 术语不一致；
* 图表编号基础错误。

## 14.4 明确不做

* 不支持 DOC；
* 不支持 DOCM；
* 不完整重排 Word；
* 不自动修改高风险科研内容；
* 不自动修改统计数字；
* 不自动修改引用结论；
* 不自动生成完整论文；
* 不实现精确查重；
* 不实现自动降重。

## 14.5 后端交付物

### Manuscript

* 逻辑 Manuscript；
* Original ManuscriptVersion；
* Artifact；
* 版本；
* 不可变；
* 解析状态；
* 结构摘要。

### DOCX 解析

* 段落；
* 标题；
* 表格；
* 图表引用；
* 文内引用；
* 参考文献；
* 数字；
* 术语；
* OOXML 关系；
* 不支持结构提示。

### ManuscriptCheckRun

检查：

* 引用双向匹配；
* 作者年份；
* 重复参考文献；
* DOI 格式；
* 样本量；
* p 值；
* 相关系数；
* 回归系数；
* 图表数字；
* 因果语言；
* 样本外推；
* 共识夸大；
* 术语一致；
* 基础格式。

### ManuscriptIssue

至少保存：

* 类型；
* 严重程度；
* 位置；
* 原文；
* 证据；
* 建议；
* 是否可自动修复；
* 用户决定；
* 状态。

### Claim

支持：

* 用户创建 Claim；
* 从论文段落建议 Claim；
* Claim 类型；
* Claim 文本；
* 来源段落；
* 确认状态；
* 风险状态；
* 限制说明。

## 14.6 前端交付物

* DOCX 上传；
* ManuscriptVersion；
* 检查进度；
* 问题列表；
* 严重程度筛选；
* 原文定位；
* 分析结果对照；
* 文献证据对照；
* 采纳或驳回；
* 低风险修复预览；
* Claim 创建；
* Claim 确认。

## 14.7 数据库与迁移

至少创建：

```text
manuscripts
manuscript_versions
manuscript_check_runs
manuscript_issues
manuscript_issue_evidence
manuscript_transformations
claims
```

关键约束：

* Original ManuscriptVersion 不可变；
* 修改生成新 Artifact 和新版本；
* ManuscriptIssue 不覆盖原文；
* 高风险问题不能自动修复；
* Claim 必须属于项目；
* Claim 来源段落可定位；
* 用户确认需要 ApprovalRecord 或确认记录。

## 14.8 API 与契约

核心端点：

```text
POST   /api/v1/projects/{project_id}/manuscripts
GET    /api/v1/manuscripts/{manuscript_id}
GET    /api/v1/manuscripts/{manuscript_id}/versions

POST   /api/v1/manuscript-versions/{manuscript_version_id}/check-runs
GET    /api/v1/manuscript-check-runs/{manuscript_check_run_id}
GET    /api/v1/manuscript-issues/{manuscript_issue_id}
POST   /api/v1/manuscript-issues/{manuscript_issue_id}/accept
POST   /api/v1/manuscript-issues/{manuscript_issue_id}/reject

POST   /api/v1/projects/{project_id}/claims
PATCH  /api/v1/claims/{claim_id}
POST   /api/v1/claims/{claim_id}/confirm
```

## 14.9 确定性工具与 AI

确定性工具负责：

* DOCX ZIP 安全；
* OOXML 解析；
* 引用匹配；
* 数字提取；
* 与 AnalysisResult 对比；
* 图表编号；
* 术语频次；
* 低风险格式修复。

AI 负责：

* 因果语言语义审核；
* 样本外推解释；
* 共识夸大建议；
* Claim 候选提取；
* 修改建议。

AI 不得：

* 修改正式统计数字；
* 自动采纳高风险修改；
* 覆盖原 DOCX；
* 生成无法定位的引用证据。

## 14.10 测试要求

DOCX 黄金集至少覆盖：

* 正常论文；
* 引用缺失；
* 未引用条目；
* 作者年份错误；
* 重复参考文献；
* 样本量不一致；
* p 值不一致；
* 相关写成因果；
* 样本外推；
* 术语不一致；
* 图表编号；
* 复杂表格；
* 公式；
* 损坏文件；
* 伪装文件；
* ZIP Slip；
* 压缩炸弹。

## 14.11 安全要求

* DOCX 作为 ZIP；
* 防 ZIP Slip；
* 限制解压大小和文件数；
* 不访问外部关系；
* 不执行宏；
* 不支持 DOCM；
* 不访问远程模板；
* 不下载远程图片；
* 修复生成新文件；
* 失败不产生正式版本。

## 14.12 演示成果

```text
上传 DOCX
→ 解析论文结构
→ 检查引用
→ 核对样本量和统计数字
→ 标记相关写成因果
→ 展示问题证据
→ 用户采纳或驳回
→ 创建 Claim
```

## 14.13 完成条件

1. DOCX 可安全解析；
2. 引用和数字核心检查可用；
3. 正文数字可映射 AnalysisResult；
4. 高风险问题只给建议；
5. 原 DOCX 不覆盖；
6. Claim 可创建和确认；
7. Issue 可定位到原文；
8. DOCX 安全测试通过。

## 14.14 可并行任务

* DOCX 安全解析；
* 引用规则；
* 数字核对；
* 语义审核；
* 前端问题页；
* Claim 模型。

## 14.15 阻塞下一阶段的缺陷

* DOCX 可路径逃逸；
* 外部关系自动访问；
* 原文件覆盖；
* 正文数字无法关联 AnalysisResult；
* Claim 无来源；
* 高风险修改自动执行。

## 14.16 Codex 推荐任务顺序

1. Manuscript 和版本；
2. DOCX 安全解析；
3. 引用规则；
4. 数字规则；
5. 语义规则；
6. ManuscriptIssue；
7. 前端问题页；
8. Claim；
9. 用户决定；
10. 黄金测试；
11. M6 E2E。

---
