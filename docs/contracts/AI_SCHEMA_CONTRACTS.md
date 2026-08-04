# AI_SCHEMA_CONTRACTS

- 所属入口文档：[API_AI_TOOL_CONTRACTS.md](../API_AI_TOOL_CONTRACTS.md)
- 文档状态：APPROVED FOR M1 DEVELOPMENT
- Migration status: COMPLETE
- M1 Contract Amendment status: APPROVED

## 权威范围

AI 公共 Envelope、校验流程、PromptContract manifest、ModelInvocation、Scoping、QueryPlan、文献抽取、证据总结、分析建议与解释、图表推荐、论文审核、AuditResult 和 Degradation Schema 的唯一完整定义。

## 不负责的内容

不定义业务资源 API 或 Agent Tool；AI 输出不能直接成为业务事实。

## 文档导航

- 返回 [API_AI_TOOL_CONTRACTS.md](../API_AI_TOOL_CONTRACTS.md)
- [COMMON_API_JOB_AND_SSE_CONTRACTS.md](COMMON_API_JOB_AND_SSE_CONTRACTS.md)
- [PROJECT_RESEARCH_AND_LITERATURE_API.md](PROJECT_RESEARCH_AND_LITERATURE_API.md)
- [DATA_ANALYSIS_AND_FIGURE_API.md](DATA_ANALYSIS_AND_FIGURE_API.md)
- [MANUSCRIPT_EVIDENCE_AND_EXPORT_API.md](MANUSCRIPT_EVIDENCE_AND_EXPORT_API.md)
- [AI_SCHEMA_CONTRACTS.md](AI_SCHEMA_CONTRACTS.md)
- [AGENT_TOOL_CONTRACTS.md](AGENT_TOOL_CONTRACTS.md)

以下正文由原入口文档对应章节机械迁入。路径、字段、错误码、Schema、Tool 名称和契约语义保持原样。


# 28. AI 输出公共 Envelope

所有重要 AI 输出统一采用：

```json id="3uc6tg"
{
  "schema_version": "1.0",
  "task_type": "RESEARCH_QUESTION_PARSE",
  "result": {},
  "source_ids": [],
  "confidence": 0.0,
  "confidence_label": "LOW",
  "limitations": [],
  "warnings": [],
  "requires_human_review": true,
  "review_reasons": [],
  "generated_at": "2026-07-29T08:30:00Z",
  "model_metadata": {
    "model_invocation_id": "uuid",
    "provider": "configured-provider",
    "model": "configured-model",
    "prompt_version": "rq-parse-1.0"
  }
}
```

## 28.1 必填字段

* `schema_version`；
* `task_type`；
* `result`；
* `source_ids`；
* `confidence`；
* `limitations`；
* `requires_human_review`；
* `generated_at`；
* `model_metadata.model_invocation_id`。

`model_metadata` 只提供本次调用的可追溯摘要。上游项目、Commit、Vendor 路径、
规则集与完整配置记录在 ModelInvocation、Prompt manifest、ProcessingRun 或
ReproPackage manifest，不得把第三方自由 JSON 塞入公共 Envelope。

## 28.2 confidence

范围：

```text id="o07vs5"
0.0 <= confidence <= 1.0
```

仅用于系统复核排序，不视为统计概率。

## 28.3 confidence_label

映射：

|        数值 | 标签     |
| --------: | ------ |
| 0.00—0.49 | LOW    |
| 0.50—0.79 | MEDIUM |
| 0.80—1.00 | HIGH   |

可根据测试调整，但必须统一。

## 28.4 source_ids

只能包含实际输入对象 ID，例如：

* ResearchQuestionVersion；
* LiteratureRecord；
* DocumentChunk；
* EvidenceSpan；
* DatasetVersion；
* AnalysisResult；
* Figure；
* ManuscriptVersion。

不得使用自然语言文献名称代替 ID。

## 28.5 requires_human_review

