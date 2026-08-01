# DATA_ANALYSIS_AND_FIGURE_API

- 所属入口文档：[API_AI_TOOL_CONTRACTS.md](../API_AI_TOOL_CONTRACTS.md)
- 文档状态：APPROVED FOR M1 DEVELOPMENT
- Migration status: COMPLETE

## 权威范围

Dataset、DatasetVersion、质量检查、CleaningPlan、DataTransformation、AnalysisPlan/Run/Result 和 Figure API 的唯一完整定义。

## 不负责的内容

不定义论文、证据图、AI 输出 Schema 或 Agent Tool；统计结果仍由确定性程序产生。

## 文档导航

- 返回 [API_AI_TOOL_CONTRACTS.md](../API_AI_TOOL_CONTRACTS.md)
- [COMMON_API_JOB_AND_SSE_CONTRACTS.md](COMMON_API_JOB_AND_SSE_CONTRACTS.md)
- [PROJECT_RESEARCH_AND_LITERATURE_API.md](PROJECT_RESEARCH_AND_LITERATURE_API.md)
- [DATA_ANALYSIS_AND_FIGURE_API.md](DATA_ANALYSIS_AND_FIGURE_API.md)
- [MANUSCRIPT_EVIDENCE_AND_EXPORT_API.md](MANUSCRIPT_EVIDENCE_AND_EXPORT_API.md)
- [AI_SCHEMA_CONTRACTS.md](AI_SCHEMA_CONTRACTS.md)
- [AGENT_TOOL_CONTRACTS.md](AGENT_TOOL_CONTRACTS.md)

以下正文由原入口文档对应章节机械迁入。路径、字段、错误码、Schema、Tool 名称和契约语义保持原样。


# 19. Datasets API

## 19.1 上传数据集

```http id="2y20jl"
POST /api/v1/projects/{project_id}/datasets
Content-Type: multipart/form-data
```

字段：

```text id="938r0m"
file
name
source_type
publisher
source_platform
source_identifier
license_name
license_status
```

响应创建 Dataset 和 Original DatasetVersion。

---

## 19.2 数据集列表

```http id="32sxce"
GET /api/v1/projects/{project_id}/datasets
```

---

## 19.3 数据集详情

```http id="k1ao5i"
GET /api/v1/datasets/{dataset_id}
```

---

## 19.4 更新数据身份证

```http id="6pj07f"
PATCH /api/v1/datasets/{dataset_id}
If-Match: "2"
```

---

## 19.5 数据版本详情

```http id="dtthth"
GET /api/v1/dataset-versions/{version_id}
```

---

## 19.6 数据预览

```http id="itw2i4"
GET /api/v1/dataset-versions/{version_id}/preview
```

参数：

```text id="3b5wpk"
offset
limit
columns
```

最大预览行数建议 200。

---

## 19.7 字段列表

```http id="mt4zi0"
GET /api/v1/dataset-versions/{version_id}/columns
```

---

## 19.8 更新字段定义

```http id="rxokg8"
PATCH /api/v1/dataset-columns/{column_id}
If-Match: "1"
```

请求：

```json id="j3w4cy"
{
  "display_name": "生成式AI使用频率",
  "confirmed_type": "NUMERIC",
  "semantic_role": "INDEPENDENT_VARIABLE",
  "unit": "次/周",
  "description": "过去一周使用生成式AI的次数",
  "confirmation_status": "CONFIRMED"
}
```

---

## 19.9 数据版本比较

```http id="99icgb"
GET /api/v1/datasets/{dataset_id}/version-comparison
```

参数：

```text id="dm6ty9"
from_version_id
to_version_id
```

---

# 20. 数据质量与清洗 API

## 20.1 启动质量检查

```http id="7aatg7"
POST /api/v1/dataset-versions/{version_id}/quality-runs
Idempotency-Key: <key>
```

请求：

```json id="urudc4"
{
  "rule_set": "RECA_P0_DEFAULT",
  "include_sensitive_field_detection": true
}
```

返回 Job。

---

## 20.2 获取质量检查

```http id="4vimhl"
GET /api/v1/data-quality-runs/{run_id}
```

