# M5_ANALYSIS_AND_FIGURES

- 所属入口文档：[IMPLEMENTATION_ROADMAP.md](../../IMPLEMENTATION_ROADMAP.md)
- 文档状态：Conditional Approval
- Migration status: COMPLETE
- Milestone ID: M5

## 权威范围

本文件是 M5 目标、依赖、范围、交付、测试、安全、门禁、阻塞和降级要求的详细路线图。产品范围、字段、API 契约和测试指标仍由对应权威文档定义。

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
| 目标 | 13.1 |
| 前置依赖 | 13.2 |
| Competition Core | 13.3 中属于 P0-Must / Competition Core 的条目；不得重新分类 |
| P0-Full | 13.3 中明确标为 P0-Full 的条目；未标记者以 PRD 为准 |
| 明确不做 | 13.4 |
| 数据模型 | 13.5 / 13.7 |
| API | 13.8 |
| 前端 | 13.6 |
| 测试 | 13.10 |
| 安全 | 13.11 |
| Prompt / AI | 13.3 / 13.9；无模型任务时不得擅自新增 |
| Codex 推荐任务顺序 | 13.16 |
| 可并行任务 | 13.14 |
| Entry Gate | 13.2 + 公共 Entry Gate |
| Exit Gate | 13.13 + 公共 Exit Gate |
| 阻塞问题 | 13.15 |
| 风险与降级 | 本里程碑原章节 + [RISK_SCOPE_AND_RELEASE.md](../RISK_SCOPE_AND_RELEASE.md) |

M0 Regression Baseline 适用于本里程碑，任何交付不得使 M0 已验收能力退化。以下正文由原路线图对应章节机械迁入，原顺序、依赖和语义不变。

<a id="milestone-m5"></a>

# 13. M5：统计分析与图表

## 13.1 目标

使用确定性统计程序生成可复现分析结果和科研图表。

## 13.2 前置依赖

M4 完成。

## 13.3 本阶段范围

```text
AnalysisPlan
AnalysisAssumptionCheck
AnalysisRun
AnalysisResult
CodeArtifact
FigurePlan
FigureRenderRun
Figure
FigureValidationIssue
```

P0-Must 方法：

```text
DESCRIPTIVE_STATISTICS
PEARSON_CORRELATION
SPEARMAN_CORRELATION
```

P0-Full 方法：

```text
INDEPENDENT_TWO_GROUP
PAIRED_TWO_GROUP
SIMPLE_LINEAR_REGRESSION
```

P0-Must 图表：

```text
SCATTER
GROUP_COMPARISON
```

P0-Full 图表：

```text
HISTOGRAM
BOXPLOT
CORRELATION_MATRIX
```

## 13.4 明确不做

* 不让模型生成统计数字；
* 不执行用户代码；
* 不支持任意统计方法；
* 不自动选择并运行方法；
* 不隐藏不显著结果；
* 不通过修改数据获得显著性；
* 不进行复杂多元模型。

## 13.5 后端交付物

### AnalysisPlan

绑定：

* ResearchQuestionVersion；
* DatasetVersion；
* 变量；
* 变量角色；
* 方法；
* 缺失策略；
* 参数；
* 前提检查；
* 用户确认；
* ApprovalRecord。

### AnalysisAssumptionCheck

至少包含：

* 数据类型；
* 样本量；
* 缺失；
* 常量列；
* 配对关系；
* 独立性确认；
* 正态性提示；
* 方差；
* 线性；
* 极端值；
* 有效样本数。

### AnalysisRun

* 创建 Job；
* 重新校验 Approval；
* 重新校验 DatasetVersion；
* 幂等；
* 运行环境；
* 依赖版本；
* 代码模板；
* 日志；
* 状态；
* 失败信息。

### AnalysisResult

正式数字包括：

* N；
* 缺失；
* 均值；
* 标准差；
* 中位数；
* 四分位数；
* 最小值；
* 最大值；
* 相关系数；
* p 值；
* 置信区间；
* 回归系数；
* 效应量；
* 方法警告。

所有数字来自确定性程序。

### Figure

* FigurePlan；
* FigureRenderRun；
* Figure；
* 图像 Artifact；
* 代码 Artifact；
* 图注；
* 数据版本；
* AnalysisRun；
* 参数；
* 规范检查；
* 用户确认；
* 失效。

## 13.6 前端交付物

* 变量选择；
* 变量角色；
* 方法建议；
* 前提检查；
* AnalysisPlan；
* 批准；
* AnalysisRun 进度；
* 结构化结果；
* 警告；
* 结果解释；
* 图表类型；
* 图表预览；
* 图注；
* 图表规范问题；
* 图表确认；
* PNG/SVG/PDF 导出。