以下情况必须为 `true`：

* 研究问题正式确认；
* 文献字段低置信度；
* 文献纳入或排除建议；
* 当前证据不足判断；
* 选题采用；
* 数据处理建议；
* 统计方法选择；
* 因果表达修改；
* 高风险论文问题；
* Claim 正式确认。

---

# 29. AI 输出校验流程

```text id="pzhlp2"
模型原始输出
→ JSON解析
→ Schema校验
→ 枚举校验
→ 来源ID校验
→ 业务规则校验
→ 安全规则校验
→ 保存候选结果
→ 必要时人工复核
```

## 29.1 JSON 解析失败

允许一次结构化修复重试。

仍失败：

```text id="61lyki"
MODEL_OUTPUT_SCHEMA_INVALID
```

## 29.2 来源缺失

当任务要求来源但 `source_ids` 为空：

```text id="xetulx"
MODEL_OUTPUT_SOURCE_MISSING
```

不得将结果保存为正式结论。

## 29.3 数字检查

AI 输出中出现统计数字时：

* 必须与输入 AnalysisResult 完全匹配；
* 不得新增；
* 不得改变精度含义；
* 不得将 `p=0.051` 表述为显著。

## 29.4 文献检查

AI 不得输出输入文献集合之外的论文元数据。

## 29.5 Prompt 版本

每个任务必须固定 `prompt_version`。

Prompt 更新必须：

* 更新版本；
* 运行黄金测试；
* 记录变更；
* 不静默覆盖。

---

<a id="schema-research-question-spec"></a>

# 30. ResearchQuestionSpec

## 30.1 task_type

```text id="a4wmxd"
RESEARCH_QUESTION_PARSE
```

## 30.2 result Schema

```json id="k7q6dc"
{
  "normalized_question": "生成式AI使用频率与师范生学习投入之间是否存在关联？",
  "research_object": "师范生",
  "population": {
    "education_level": "本科",
    "major_scope": "师范类专业",
    "other_constraints": []
  },
  "context": "高校学习场景",
  "independent_variables": [
    {
      "name": "生成式AI使用频率",
      "definition": null,
      "measurement_hint": null
    }
  ],
  "dependent_variables": [
    {
      "name": "学习投入",
      "definition": null,
      "measurement_hint": null
    }
  ],
  "control_variables": [],
  "research_goal": "RELATE",
  "relationship_type": "ASSOCIATION",
  "method_preference": [],
  "time_scope": null,
  "region_scope": null,
  "language_scope": ["zh", "en"],
  "resource_constraints": [],
  "ethical_constraints": [],
  "uncertainties": [
    {
      "field": "population.education_level",
      "reason": "用户未明确本科或研究生。"
    }
  ],
  "follow_up_questions": [
    "研究对象限定本科师范生吗？"
  ]
}
```

## 30.3 规则

* 不生成文献；
* 不自动声称因果；
* 用户使用“影响”时应判断是否需要改为相关、比较或预测；
* 最多输出 3 个高价值追问；
* 不填充用户未提供且无法推断的事实。

<a id="schema-research-question-scoping-input"></a>
<a id="schema-research-question-scoping-output"></a>

## 30.4 ResearchQuestionScopingOutput

当用户只有宽泛主题或关键前提不足时，路由器必须返回收敛结果，不能直接生成大纲、完整论文或启动全流程。该任务的 `task_type` 为 `RESEARCH_QUESTION_SCOPING`，输入 `ResearchQuestionScopingInput` 包含当前主题、已保存的 `ScopingAnswer`、项目上下文快照和允许使用的证据 ID。

```json
{
  "status": "NEEDS_USER_INPUT",
  "socratic_questions": [
    {
      "question_id": "population",
      "question": "你希望研究哪一类大学生？",
      "reason": "研究对象会影响文献范围、可得数据和结论边界。",
      "required": true
    }
  ],
  "candidates": [],
  "evidence_gaps": ["尚未确认可用数据或测量方式。"],
  "source_ids": []
}
```