## 20.3 获取问题列表

```http id="yp98qt"
GET /api/v1/data-quality-runs/{run_id}/issues
```

过滤：

```text id="zgkcar"
severity
issue_type
status
column_id
```

---

## 20.4 标记问题

```http id="nv16w2"
POST /api/v1/data-quality-issues/{issue_id}/acknowledge
```

或：

```http id="yr3tsw"
POST /api/v1/data-quality-issues/{issue_id}/ignore
```

忽略需要原因。

---

## 20.5 创建 CleaningPlan

```http id="exk74c"
POST /api/v1/dataset-versions/{version_id}/cleaning-plans
```

请求：

```json id="q565v9"
{
  "title": "统一缺失编码和性别分类",
  "rationale": "将999标记为缺失，并统一性别编码。",
  "actions": [
    {
      "action_type": "MARK_MISSING",
      "target_columns": ["uuid"],
      "row_selector": {
        "operator": "VALUE_EQUALS",
        "value": 999
      },
      "parameters": {
        "replacement": null
      },
      "reason": "999为数据说明中的缺失编码。",
      "source_issue_ids": ["uuid"]
    },
    {
      "action_type": "MAP_CATEGORY",
      "target_columns": ["uuid"],
      "parameters": {
        "mapping": {
          "M": "男",
          "male": "男",
          "F": "女",
          "female": "女"
        }
      },
      "reason": "统一类别编码。"
    }
  ]
}
```

---

## 20.6 AI 建议 CleaningPlan

```http id="ae76ax"
POST /api/v1/dataset-versions/{version_id}/cleaning-plan-suggestions
Idempotency-Key: <key>
```

AI 只生成建议，不执行。

---

## 20.7 获取处理预览

```http id="yl066q"
POST /api/v1/cleaning-plans/{plan_id}/preview
Idempotency-Key: <key>
```

响应：

```json id="6rdupu"
{
  "data": {
    "cleaning_plan_id": "uuid",
    "source_dataset_version_id": "uuid",
    "affected_row_count": 36,
    "affected_column_count": 2,
    "row_count_before": 1020,
    "row_count_after": 1020,
    "sample_changes": [],
    "warnings": [],
    "ready_for_approval": true
  }
}
```

---

## 20.8 请求审批

```http id="o7840q"
POST /api/v1/cleaning-plans/{plan_id}/approval-requests
```

---

## 20.9 执行批准计划

```http id="0n01gz"
POST /api/v1/cleaning-plans/{plan_id}/execute
Idempotency-Key: <key>
```

前置：

* Plan 状态为 APPROVED；
* Approval 未失效；
* Source DatasetVersion 可用；
* Plan 内容哈希与审批快照一致。

返回 Job。

---

# 21. Analysis API

## 21.1 创建 AnalysisPlan

```http id="spb7kf"
POST /api/v1/projects/{project_id}/analysis-plans
```

请求：

```json id="dv3ts4"
{
  "research_question_version_id": "uuid",
  "dataset_version_id": "uuid",
  "analysis_goal": "CORRELATION",
  "method": "PEARSON_CORRELATION",
  "dependent_variable_ids": ["uuid"],
  "independent_variable_ids": ["uuid"],
  "control_variable_ids": [],
  "missing_data_policy": {
    "mode": "PAIRWISE_COMPLETE"
  },
  "sample_filter": null,
  "parameters": {
    "confidence_level": 0.95
  }
}
```

---

## 21.2 AI 建议 AnalysisPlan

```http id="se5k2j"
POST /api/v1/projects/{project_id}/analysis-plan-suggestions
Idempotency-Key: <key>
```

请求必须包括：

* 研究问题版本；
* 数据版本；
* 已确认字段角色；
* 用户分析目标。

---

## 21.3 验证前提

```http id="m2bxzx"
POST /api/v1/analysis-plans/{plan_id}/validate
Idempotency-Key: <key>
```

可同步或异步。

响应：

