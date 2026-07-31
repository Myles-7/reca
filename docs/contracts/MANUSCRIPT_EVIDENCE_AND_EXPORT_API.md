# MANUSCRIPT_EVIDENCE_AND_EXPORT_API

- 所属入口文档：[API_AI_TOOL_CONTRACTS.md](../API_AI_TOOL_CONTRACTS.md)
- 文档状态：Conditional Approval
- Migration status: COMPLETE

## 权威范围

Manuscript、Manuscript Check、MANU-P0-018、Claim、Evidence Graph、Audit、Export 和 ReproPackage API 的唯一完整定义。

## 不负责的内容

不定义通用 AI 输出 Schema、Agent Tool 或数据分析 API。

## 文档导航

- 返回 [API_AI_TOOL_CONTRACTS.md](../API_AI_TOOL_CONTRACTS.md)
- [COMMON_API_JOB_AND_SSE_CONTRACTS.md](COMMON_API_JOB_AND_SSE_CONTRACTS.md)
- [PROJECT_RESEARCH_AND_LITERATURE_API.md](PROJECT_RESEARCH_AND_LITERATURE_API.md)
- [DATA_ANALYSIS_AND_FIGURE_API.md](DATA_ANALYSIS_AND_FIGURE_API.md)
- [MANUSCRIPT_EVIDENCE_AND_EXPORT_API.md](MANUSCRIPT_EVIDENCE_AND_EXPORT_API.md)
- [AI_SCHEMA_CONTRACTS.md](AI_SCHEMA_CONTRACTS.md)
- [AGENT_TOOL_CONTRACTS.md](AGENT_TOOL_CONTRACTS.md)

以下正文由原入口文档对应章节机械迁入。路径、字段、错误码、Schema、Tool 名称和契约语义保持原样。


# 23. Manuscripts API

## 23.1 上传 DOCX

```http id="639mso"
POST /api/v1/projects/{project_id}/manuscripts
Content-Type: multipart/form-data
```

字段：

```text id="u3pzsc"
file
title
```

响应创建 Manuscript 和 ManuscriptVersion。

---

## 23.2 论文详情

```http id="ijpl44"
GET /api/v1/manuscripts/{manuscript_id}
```

---

## 23.3 论文版本

```http id="s4akv0"
GET /api/v1/manuscript-versions/{version_id}
```

---

## 23.4 启动检查

```http id="7ln2d5"
POST /api/v1/manuscript-versions/{version_id}/check-runs
Idempotency-Key: <key>
```

请求：

```json id="wq7fs6"
{
  "checks": [
    "CITATION",
    "NUMERIC_CONSISTENCY",
    "CAUSALITY",
    "TERMINOLOGY",
    "BASIC_FORMAT"
  ],
  "use_project_literature": true,
  "use_project_analysis_results": true,
  "use_project_figures": true
}
```

返回 Job。

---

## 23.5 获取检查结果

```http id="0v6ygq"
GET /api/v1/manuscript-check-runs/{run_id}
```

## 23.6 获取问题列表

```http id="7g6o7y"
GET /api/v1/manuscript-check-runs/{run_id}/issues
```

过滤：

* `severity`；
* `issue_type`；
* `status`；
* `auto_fixable`。

---

## 23.7 问题详情

```http id="3xkt99"
GET /api/v1/manuscript-issues/{issue_id}
```

---

## 23.8 接受建议

```http id="4fgo4z"
POST /api/v1/manuscript-issues/{issue_id}/accept
```

高风险问题仅表示用户接受建议，不自动修改。

---

## 23.9 驳回建议

```http id="r0rnqh"
POST /api/v1/manuscript-issues/{issue_id}/reject
```

请求需要原因。

---

## 23.10 创建低风险修复计划

```http id="c7depl"
POST /api/v1/manuscript-versions/{version_id}/fix-plans
```

只允许自动修复项。

---

## 23.11 执行批准修复

```http id="5ecjly"
POST /api/v1/manuscript-fix-plans/{plan_id}/execute
Idempotency-Key: <key>
```

输出新 ManuscriptVersion。

---

## 23.12 MANU-P0-018：创建修订漂移审核

```http
POST /api/v1/projects/{project_id}/manuscript-revision-audits
```

请求必须引用两个已持久化版本，且只创建审核结果，不会修改论文：

```json
{
  "baseline_manuscript_version_id": "uuid",
  "candidate_manuscript_version_id": "uuid"
}
```

响应为 `202 Accepted` 的 `Job`（`job_type = MANUSCRIPT_REVISION_AUDIT`）；完成后产生 `AuditResult.audit_type = REVISION_DRIFT_AUDIT`。Competition Core 的确定性 finding 包括 `CLAIM_NUMERIC_MISMATCH`、`CLAIM_CAUSAL_OVERSTATEMENT`、`CLAIM_STALE_AFTER_REVISION`、`CLAIM_FIGURE_VERSION_MISMATCH`；P0-Full 才可加入模型辅助的限定词与范围语义漂移。该端点不得自动接受修订或补写证据关系。

---

# 24. Claims 与 Evidence API

## 24.1 创建 Claim

```http id="l2bcb1"
POST /api/v1/projects/{project_id}/claims
```

请求：

```json id="9fr7ch"
{
  "claim_type": "MANUSCRIPT_STATEMENT",
  "source_object_type": "manuscript_version",
  "source_object_id": "uuid",
  "source_location": {
    "paragraph_index": 42
  },
  "claim_text": "生成式AI使用频率与师范生学习投入呈正相关。",
  "scope_statement": "基于当前公开数据集和相关分析。"
}
```

---

## 24.2 Claim 详情