`SocraticQuestion`、`ScopingAnswer` 和 `ResearchQuestionCandidate` 都必须是结构化对象并可持久化；每轮最多 3 个高价值问题，最多 2 轮。输出状态仅可为：

```text
NEEDS_USER_INPUT
CANDIDATES_READY
INSUFFICIENT_EVIDENCE
OUT_OF_SCOPE
```

当状态为 `CANDIDATES_READY` 时，最多返回 3 个候选问题；每个候选问题必须分别列出当前项目的支持证据、可得数据、证据缺口和可行性风险。它只能陈述“当前项目集合中的证据空白”，不得断言学术界不存在研究。

ARS Scoping 资产可以实现该既有 Schema，但不得增加未登记字段。ARS
Checkpoint 不建立新 AI Schema：它映射到 ProjectContextSnapshot 的当前阶段、
`pending_approval_ids`、`blocking_issue_ids`、`allowed_next_actions` 以及 Envelope
的 `requires_human_review`。Workflow mode 由现有项目阶段、`task_type` 和
PromptContract 决定，不允许第三方 Router 自由创建状态或枚举。

---

<a id="schema-query-plan"></a>

# 31. QueryPlan AI Schema

## 31.1 task_type

```text id="abnjss"
QUERY_PLAN_GENERATION
```

## 31.2 result Schema

```json id="enbkfn"
{
  "chinese_terms": {
    "core": ["生成式人工智能", "学习投入", "师范生"],
    "synonyms": [],
    "object_terms": ["师范生", "教师教育学生"],
    "method_terms": ["问卷", "相关研究"]
  },
  "english_terms": {
    "core": [
      "generative artificial intelligence",
      "learning engagement",
      "pre-service teachers"
    ],
    "synonyms": [
      "student engagement",
      "teacher education students"
    ],
    "method_terms": [
      "survey",
      "correlational study"
    ]
  },
  "boolean_query": "(\"generative artificial intelligence\" OR \"generative AI\") AND (\"learning engagement\" OR \"student engagement\") AND (\"pre-service teacher*\" OR \"teacher education student*\")",
  "filters": {
    "from_year": 2020,
    "to_year": 2026,
    "languages": ["zh", "en"],
    "work_types": ["article"]
  },
  "expansion_options": [],
  "narrowing_options": [],
  "limitations": [
    "检索词用于查询规划，不代表已检索到真实文献。"
  ]
}
```

## 31.3 规则

* 查询词和真实检索结果必须区分；
* 不输出论文题目；
* 不伪造数据库特定语法能力；
* Provider Adapter 负责最终查询转换。

---

<a id="schema-literature-extraction"></a>

# 32. LiteratureExtraction AI Schema

## 32.1 task_type

```text id="0z7wuu"
LITERATURE_FIELD_EXTRACTION
```

## 32.2 result Schema

模型 Provider 的原始结果使用内部 `LiteratureExtractionCandidateOutput@1.0`。其中
`evidence_candidates` 只是待验证的原文候选，禁止包含或接受 `evidence_span_id`。RECA
必须逐项完成 project、document、page、chunk、source_text、hash、offset 和坐标定位后，
才能形成下面的 `LiteratureExtractionOutput@1.0`。该正式结果中的 `evidence_span_ids` 只能
引用服务端已经持久化的 EvidenceSpan。

```json id="q1meva"
{
  "literature_record_id": "uuid",
  "document_id": "uuid",
  "fields": [
    {
      "field_code": "RESEARCH_OBJECT",
      "value": {
        "text": "本科师范生",
        "structured": {
          "education_level": "本科",
          "population_type": "师范生"
        }
      },
      "evidence_span_ids": ["uuid"],
      "confidence": 0.91,
      "requires_human_review": false,
      "notes": []
    },
    {
      "field_code": "SAMPLE_SIZE",
      "value": {
        "text": "312",
        "structured": {
          "n": 312
        }
      },
      "evidence_span_ids": ["uuid"],
      "confidence": 0.87,
      "requires_human_review": false,
      "notes": []
    }
  ],
  "document_level_limitations": []
}
```