```json id="1zgw5g"
{
  "data": {
    "analysis_plan_id": "uuid",
    "status": "READY",
    "checks": [
      {
        "check_code": "DATA_TYPE",
        "status": "PASSED",
        "explanation": "两个变量均已确认为数值型。"
      },
      {
        "check_code": "LINEARITY",
        "status": "WARNING",
        "explanation": "散点关系存在轻微非线性迹象。"
      }
    ],
    "warnings": [
      "相关分析不支持因果解释。"
    ]
  }
}
```

---

## 21.4 更新 AnalysisPlan

```http id="jz6fnz"
PATCH /api/v1/analysis-plans/{plan_id}
If-Match: "2"
```

仅 DRAFT、NEEDS_INPUT、READY 状态可修改。

---

## 21.5 请求审批

```http id="6bt7rd"
POST /api/v1/analysis-plans/{plan_id}/approval-requests
```

---

## 21.6 执行分析

```http id="w29jby"
POST /api/v1/analysis-plans/{plan_id}/runs
Idempotency-Key: <key>
```

请求：

```json id="qpyon2"
{
  "run_reason": "执行已确认的主演示相关分析。"
}
```

前置：

* Plan 已批准；
* 数据版本可用；
* 变量确认；
* 方法 P0 支持；
* 审批快照一致。

返回 Job 和 AnalysisRun ID。

---

## 21.7 AnalysisRun 详情

```http id="ilwfqv"
GET /api/v1/analysis-runs/{run_id}
```

---

## 21.8 AnalysisResult

```http id="mixw79"
GET /api/v1/analysis-runs/{run_id}/results
```

示例：

```json id="eyawpo"
{
  "data": {
    "analysis_run_id": "uuid",
    "dataset_version_id": "uuid",
    "method": "PEARSON_CORRELATION",
    "variables": [
      {
        "column_id": "uuid",
        "role": "X",
        "display_name": "生成式AI使用频率"
      },
      {
        "column_id": "uuid",
        "role": "Y",
        "display_name": "学习投入"
      }
    ],
    "sample_size": 984,
    "statistics": {
      "coefficient": 0.31,
      "p_value": 0.00001
    },
    "confidence_intervals": {
      "coefficient": {
        "lower": 0.25,
        "upper": 0.37,
        "level": 0.95
      }
    },
    "assumption_results": [],
    "warnings": [
      "该结果仅表示相关关系，不支持因果推断。"
    ],
    "environment": {
      "python": "3.11.x",
      "scipy": "locked-version",
      "pandas": "locked-version"
    },
    "code_artifact_id": "uuid",
    "created_at": "2026-07-29T09:00:00Z"
  }
}
```

---

## 21.9 AI 解释分析结果

```http id="ha1e0o"
POST /api/v1/analysis-runs/{run_id}/interpretations
Idempotency-Key: <key>
```

AI 输入只读取结构化结果。

输出不得出现输入中不存在的新数字。

---

## 21.10 失效 AnalysisRun

```http id="hd0awz"
POST /api/v1/analysis-runs/{run_id}/invalidate
```

请求：

```json id="mtlfqp"
{
  "reason": "上游数据版本被确认包含错误编码。"
}
```

---

# 22. Figures API

## 22.1 创建 FigurePlan

```http id="yro86f"
POST /api/v1/projects/{project_id}/figure-plans
```

请求：

```json id="f8u1b4"
{
  "dataset_version_id": "uuid",
  "analysis_run_id": "uuid",
  "chart_type": "SCATTER",
  "x_column_id": "uuid",
  "y_column_id": "uuid",
  "group_column_id": null,
  "parameters": {
    "show_regression_line": true,
    "show_confidence_interval": true,
    "width_inches": 8,
    "height_inches": 6,
    "dpi": 300
  },
  "caption_draft": "生成式AI使用频率与学习投入的散点关系。"
}
```

---

## 22.2 AI 图表推荐

```http id="44yd4s"
POST /api/v1/projects/{project_id}/figure-recommendations
Idempotency-Key: <key>
```

---

## 22.3 渲染图表

```http id="hlta75"
POST /api/v1/figure-plans/{plan_id}/render
Idempotency-Key: <key>
```

返回 Job。

---

## 22.4 图表详情

```http id="ksaqi1"
GET /api/v1/figures/{figure_id}
```

---

## 22.5 图表规范问题

