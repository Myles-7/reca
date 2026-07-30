# M4_DATA_QUALITY

- 所属入口文档：[IMPLEMENTATION_ROADMAP.md](../../IMPLEMENTATION_ROADMAP.md)
- 文档状态：Conditional Approval
- Migration status: COMPLETE
- Milestone ID: M4

## 权威范围

本文件是 M4 目标、依赖、范围、交付、测试、安全、门禁、阻塞和降级要求的详细路线图。产品范围、字段、API 契约和测试指标仍由对应权威文档定义。

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
| 目标 | 12.1 |
| 前置依赖 | 12.2 |
| Competition Core | 12.3 中属于 P0-Must / Competition Core 的条目；不得重新分类 |
| P0-Full | 12.3 中明确标为 P0-Full 的条目；未标记者以 PRD 为准 |
| 明确不做 | 12.4 |
| 数据模型 | 12.5 / 12.7 |
| API | 12.8 |
| 前端 | 12.6 |
| 测试 | 12.10 |
| 安全 | 12.11 |
| Prompt / AI | 12.3 / 12.9；无模型任务时不得擅自新增 |
| Codex 推荐任务顺序 | 12.16 |
| 可并行任务 | 12.14 |
| Entry Gate | 12.2 + 公共 Entry Gate |
| Exit Gate | 12.13 + 公共 Exit Gate |
| 阻塞问题 | 12.15 |
| 风险与降级 | 本里程碑原章节 + [RISK_SCOPE_AND_RELEASE.md](../RISK_SCOPE_AND_RELEASE.md) |

M0 Regression Baseline 适用于本里程碑，任何交付不得使 M0 已验收能力退化。以下正文由原路线图对应章节机械迁入，原顺序、依赖和语义不变。

<a id="milestone-m4"></a>

# 12. M4：数据质量与版本

## 12.1 目标

建立从数据上传、身份登记、质量检查、处理计划、用户审批到新数据版本的可追溯链路。

## 12.2 前置依赖

M1 完成。

M4 可与 M2、M3 的后半部分并行，但必须复用 M1 的 Artifact、Approval、Job 和 Audit。

## 12.3 本阶段范围

```text
Dataset
DatasetVersion
DatasetColumn
DataQualityRun
DataQualityIssue
CleaningPlan
CleaningPlanAction
DataTransformation
```

支持：

```text
CSV
XLSX
```

## 12.4 明确不做

* 不执行用户 Python；
* 不执行任意 SQL；
* 不执行任意表达式；
* 不自动删除异常值；
* 不自动插补缺失值；
* 不自动修改原始数据；
* 不支持任意数据格式；
* 不建设完整 ETL 平台。

## 12.5 后端交付物

### Dataset

* 创建 Dataset；
* 数据身份证；
* 来源；
* 发布者；
* 平台；
* DOI 或标识；
* 获取日期；
* 许可证；
* 推荐引用；
* 限制；
* 当前版本。

### DatasetVersion

* Original DatasetVersion；
* 父版本；
* 版本号；
* Artifact；
* SHA-256；
* 行列数；
* 工作表；
* 版本状态；
* 不可变；
* 失效。

### DatasetColumn

* 字段名；
* 显示名；
* 推断类型；
* 用户确认类型；
* 变量角色；
* 单位；
* 缺失编码；
* 敏感性；
* 枚举信息。

### DataQualityRun

检查：

* 缺失；
* 重复行；
* 重复 ID；
* 常量列；
* 混合类型；
* 类别不一致；
* 越界；
* 极端值；
* 分组不平衡；
* 单位疑似不一致；
* 日期异常；
* 手机号；
* 身份证号；
* 学号；
* 其他疑似敏感字段。

### CleaningPlan

* 白名单操作；
* 输入版本；
* 操作参数；
* 受影响记录；
* 预览；
* 风险；
* 审批要求；
* 状态机。

### DataTransformation

* 仅执行 APPROVED CleaningPlan；
* Worker 重新校验；
* 生成新 Artifact；
* 生成新 DatasetVersion；
* 保存父版本；
* 保存参数；
* 保存受影响记录；
* 保存日志；
* 保存 ApprovalRecord；
* 执行后重新质量检查。

## 12.6 前端交付物

* 数据上传；
* 工作表选择；
* 数据预览；
* 数据身份证；
* 字段字典；
* 数据版本列表；
* 质量问题列表；
* 严重程度筛选；
* 受影响记录预览；
* CleaningPlan；
* 操作预览；
* 批准或驳回；
* 转换 Job；
* 新旧版本对比；
* 数据血缘。