## 32.3 规则

* 每个语义字段尽可能绑定 EvidenceSpan；
* 无证据时字段应为 `null` 或低置信度；
* 不从摘要之外推完整方法；
* 不把研究假设当结论；
* 样本量必须来自原文；
* 主要结论必须保留限定条件。

---

<a id="schema-evidence-set-summary"></a>

# 33. EvidenceSetSummary AI Schema

## 33.1 task_type

```text id="py0gfn"
EVIDENCE_SET_SUMMARY
```

## 33.2 result Schema

```json id="mfc1tk"
{
  "included_literature_ids": ["uuid"],
  "scope_statement": "基于当前纳入的8篇文献。",
  "consensus_items": [
    {
      "claim_text": "多数纳入研究报告生成式AI使用与学习相关结果之间存在正向关联。",
      "supporting_literature_ids": ["uuid"],
      "contradicting_literature_ids": [],
      "evidence_span_ids": ["uuid"],
      "strength": "MODERATE",
      "limitations": [
        "多数研究采用横断面设计。"
      ]
    }
  ],
  "controversy_items": [],
  "evidence_gap_items": [
    {
      "claim_text": "在当前文献集合中，纵向研究证据较少。",
      "basis": {
        "included_count": 8,
        "longitudinal_count": 1
      },
      "evidence_span_ids": ["uuid"],
      "limitations": [
        "该判断仅适用于当前纳入文献。"
      ]
    }
  ],
  "counterexamples": [],
  "missing_information": []
}
```

## 33.3 规则

禁止：

* “学术界从未研究”；
* “已经证明不存在研究”；
* 隐藏反例；
* 将单篇文献作为共识；
* 引用未纳入文献。

## 33.4 候选、证据不足与冲突语义

PaperQA 或其他检索/packing 实现只能向既有严格输出提供候选项。候选项必须
包含 RECA 文档或 Chunk ID、原文片段、哈希、页码（若可用）、检索运行 ID、
分数和限制；未通过原文定位校验时不得产生 `evidence_span_ids`。

* evidence candidate 通过 `retrieve_evidence` Tool 的既有 EvidenceCandidate 输出表达；
* evidence insufficiency 通过空候选、`evidence_gap_items`、`missing_information`、`limitations` 和 `requires_human_review=true` 表达；
* conflicting evidence 通过 `controversy_items`、`contradicting_literature_ids` 和 counterexamples 表达；
* 当前集合无证据不是错误，也不得改写为“学术界不存在证据”。

第三方输出必须先通过注册的 output Schema；即使上游返回更多字段，也不得以
自由 JSON 绕过枚举、来源 ID、项目隔离和 EvidenceSpan 校验。

---

<a id="schema-topic-candidate"></a>

# 34. TopicCandidate AI Schema

## 34.1 task_type

```text id="a54p7n"
TOPIC_CANDIDATE_GENERATION
```

## 34.2 result Schema

```json id="wab71p"
{
  "candidates": [
    {
      "candidate_order": 1,
      "question_text": "生成式AI使用频率与本科师范生学习投入之间的关系：AI素养的调节作用",
      "research_object": "本科师范生",
      "variables": {
        "independent": ["生成式AI使用频率"],
        "dependent": ["学习投入"],
        "moderator": ["AI素养"]
      },
      "literature_basis": "基于当前纳入文献中的相关研究与测量建议。",
      "literature_record_ids": ["uuid"],
      "evidence_span_ids": ["uuid"],
      "possible_innovation": "在当前文献集合中，AI素养作为调节变量的研究较少。",
      "data_requirements": {
        "minimum_fields": [
          "生成式AI使用频率",
          "学习投入",
          "AI素养"
        ],
        "sample_notes": "需具备足够样本进行基础回归分析。"
      },
      "recommended_method": "相关分析；调节分析不进入P0自动执行范围。",
      "literature_basis_level": "MEDIUM",
      "data_availability": "MEDIUM",
      "method_difficulty": "MEDIUM",
      "time_feasibility": "HIGH",
      "ethical_risk": "LOW",
      "major_risks": [],
      "supervisor_confirmation_items": [
        "确认AI素养的理论角色。"
      ]
    }
  ]
}
```