```http id="den2dp"
GET /api/v1/figures/{figure_id}/validation-issues
```

---

## 22.6 确认图表

```http id="3vc7uw"
POST /api/v1/figures/{figure_id}/approval-requests
```

确认通过 Approval API 完成。

---

## 22.7 下载图表

```http id="mtf5ds"
GET /api/v1/figures/{figure_id}/artifacts/{format}
```

`format`：

* `png`；
* `svg`；
* `pdf`；
* `code`。

---

## 22.8 引擎中立与运行元数据

本文件所有路径保持领域命名，不新增 Pandera、SciPy、statsmodels 或 Matplotlib
专属端点：

* 质量检查把 Pandera FailureCase 归一化为 DataQualityIssue；
* 分析执行把 SciPy/statsmodels 数值结果归一化为 AnalysisResult，不返回库对象或文本 Summary；
* 图表渲染把 Matplotlib 产物归一化为 Figure 与 Artifact；
* 实际引擎、版本、配置哈希、规则集版本、Python/依赖和字体信息记录在 AnalysisRun、ProcessingRun、CodeArtifact 或 Artifact metadata；
* 公共响应只返回 RECA 对象、运行状态和可公开复现摘要，不允许客户端选择任意 Python 引擎或代码。

第三方输出无法通过领域校验时使用 `EXTERNAL_OUTPUT_INVALID`；引擎不可用且无
可接受回退时使用 `EXTERNAL_CAPABILITY_UNAVAILABLE`。低风险质量扫描为
`AUTO_ALLOWED`，正式 AnalysisPlan 执行继续要求既有 `FORMAL_APPROVAL`。

---

# 兼容性路径索引：数据、分析与图表

以下字符串从原附录 A 原样迁入，仅保留旧 `{id}` 参数命名和总览兼容性。它们不是第二份完整端点定义；请求、响应、错误和前置条件以本文件对应资源章节为准。不得在本阶段擅自将 `{id}` 与更具体的参数名合并或重命名。

```text
POST   /api/v1/projects/{project_id}/datasets
GET    /api/v1/projects/{project_id}/datasets
GET    /api/v1/datasets/{id}
PATCH  /api/v1/datasets/{id}
GET    /api/v1/dataset-versions/{id}
GET    /api/v1/dataset-versions/{id}/preview
GET    /api/v1/dataset-versions/{id}/columns
PATCH  /api/v1/dataset-columns/{id}
GET    /api/v1/datasets/{id}/version-comparison
POST   /api/v1/dataset-versions/{id}/quality-runs
GET    /api/v1/data-quality-runs/{id}
GET    /api/v1/data-quality-runs/{id}/issues
POST   /api/v1/data-quality-issues/{id}/acknowledge
POST   /api/v1/data-quality-issues/{id}/ignore
POST   /api/v1/dataset-versions/{id}/cleaning-plans
POST   /api/v1/dataset-versions/{id}/cleaning-plan-suggestions
POST   /api/v1/cleaning-plans/{id}/preview
POST   /api/v1/cleaning-plans/{id}/approval-requests
POST   /api/v1/cleaning-plans/{id}/execute
POST   /api/v1/projects/{project_id}/analysis-plans
POST   /api/v1/projects/{project_id}/analysis-plan-suggestions
POST   /api/v1/analysis-plans/{id}/validate
PATCH  /api/v1/analysis-plans/{id}
POST   /api/v1/analysis-plans/{id}/approval-requests
POST   /api/v1/analysis-plans/{id}/runs
GET    /api/v1/analysis-runs/{id}
GET    /api/v1/analysis-runs/{id}/results
POST   /api/v1/analysis-runs/{id}/interpretations
POST   /api/v1/analysis-runs/{id}/invalidate
POST   /api/v1/projects/{project_id}/figure-plans
POST   /api/v1/projects/{project_id}/figure-recommendations
POST   /api/v1/figure-plans/{id}/render
GET    /api/v1/figures/{id}
GET    /api/v1/figures/{id}/validation-issues
POST   /api/v1/figures/{id}/approval-requests
GET    /api/v1/figures/{id}/artifacts/{format}
```
