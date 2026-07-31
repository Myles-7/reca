# M7_EVIDENCE_AND_EXPORT

- 所属入口文档：[IMPLEMENTATION_ROADMAP.md](../../IMPLEMENTATION_ROADMAP.md)
- 文档状态：Conditional Approval
- Migration status: COMPLETE
- Milestone ID: M7

## 权威范围

本文件是 M7 目标、依赖、范围、交付、测试、安全、门禁、阻塞和降级要求的详细路线图。产品范围、字段、API 契约和测试指标仍由对应权威文档定义。

## 不负责的内容

本文件不改变 M1–M9 顺序，不新增 P0，不把 P1 升级，不降低 Competition Core，也不覆盖其他里程碑或公共交付规则。

## 文档导航

- 返回 [IMPLEMENTATION_ROADMAP.md](../../IMPLEMENTATION_ROADMAP.md)
- [DELIVERY_WORKFLOW.md](../DELIVERY_WORKFLOW.md)
- [RISK_SCOPE_AND_RELEASE.md](../RISK_SCOPE_AND_RELEASE.md)
- [M0 Regression Baseline](../../testing/M0_REGRESSION_BASELINE.md)

## 开源复用与安全分层

本里程碑允许选择成熟开源实现，不要求先自行重写或预建复杂 Adapter。依赖、服务、Fork、Vendor、Submodule 或选择性复制必须在同一 PR 完成许可证核验、上游 Commit/Tag、归属和修改记录；无许可证或来源不明内容不得复制。企业生产强化不阻塞 Competition Core，Competition Edition 最小护栏仍必须满足。实际复制 ARS-Codex 内容需要单独记录许可证、归属和架构决定，且不提前 M8 或改变单总控 Agent 边界。

### M7 开源接入步骤

- `Research`：读取 xyflow/React Flow、ReproPackage 实现元数据和相关 ADR-006/ADR-008。
- `Spike`：验证授权图投影、较大图性能、失效/拒绝边显示和表格回退，并生成包含依赖、镜像、上游/Vendor Commit、Prompt、规则、统计引擎和 CSL 标识的 manifest。
- `Decision`：后端 evidence graph/ClaimEvidenceLink 是权威；React Flow 仅可视化，ReproPackage manifest 承载实现可复现信息。
- `Integration`：不得从客户端节点/边反写事实；导出同时验证第三方许可证、缺失项、降级和 Artifact 哈希。

## 里程碑契约覆盖索引

| 必需内容 | 本文件权威位置 |
| --- | --- |
| 目标 | 15.1 |
| 前置依赖 | 15.2 |
| Competition Core | 15.3 中属于 P0-Must / Competition Core 的条目；不得重新分类 |
| P0-Full | 15.3 中明确标为 P0-Full 的条目；未标记者以 PRD 为准 |
| 明确不做 | 15.4 |
| 数据模型 | 15.5 / 15.7 |
| API | 15.8 |
| 前端 | 15.6 |
| 测试 | 15.10 |
| 安全 | 15.11 |
| Prompt / AI | 15.3 / 15.9；无模型任务时不得擅自新增 |
| Codex 推荐任务顺序 | 15.16 |
| 可并行任务 | 15.14 |
| Entry Gate | 15.2 + 公共 Entry Gate |
| Exit Gate | 15.13 + 公共 Exit Gate |
| 阻塞问题 | 15.15 |
| 风险与降级 | 本里程碑原章节 + [RISK_SCOPE_AND_RELEASE.md](../RISK_SCOPE_AND_RELEASE.md) |

M0 Regression Baseline 适用于本里程碑，任何交付不得使 M0 已验收能力退化。以下正文由原路线图对应章节机械迁入，原顺序、依赖和语义不变。

<a id="milestone-m7"></a>

# 15. M7：证据链与复现包

M7 将 `REVISION_DRIFT_AUDIT` finding 与 Claim—Evidence—Analysis/Figure 链接纳入证据图和复现包，而非在 M7 首次定义审核契约。

## 15.1 目标

将文献、原文、数据版本、处理记录、分析、图表、论文 Claim、审批和审核连接成统一证据链，并导出可复现材料。

## 15.2 前置依赖

* M3 完成；
* M5 完成；
* M6 完成。

## 15.3 本阶段范围

```text
ClaimEvidenceLink
AuditResult
EvidenceGraph
EvidenceCompleteness
InvalidationPropagation
Export
ReproPackage
ExportItem
Manifest
```

## 15.4 明确不做

* 不引入 Neo4j；
* 不建设通用知识图谱平台；
* 不构建大规模引文网络；
* 不使用区块链；
* 不将完整敏感数据默认打包；
* 不重新分发无权分发的 PDF。

## 15.5 后端交付物

### ClaimEvidenceLink

关系类型：

```text
SUPPORTED_BY
CONTRADICTED_BY
DERIVED_FROM
TRANSFORMED_FROM
ANALYZED_BY
PRODUCED
VISUALIZED_AS
CONFIRMED_BY
AUDITED_BY
```

必须校验：

* 同项目；
* 来源存在；
* 来源有效；
* 关系类型合法；
* 下游对象状态；
* 证据限制。

### EvidenceGraph

提供：

* 节点；
* 边；
* 节点详情；
* 来源；
* 风险；
* 失效状态；
* 完整度；
* 待补证据；
* 前端布局所需数据。

前端不得自行推断关系。

### AuditResult

审核：