## 34.3 规则

* 固定返回 3 个候选项；
* 不使用 93 分等伪精确分数；
* 超出 P0 方法时必须明确；
* 每项必须有文献依据和数据要求；
* 最终采用需用户和导师确认。

---

<a id="schema-cleaning-plan-suggestion"></a>

# 35. CleaningPlanSuggestion AI Schema

## 35.1 task_type

```text id="ut7n9w"
CLEANING_PLAN_SUGGESTION
```

## 35.2 result Schema

```json id="xqoa0d"
{
  "dataset_version_id": "uuid",
  "suggested_actions": [
    {
      "source_issue_ids": ["uuid"],
      "action_type": "MARK_MISSING",
      "target_column_ids": ["uuid"],
      "row_selector": {
        "operator": "VALUE_EQUALS",
        "value": 999
      },
      "parameters": {
        "replacement": null
      },
      "reason": "数据说明中将999定义为缺失编码。",
      "risk_level": "MEDIUM",
      "expected_effect": {
        "affected_rows": 18,
        "row_count_change": 0
      },
      "alternatives": [
        "保留原值并在分析时排除。"
      ],
      "requires_approval": true
    }
  ],
  "warnings": [],
  "limitations": []
}
```

## 35.3 规则

* 只能引用已检测问题；
* 不自动执行；
* 不输出任意代码；
* 异常值不能默认删除；
* 处理影响必须可预览。

---

<a id="schema-analysis-plan-suggestion"></a>

# 36. AnalysisPlanSuggestion AI Schema

## 36.1 task_type

```text id="2f00si"
ANALYSIS_PLAN_SUGGESTION
```

## 36.2 result Schema

```json id="wzsbdm"
{
  "research_question_version_id": "uuid",
  "dataset_version_id": "uuid",
  "analysis_goal": "CORRELATION",
  "recommended_method": "PEARSON_CORRELATION",
  "variable_mapping": {
    "independent_variable_ids": ["uuid"],
    "dependent_variable_ids": ["uuid"],
    "control_variable_ids": [],
    "group_variable_id": null
  },
  "missing_data_policy": {
    "mode": "PAIRWISE_COMPLETE"
  },
  "required_assumption_checks": [
    "DATA_TYPE",
    "SAMPLE_SIZE",
    "LINEARITY",
    "OUTLIER_INFLUENCE"
  ],
  "recommendation_reason": "研究目标为两个连续变量之间的相关关系。",
  "alternative_methods": [
    {
      "method": "SPEARMAN_CORRELATION",
      "condition": "线性或分布前提不足时。"
    }
  ],
  "limitations": [
    "相关分析不能支持因果推断。"
  ],
  "requires_human_review": true
}
```

## 36.3 规则

* 只能推荐 P0 方法；
* 变量角色必须由用户确认；
* 不直接执行；
* 不生成统计数字；
* 前提不明确时必须说明。

---

<a id="schema-analysis-interpretation"></a>

# 37. AnalysisInterpretation AI Schema

## 37.1 task_type

```text id="dfx7z0"
ANALYSIS_RESULT_INTERPRETATION
```

## 37.2 result Schema