## 12.7 数据库与迁移

至少创建：

```text
datasets
dataset_versions
dataset_columns
data_quality_runs
data_quality_issues
cleaning_plans
cleaning_plan_actions
data_transformations
```

关键约束：

* Original DatasetVersion 无父版本；
* Original DatasetVersion 不可变；
* 新版本必须有父版本；
* DataTransformation 必须绑定 CleaningPlan；
* CleaningPlan 执行必须绑定有效 ApprovalRecord；
* 版本号同 Dataset 唯一；
* Artifact 不允许覆盖。

## 12.8 API 与契约

核心端点：

```text
POST   /api/v1/projects/{project_id}/datasets
GET    /api/v1/datasets/{dataset_id}
GET    /api/v1/datasets/{dataset_id}/versions
GET    /api/v1/dataset-versions/{dataset_version_id}
GET    /api/v1/dataset-versions/{dataset_version_id}/preview

POST   /api/v1/dataset-versions/{dataset_version_id}/quality-runs
GET    /api/v1/data-quality-runs/{data_quality_run_id}

POST   /api/v1/dataset-versions/{dataset_version_id}/cleaning-plans
PATCH  /api/v1/cleaning-plans/{cleaning_plan_id}
GET    /api/v1/cleaning-plans/{cleaning_plan_id}/preview
POST   /api/v1/cleaning-plans/{cleaning_plan_id}/request-approval
POST   /api/v1/cleaning-plans/{cleaning_plan_id}/execute
```

## 12.9 确定性工具

* CSV 编码检测；
* XLSX 结构读取；
* 行列限制；
* 数据类型推断；
* Pandera；
* 缺失检测；
* 重复检测；
* 范围规则；
* 极端值规则；
* 敏感字段规则；
* 白名单数据转换；
* 数据版本哈希；
* 转换差异统计。

AI 只负责：

* 解释质量问题；
* 建议 CleaningPlan；
* 解释操作影响。

AI 不负责：

* 计算问题数量；
* 执行数据修改；
* 批准计划；
* 判断异常值必然错误。

## 12.10 测试要求

必须覆盖：

* 正常 CSV；
* 正常 XLSX；
* 多工作表；
* 缺失；
* 重复；
* 混合类型；
* 类别不一致；
* 极端值；
* 单位疑似不一致；
* 敏感字段；
* 未批准计划拒绝；
* 原始哈希不变；
* 新版本父关系；
* 转换幂等；
* 失败不生成 AVAILABLE 版本；
* CSV 公式注入；
* XLSX 外部链接不访问；
* 超大文件限制。

## 12.11 安全要求

* CSV/XLSX 不可信；
* 限制行列和单元格长度；
* 不执行公式；
* 不访问外部连接；
* 识别隐藏工作表；
* 敏感字段默认不发送模型；
* 清洗计划不允许代码；
* Worker 不信任队列消息；
* 导出处理公式注入。

## 12.12 演示成果

```text
上传数据
→ 查看数据身份证
→ 查看原始版本
→ 运行质量检查
→ 查看缺失、重复和异常
→ 生成 CleaningPlan
→ 预览受影响记录
→ 用户批准
→ 执行转换
→ 生成新 DatasetVersion
→ 查看版本血缘
```

## 12.13 完成条件

1. CSV/XLSX 可上传；
2. Original DatasetVersion 不可变；
3. 基础质量问题可确定性检出；
4. CleaningPlan 仅允许白名单；
5. 未批准计划无法执行；
6. 转换生成新 Artifact 和新版本；
7. 原始哈希保持不变；
8. 处理日志和父版本完整；
9. 失败不会留下正式半成品。

## 12.14 可并行任务

* 数据解析；
* 数据身份证；
* 质量规则；
* CleaningPlan；
* 前端数据表；
* 黄金数据集。

## 12.15 阻塞下一阶段的缺陷

* 原始数据可覆盖；
* 未审批可转换；
* CleaningPlan 可执行任意代码；
* 转换失败产生正式版本；
* 数据版本无父关系；
* 敏感字段默认发送模型。

## 12.16 Codex 推荐任务顺序

1. Dataset 和 DatasetVersion；
2. CSV/XLSX Adapter；
3. DatasetColumn；
4. 数据预览；
5. DataQualityRun；
6. 质量规则；
7. CleaningPlan；
8. 预览；
9. Approval 集成；
10. DataTransformation；
11. 新版本；
12. 前端工作台；
13. 黄金测试；
14. M4 E2E。

---