* 文献真实性；
* EvidenceSpan 来源；
* 数据版本；
* 处理审批；
* 分析来源；
* 图表一致性；
* Claim 支持程度；
* 限制；
* 风险等级。

### 失效传播

上游对象失效时：

* 标记受影响下游；
* 不自动删除；
* 记录原因；
* 记录传播路径；
* 生成待复核事项；
* 允许重新运行。

### ReproPackage

目录：

```text
reca-repro-package/
├── 01_research_question/
├── 02_literature/
├── 03_evidence_matrix/
├── 04_dataset_identity/
├── 05_dataset_versions/
├── 06_cleaning_log/
├── 07_analysis_plan/
├── 08_analysis_code/
├── 09_analysis_results/
├── 10_figures/
├── 11_manuscript_check/
├── 12_evidence_graph/
├── 13_agent_and_approval_logs/
├── README_REPRODUCE.md
├── requirements-lock.txt
└── manifest.json
```

Manifest 至少包含：

* 文件路径；
* Artifact ID；
* SHA-256；
* 大小；
* 类型；
* 来源对象；
* 许可证；
* 是否包含敏感数据；
* 是否允许再分发；
* 创建时间；
* 代码版本；
* Schema 版本。

## 15.6 前端交付物

* React Flow 证据链；
* 风险筛选；
* 失效筛选；
* Claim 节点；
* 文献节点；
* EvidenceSpan；
* DatasetVersion；
* DataTransformation；
* AnalysisPlan；
* AnalysisRun；
* AnalysisResult；
* Figure；
* ApprovalRecord；
* AuditResult；
* 节点详情；
* 证据完整度；
* 复现包导出；
* 导出内容预览；
* 许可证和敏感数据提示。

## 15.7 数据库与迁移

至少创建：

```text
claim_evidence_links
audit_results
exports
repro_packages
export_items
```

可选 MAY_EMBED：

```text
evidence_graph_snapshots
evidence_completeness_details
```

关键约束：

* ClaimEvidenceLink 不跨项目；
* ExportItem 不跨项目；
* ReproPackage 不可变；
* 导出失败不产生 AVAILABLE 包；
* Manifest 文件哈希与 Artifact 一致；
* 失效对象保留历史。

## 15.8 API 与契约

核心端点：

```text
POST   /api/v1/claims/{claim_id}/evidence-links
GET    /api/v1/claims/{claim_id}/evidence-links
GET    /api/v1/projects/{project_id}/evidence-graph
POST   /api/v1/claims/{claim_id}/audit-runs
GET    /api/v1/audit-results/{audit_result_id}

POST   /api/v1/projects/{project_id}/exports/repro-package
GET    /api/v1/exports/{export_id}
GET    /api/v1/repro-packages/{repro_package_id}
GET    /api/v1/repro-packages/{repro_package_id}/download
```

## 15.9 确定性工具

* 图关系校验；
* 同项目校验；
* 失效传播；
* 完整度规则；
* 文件收集；
* SHA-256；
* Manifest；
* ZIP 安全生成；
* 许可证检查；
* 敏感数据检查；
* 路径规范化。

AI 只负责：

* 解释证据强弱；
* 建议待补证据；
* 总结限制；
* 解释审核结果。

## 15.10 测试要求

必须覆盖：

* Claim 到 EvidenceSpan；
* Claim 到 AnalysisResult；
* Claim 到 Figure；
* 同项目关系；
* 跨项目关系拒绝；
* 无效来源；
* 上游失效传播；
* 图数据一致；
* 复现包目录；
* Manifest；
* 文件哈希；
* 敏感数据检查；
* 许可证检查；
* ZIP Slip；
* 重复导出幂等；
* 导出失败无正式包；
* 复现说明完整。

## 15.11 安全要求

* 不默认打包原始敏感数据；
* 不打包系统密钥；
* 不打包其他项目文件；
* 受限 PDF 不默认再分发；
* ZIP 路径安全；
* 下载权限校验；
* Manifest 不包含 Token；
* 日志导出脱敏；
* Agent 日志只导出允许字段。

## 15.12 演示成果

```text
点击论文 Claim
→ 查看支持文献
→ 跳转原文页码
→ 查看数据来源
→ 查看数据版本和清洗记录
→ 查看分析计划
→ 查看统计结果
→ 查看图表
→ 查看用户审批
→ 查看可信审核
→ 导出复现包
```

## 15.13 完成条件

1. Claim 能回到真实来源；
2. 图谱关系由后端提供；
3. 跨项目关系被拒绝；
4. 上游失效能传播；
5. AuditResult 可解释风险；
6. ReproPackage 可生成；
7. Manifest 完整；
8. 文件哈希可校验；
9. 许可证和敏感数据检查通过；
10. P0-Must 主闭环除 Agent 外全部完成。

## 15.14 可并行任务

* ClaimEvidenceLink；
* EvidenceGraph API；
* React Flow；
* AuditResult；
* Export；
* Manifest；
* 安全检查。

## 15.15 阻塞下一阶段的缺陷

* 证据关系跨项目；
* 前端自行推断关系；
* 复现包包含其他项目数据；
* Manifest 哈希不正确；
* 失效不传播；
* Claim 无法回到任何来源。

## 15.16 Codex 推荐任务顺序

1. ClaimEvidenceLink；
2. 图查询服务；
3. 证据图 API；
4. React Flow；
5. AuditResult；
6. 失效传播；
7. Export；
8. Manifest；
9. ZIP 生成；
10. 安全和许可证检查；
11. M7 E2E。

---