```json id="vqbypm"
{
  "analysis_run_id": "uuid",
  "result_summary": "在当前样本中，生成式AI使用频率与学习投入呈正相关。",
  "numeric_statements": [
    {
      "text": "相关系数为0.31。",
      "analysis_result_path": "statistics.coefficient",
      "value": 0.31
    }
  ],
  "statistical_significance_statement": "该相关在当前分析中达到统计显著。",
  "practical_interpretation": "关联强度较弱至中等，仍需结合研究背景解释。",
  "causal_boundary": "该分析不能说明生成式AI使用导致学习投入变化。",
  "sample_scope": "结论仅适用于当前数据版本中的有效样本。",
  "limitations": [],
  "recommended_follow_up": []
}
```

## 37.3 规则

* 所有数字必须绑定 `analysis_result_path`；
* 值必须与 AnalysisResult 完全一致；
* 不把不显著写成显著；
* 不把相关写成因果；
* 不扩大样本范围。

---

<a id="schema-figure-recommendation"></a>

# 38. FigureRecommendation AI Schema

## 38.1 task_type

```text id="u2zsl4"
FIGURE_RECOMMENDATION
```

## 38.2 result Schema

```json id="fgzxu8"
{
  "recommendations": [
    {
      "chart_type": "SCATTER",
      "x_column_id": "uuid",
      "y_column_id": "uuid",
      "group_column_id": null,
      "reason": "用于展示两个连续变量之间的关系。",
      "required_parameters": {
        "show_regression_line": true,
        "show_confidence_interval": true
      },
      "caption_elements": [
        "变量名称",
        "样本量",
        "数据版本",
        "相关不等于因果"
      ],
      "risks": [
        "大量重叠点可能影响可读性。"
      ]
    }
  ],
  "not_recommended": [
    {
      "chart_type": "BAR",
      "reason": "柱状图不适合展示两个连续变量之间的关系。"
    }
  ]
}
```

---

<a id="schema-manuscript-issue-suggestion"></a>

# 39. ManuscriptIssueSuggestion AI Schema

## 39.1 task_type

```text id="pmf8sd"
MANUSCRIPT_ISSUE_SUGGESTION
```

## 39.2 result Schema

```json id="focjtw"
{
  "manuscript_version_id": "uuid",
  "issues": [
    {
      "issue_type": "CAUSAL_OVERCLAIM",
      "severity": "HIGH",
      "section_name": "讨论",
      "paragraph_index": 42,
      "original_text": "生成式AI使用提高了师范生学习投入。",
      "reason": "项目中仅执行了相关分析，不能支持因果表述。",
      "evidence": [
        {
          "object_type": "ANALYSIS_RESULT",
          "object_id": "uuid"
        }
      ],
      "suggestion": "可改为“生成式AI使用频率与学习投入呈正相关”。",
      "auto_fixable": false,
      "requires_human_review": true
    }
  ]
}
```

## 39.3 规则

* 高风险问题不自动修复；
* 建议不得新增不存在的引用或数字；
* 问题必须有位置；
* 数字问题必须关联 AnalysisResult；
* 文献问题必须关联 LiteratureRecord 或 EvidenceSpan。

---

<a id="schema-audit-result"></a>

# 40. AuditResult AI Schema

## 40.1 task_type

```text id="jjoz37"
TRUST_AUDIT
```

## 40.2 result Schema

```json id="7q5crn"
{
  "audit_type": "CLAIM_COMPLETENESS_AUDIT",
  "target_object_type": "CLAIM",
  "target_object_id": "uuid",
  "status": "NEEDS_REVIEW",
  "findings": [
    {
      "finding_code": "MISSING_QUALIFYING_EVIDENCE",
      "severity": "MEDIUM",
      "message": "当前Claim缺少横断面设计限制说明。",
      "evidence_object_ids": ["uuid"],
      "recommended_action": "补充限定性证据或修改Claim表述。"
    }
  ],
  "evidence_coverage": {
    "has_source": true,
    "has_page_location": true,
    "has_dataset_version": true,
    "has_analysis_result": true,
    "has_user_confirmation": false
  },
  "limitations": []
}
```