```http id="w32063"
GET /api/v1/claims/{claim_id}
```

---

## 24.3 创建证据关系

```http id="si6m14"
POST /api/v1/claims/{claim_id}/evidence-links
```

请求：

```json id="35fgzq"
{
  "evidence_object_type": "ANALYSIS_RESULT",
  "evidence_object_id": "uuid",
  "relation_type": "SUPPORTED_BY",
  "strength": "STRONG",
  "explanation": "相关分析结果支持该表述。"
}
```

服务端校验同项目。

---

## 24.4 Claim 审核

```http id="e2fpvo"
POST /api/v1/claims/{claim_id}/audits
Idempotency-Key: <key>
```

返回 Job 或同步 AuditResult。

---

## 24.5 证据图

```http id="mjmwc0"
GET /api/v1/projects/{project_id}/evidence-graph
```

参数：

```text id="qyuukj"
root_claim_id
depth
node_types
risk_only
include_invalidated
```

响应：

```json id="axsywd"
{
  "data": {
    "nodes": [
      {
        "id": "claim:uuid",
        "node_type": "CLAIM",
        "object_id": "uuid",
        "label": "生成式AI使用频率与学习投入呈正相关",
        "status": "SUPPORTED",
        "risk_level": "LOW",
        "detail_url": "/api/v1/claims/uuid"
      }
    ],
    "edges": [
      {
        "id": "uuid",
        "source": "claim:uuid",
        "target": "analysis_result:uuid",
        "relation_type": "SUPPORTED_BY",
        "status": "ACTIVE"
      }
    ],
    "scope": {
      "literature_count": 8,
      "dataset_version_id": "uuid",
      "analysis_run_ids": ["uuid"],
      "generated_at": "2026-07-29T10:00:00Z"
    }
  }
}
```

---

## 24.6 Claim 确认

通过 Approval API，不允许直接设置 `CONFIRMED`。

## 24.7 引用渲染边界

当前不新增 citation processor 专属公共路径或 Agent Tool。论文检查、引用导出
或复现包流程需要格式化时，由领域 Service 调用隔离 Citation Engine 或简单
确定性格式器，并把结果保存为绑定 ProcessingRun/Artifact 的严格
`CitationRenderResult` 载荷。

渲染结果只证明“按给定元数据和样式生成了文本”，不证明 DOI、作者、来源、
引用适切性或 EvidenceSpan 有效。引擎不可用时使用
`EXTERNAL_CAPABILITY_UNAVAILABLE` 和显式降级，不得把未渲染内容标为成功。

---

# 26. Exports API

## 26.1 创建复现包

```http id="7rczfr"
POST /api/v1/projects/{project_id}/exports/repro-package
Idempotency-Key: <key>
```

请求：

```json id="duun5u"
{
  "include_original_literature_files": true,
  "include_dataset_versions": true,
  "include_sensitive_data": false,
  "include_agent_logs": true,
  "include_model_output_artifacts": false,
  "acknowledge_license_warnings": false
}
```

系统先执行导出就绪审核。

生成的 ReproPackage Manifest 必须记录实际 runtime dependency 版本、service
image digest、upstream 项目、Vendor Commit、Prompt/规则集/统计引擎版本、
citation style 标识与哈希、配置哈希和来源对象版本。研究过但未实际采用的项目
不得进入 runtime 或 vendored asset 清单。

可能返回：

* `202 Accepted`；
* 或 `409`，要求用户处理许可证或敏感信息问题。

---

## 26.2 导出就绪检查

```http id="i7iluh"
POST /api/v1/projects/{project_id}/exports/readiness-check
```

响应：

```json id="bf35wf"
{
  "data": {
    "ready": false,
    "blocking_issues": [
      {
        "code": "DATASET_LICENSE_UNKNOWN",
        "object_id": "uuid",
        "message": "数据集许可证未知。"
      }
    ],
    "warnings": [],
    "requires_confirmation": true
  }
}
```

---

## 26.3 导出详情

```http id="o4krbs"
GET /api/v1/exports/{export_id}
```

## 26.4 下载导出包

```http id="7scudj"
GET /api/v1/repro-packages/{package_id}/download
```

---

# 兼容性路径索引：论文、证据与导出

以下字符串从原附录 A 原样迁入，仅保留旧 `{id}` 参数命名和总览兼容性。它们不是第二份完整端点定义；请求、响应、错误和前置条件以本文件对应资源章节为准。不得在本阶段擅自将 `{id}` 与更具体的参数名合并或重命名。

```text
POST   /api/v1/projects/{project_id}/manuscripts
GET    /api/v1/manuscripts/{id}
GET    /api/v1/manuscript-versions/{id}
POST   /api/v1/manuscript-versions/{id}/check-runs
GET    /api/v1/manuscript-check-runs/{id}
GET    /api/v1/manuscript-check-runs/{id}/issues
GET    /api/v1/manuscript-issues/{id}
POST   /api/v1/manuscript-issues/{id}/accept
POST   /api/v1/manuscript-issues/{id}/reject
POST   /api/v1/manuscript-versions/{id}/fix-plans
POST   /api/v1/manuscript-fix-plans/{id}/execute
POST   /api/v1/projects/{project_id}/claims
GET    /api/v1/claims/{id}
POST   /api/v1/claims/{id}/evidence-links
POST   /api/v1/claims/{id}/audits
GET    /api/v1/projects/{project_id}/evidence-graph
POST   /api/v1/projects/{project_id}/exports/readiness-check
POST   /api/v1/projects/{project_id}/exports/repro-package
GET    /api/v1/exports/{id}
GET    /api/v1/repro-packages/{id}/download
```