## 13.7 数据库与迁移

至少创建：

```text
analysis_plans
analysis_assumption_checks
analysis_runs
analysis_results
code_artifacts
figure_plans
figure_render_runs
figures
figure_validation_issues
```

关键约束：

* AnalysisPlan 必须绑定 DatasetVersion；
* AnalysisRun 必须绑定 APPROVED AnalysisPlan；
* AnalysisResult 不可变；
* Figure 必须绑定 DatasetVersion；
* 图表引用的 AnalysisRun 必须属于同项目；
* FigureRenderRun 状态与 Figure 状态分离；
* 失效保留历史。

## 13.8 API 与契约

核心端点：

```text
POST   /api/v1/projects/{project_id}/analysis-plans
GET    /api/v1/analysis-plans/{analysis_plan_id}
PATCH  /api/v1/analysis-plans/{analysis_plan_id}
POST   /api/v1/analysis-plans/{analysis_plan_id}/validate
POST   /api/v1/analysis-plans/{analysis_plan_id}/request-approval
POST   /api/v1/analysis-plans/{analysis_plan_id}/runs

GET    /api/v1/analysis-runs/{analysis_run_id}
GET    /api/v1/analysis-results/{analysis_result_id}

POST   /api/v1/projects/{project_id}/figure-plans
POST   /api/v1/figure-plans/{figure_plan_id}/render
GET    /api/v1/figures/{figure_id}
POST   /api/v1/figures/{figure_id}/confirm
```

## 13.9 确定性工具

* pandas；
* NumPy；
* SciPy；
* statsmodels；
* Matplotlib；
* 固定统计模板；
* 固定绘图模板；
* 依赖版本记录；
* 代码 Artifact；
* 结果 Schema；
* 图表数据一致性检查。

AI 只负责：

* 推荐方法；
* 解释前提；
* 解释结果；
* 推荐图表；
* 生成图注草稿。

AI 不得：

* 计算 p 值；
* 修改系数；
* 修改 N；
* 生成不存在的显著性；
* 隐藏不显著结果；
* 将相关解释为因果。

## 13.10 测试要求

必须建立独立统计黄金集。

覆盖：

* 描述统计；
* 完全正相关；
* 完全负相关；
* 接近零相关；
* Pearson 与 Spearman 差异；
* 缺失；
* 常量列；
* 有效样本过少；
* 极端值；
* 独立两组；
* 配对两组；
* 简单回归；
* 数值容差；
* 重复运行；
* 幂等；
* 未批准计划拒绝；
* 图表数据一致；
* 图表代码可复现。

## 13.11 安全要求

* 不执行用户代码；
* 不加载不可信序列化对象；
* Worker 限制内存和时间；
* 输入版本必须可用；
* AnalysisResult 不允许模型写入；
* 代码 Artifact 由系统模板生成；
* 图表文件使用新 Artifact；
* 下载前校验项目权限。

## 13.12 演示成果

```text
选择新 DatasetVersion
→ 选择变量
→ 查看方法建议
→ 查看前提检查
→ 创建 AnalysisPlan
→ 用户批准
→ 运行确定性统计
→ 查看结构化结果
→ 生成散点图
→ 查看图表代码和数据来源
```

## 13.13 完成条件

1. 描述统计正确；
2. Pearson 或 Spearman 正确；
3. AnalysisPlan 与 AnalysisRun 分离；
4. 未批准计划无法运行；
5. 正式数字来自 StatisticalEngine；
6. AnalysisResult 不可变；
7. 图表绑定正确数据版本和分析运行；
8. 图表与结果一致；
9. 统计黄金测试通过；
10. 相同输入重复结果一致。

## 13.14 可并行任务

* 统计引擎；
* 前提检查；
* AnalysisPlan；
* 图表引擎；
* 前端分析页；
* 黄金测试。

## 13.15 阻塞下一阶段的缺陷

* 模型写正式数字；
* AnalysisPlan 未批准可运行；
* 数值黄金测试失败；
* 图表使用错误数据版本；
* 图表和统计结果不一致；
* 运行结果可原地修改。

## 13.16 Codex 推荐任务顺序

1. AnalysisPlan；
2. 前提检查；
3. StatisticalEngine Protocol；
4. 描述统计；
5. Pearson/Spearman；
6. AnalysisRun；
7. AnalysisResult；
8. 代码 Artifact；
9. FigurePlan；
10. Matplotlib Adapter；
11. 图表验证；
12. 前端；
13. 黄金测试；
14. P0-Full 方法；
15. M5 E2E。

---