## 40.3 规则

* Audit 不直接修改目标对象；
* 审核结果必须关联证据；
* 无法验证时应返回 `INSUFFICIENT_EVIDENCE`；
* 不得使用“已验证”掩盖来源缺失。

ARS Claim Verification 可以提供 Prompt、检查顺序和测试资产，但结果仍使用
既有 `AuditResult` Schema。它不能直接更新 Claim、ClaimEvidenceLink、
ManuscriptVersion 或 ApprovalRecord。

---

<a id="contract-prompt-manifest"></a>
<a id="contract-model-invocation"></a>

# 72. 模型调用契约

## 72.0 M1 持久化与运行边界

M1 必须交付 `ModelInvocation` 持久化 Schema、内部 Service DTO、Prompt manifest 校验和
Mock/Recorded 契约测试模式。M1 不调用模型 Provider，不接入 Agents SDK、Agent runtime、
ResearchOrchestrator 或 Tool Registry runtime。

PromptContract 的权威是 Git 管理的
`backend/app/agents/prompts/prompt-manifest.yaml`；ModelInvocation 是每次已计划或实际模型
调用的不可变审计事实。二者不能互相替代，数据库不得提供用户可编辑 Prompt。

ModelInvocation 由内部 model-invocation Service 在执行边界前创建；同一 Service 校验
project/source/access policy，并通过受控方法推进 RUNNING/terminal 状态。Provider adapter、
Agents SDK、Worker 或客户端都不能绕过 Service 直接写记录。M1 不提供 ModelInvocation
public create/update/delete API；授权审计读取由后续真实 consumer 的资源 projection 决定。

## 72.1 模型调用输入

必须包含：

* task_type；
* prompt_id；
* prompt_version；
* schema_name；
* schema_version；
* source_ids；
* sanitized_input；
* output_requirements；
* prohibited_behaviors。
* requested_data_access_level；
* max_allowed_data_access_level；
* effective_data_access_level；

使用第三方 Prompt/Workflow 资产时，还必须由 Prompt manifest 固定来源记录、
内容哈希和适用 Schema；这些治理元数据不进入模型可修改输入。Agents SDK
structured output 只负责执行校验，不能放宽 RECA Schema 或把 SDK Session
内容当作项目状态。

P0 的 PromptContract 是 `backend/app/agents/prompts/prompt-manifest.yaml` 中受 Git 管理的代码注册表，不是数据库可编辑内容。`prompt_id + prompt_version + prompt_content_hash` 必须能定位已登记合同；其声明 input/output Schema、允许工具、允许来源类型、最大工具调用数、失败行为和 `requested_data_access_level`。Prompt 文本的内容哈希先把 `CRLF` 和单独 `CR` 规范化为 `LF`，再对 UTF-8 字节计算 SHA-256；Git checkout 的平台行尾不得改变 Prompt identity。Tool/Policy 另声明 `max_allowed_data_access_level`；调用审计记录实际 `effective_data_access_level`，且必须不高于上限并符合最小化原则。未登记、Schema 不匹配或试图扩大工具/数据权限的调用必须在 Service 层拒绝。

## 72.1.1 ModelInvocation 最小持久化合同

| Concern | M1 required fields / rule |
| --- | --- |
| identity | `id`, `project_id`, `request_id`, `actor_type`, `actor_id`, `task_type` |
| Prompt identity | `prompt_id`, `prompt_version`, `prompt_content_hash`，必须匹配 manifest |
| Schema identity | `input_schema_name`, `input_schema_version`, `output_schema_name`, `output_schema_version` |
| runtime identity | `provider`, `model`；M1 未实际调用时可为 `null`，Mock/Recorded 必须显式标识模式 |
| access policy | `requested_data_access_level`, `max_allowed_data_access_level`, `effective_data_access_level` |
| provenance | project-scoped `source_ids`, `input_hash`, nullable `output_hash` |
| outcome | `status`, nullable `error_code`, nullable `degradation` |
| implementation | nullable `implementation_metadata`，可记录 mode、adapter/version、fixture/recording identity |
| time | `started_at`, nullable `completed_at`, `created_at` |

状态仅为：

```text
PENDING
RUNNING
SUCCEEDED
FAILED
```

数据访问等级从低到高仅为：

```text
METADATA_ONLY
REDACTED_CONTENT
VERIFIED_EVIDENCE_ONLY
APPROVED_FULL_CONTENT
```

`effective_data_access_level` 必须不高于 requested 与 policy max 中更严格的边界。
`source_ids` 必须全部属于同一 `project_id` 且符合 PromptContract 的来源白名单。默认只保存
规范化 input/output hash 和必要审计摘要，不保存完整敏感正文。terminal record 不得普通
更新；一次 retry 创建新的 ModelInvocation 并通过 implementation metadata 或上层
ProcessingRun 建立关联。

## 72.1.2 Mock / Recorded 模式

* `MOCK` 只验证 manifest、Schema、权限、哈希和持久化边界；输出必须来自明确标记的确定性
  fixture，不得声称来自真实模型；
* `RECORDED` 使用已审查、固定 hash/version 的录制响应，禁止联网，必须记录 recording
  identity 与来源许可/脱敏状态；
* 两种模式都创建 ModelInvocation，记录实际 mode，并执行与未来 live mode 相同的
  project isolation、data access、Schema 和审计校验；
* M1 不定义 `LIVE` Provider 执行实现。后续里程碑接入时仍必须使用本合同，不得把 SDK
  trace 或 session 当作 ModelInvocation、ResearchProject 或 AuditLog。

## 72.2 敏感数据

默认不向模型发送：

* 完整数据表；
* 身份证号；
* 手机号；
* 姓名列表；
* 未脱敏论文附件；
* 系统密钥；
* 对象存储凭据。

## 72.3 模型重试

可重试：

* 临时网络错误；
* 模型超时；
* JSON 解析失败；
* Schema 轻微失败。

不可自动重试：

* 内容安全拒绝；
* 来源缺失；
* 输入权限错误；
* 数据敏感规则阻止；
* 任务超出产品范围。

## 72.4 最大重试

建议：

```text id="m766p0"
2
```

超过后进入人工处理。

## 72.5 模型回退

允许配置备用模型，但必须记录实际模型。

不得将备用模型结果伪装成主模型结果。

---

# 79. AI 与外部能力降级契约

<a id="schema-degradation-record"></a>

## 79.5 统一降级响应

所有外部 Adapter、模型与事件通道在发生降级时，除原有 `warnings` 和 `limitations` 外必须返回下列对象；无降级时为 `null`：

```json
{
  "requested_capability": "PDF_PAGE_LOCATION",
  "primary_provider": "grobid",
  "fallback_provider": "pypdf",
  "reason_code": "GROBID_UNAVAILABLE",
  "impact": "页码定位无法验证；保留页文本，EvidenceSpan 标记为 LOCATION_UNCERTAIN。",
  "result_status": "DEGRADED",
  "user_visible_message": "原文页码定位服务暂不可用，当前定位尚未验证。"
}
```

`result_status` 只能为 `DEGRADED`、`UNAVAILABLE` 或 `FALLBACK_COMPLETED`。返回该对象时必须创建对应审计记录；回退不得改变授权、扩大模型输入或把不确定定位升级为已验证。

筛选、引用渲染、Vendor 资产或许可证限制导致能力不可用时也使用同一结构。
许可证相关 `reason_code` 只表达“能力不可用/需要治理复核”，不得给出未经核验
的法律结论；若第三方输出无法转换为严格 Schema，使用
`EXTERNAL_OUTPUT_INVALID` 并禁止部分写入。

---
