# M8_AGENT

- 所属入口文档：[IMPLEMENTATION_ROADMAP.md](../../IMPLEMENTATION_ROADMAP.md)
- 文档状态：Conditional Approval
- Migration status: COMPLETE
- Milestone ID: M8

## 权威范围

本文件是 M8 目标、依赖、范围、交付、测试、安全、门禁、阻塞和降级要求的详细路线图。产品范围、字段、API 契约和测试指标仍由对应权威文档定义。

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
| 目标 | 16.1 |
| 前置依赖 | 16.2 |
| Competition Core | 16.3 中属于 P0-Must / Competition Core 的条目；不得重新分类 |
| P0-Full | 16.3 中明确标为 P0-Full 的条目；未标记者以 PRD 为准 |
| 明确不做 | 16.4 |
| 数据模型 | 16.6 / 16.8 |
| API | 16.9 |
| 前端 | 16.7 |
| 测试 | 16.11 |
| 安全 | 16.12 |
| Prompt / AI | 16.5 / 16.10；无模型任务时不得擅自新增 |
| Codex 推荐任务顺序 | 16.17 |
| 可并行任务 | 16.15 |
| Entry Gate | 16.2 + 公共 Entry Gate |
| Exit Gate | 16.14 + 公共 Exit Gate |
| 阻塞问题 | 16.16 |
| 风险与降级 | 本里程碑原章节 + [RISK_SCOPE_AND_RELEASE.md](../RISK_SCOPE_AND_RELEASE.md) |

M0 Regression Baseline 适用于本里程碑，任何交付不得使 M0 已验收能力退化。以下正文由原路线图对应章节机械迁入，原顺序、依赖和语义不变。

<a id="milestone-m8"></a>

# 16. M8：科研总控 Agent 接入

M8 只实现 StageResolver、Tool Registry、Agent route decision、受控工具编排与 Agent 面板。Prompt 版本、ModelInvocation 和模型数据访问治理必须已在 M1 建立；不引入自由多 Agent。

## 16.1 目标

在不改变领域规则和审批边界的前提下，让科研总控 Agent 识别项目状态、推荐下一步并调用白名单工具。

## 16.2 前置依赖

M8 不得提前开始正式集成，除非满足：

1. M1 基础领域能力稳定；
2. M3 文献闭环稳定；
3. M4 数据版本稳定；
4. M5 统计和图表黄金测试通过；
5. M6 Claim 可用；
6. M7 证据链核心查询可用；
7. Tool Contract 已冻结；
8. ApprovalRecord 可用；
9. ToolCall 和 ModelInvocation 可审计；
10. Agent 不能绕过 Service 和权限。

可以提前设计 Agent Schema，但不得提前让 Agent 执行正式副作用。

## 16.3 本阶段范围

```text
AgentRun
ToolCall
ModelInvocation
AgentContext
Guardrail
ToolRegistry
ApprovalGate
```

## 16.4 明确不做

* 不采用自由多 Agent；
* 不允许 Agent 直接写数据库；
* 不允许 Agent 获取数据库 Session；
* 不允许任意代码执行；
* 不允许 Agent 自动审批；
* 不允许模型生成统计事实；
* 不允许无限工具循环；
* 不允许跨项目检索；
* 不允许模型决定用户权限。

## 16.5 Agent 能力分层

### 第一层：只读工具

优先接入：

```text
get_project_state
get_pending_actions
get_research_question
get_literature_matrix
get_document_status
get_dataset_profile
get_data_quality_issues
get_analysis_result
get_figure
get_manuscript_issues
get_claim_evidence
get_export_status
```

### 第二层：建议与计划工具

```text
parse_research_question
generate_query_plan
suggest_literature_decision
summarize_evidence_set
generate_topic_candidates
suggest_cleaning_plan
suggest_analysis_plan
suggest_figure_plan
review_manuscript_language
suggest_claim_links
```

### 第三层：有副作用工具

P0-Must 仅保留必要工具：

```text
start_literature_search
start_document_parse
start_literature_extraction
start_data_quality_run
execute_approved_cleaning_plan
run_approved_analysis_plan
render_approved_figure_plan
start_manuscript_check
export_repro_package
```

有副作用工具必须要求：

* 项目权限；
* 对象状态；
* ApprovalRecord；
* Idempotency-Key；
* ToolCall；
* Job；
* Worker 重新校验。

## 16.6 后端交付物

* AgentRun；
* 项目上下文；
* 工具白名单；
* Tool Schema；
* ToolCall；
* ModelInvocation；
* Guardrail；
* 最大工具调用次数；
* 超时；
* 重试；
* 项目边界；
* 来源校验；
* ApprovalGate；
* Agent 结果结构化；
* Tracing；
* 失败回退。

## 16.7 前端交付物

Agent 面板只负责：

* 下一步建议；
* 信息补充；
* 任务规划；
* 工具调用说明；
* 审批请求；
* 结构化结果摘要；
* 错误提示；
* 来源链接。

正式科研数据仍在结构化工作台展示。

前端必须区分：

* Agent 建议；
* 系统事实；
* 确定性结果；
* 用户确认；
* 待审批操作。

## 16.8 数据库与迁移

至少创建：

```text
agent_runs
tool_calls
model_invocations
```

关键约束：

* 所有记录含 `project_id`；
* ToolCall 追加写；
* ModelInvocation 追加写；
* 参数保存脱敏摘要；
* 高风险工具记录 ApprovalRecord；
* 失败调用保留错误；
* 工具结果保留来源对象 ID。

## 16.9 API 与契约

核心端点：

```text
POST   /api/v1/projects/{project_id}/agent-runs
GET    /api/v1/agent-runs/{agent_run_id}
POST   /api/v1/agent-runs/{agent_run_id}/messages
GET    /api/v1/agent-runs/{agent_run_id}/tool-calls
GET    /api/v1/tool-calls/{tool_call_id}
```

Agent 输出必须使用结构化 Envelope。

## 16.10 Guardrail

必须检查：

* 当前项目；
* 当前用户；
* 工具白名单；
* 工具参数；
* 来源 ID；
* 状态机；
* ApprovalRecord；
* 幂等；
* 敏感数据；
* 最大调用数；
* 超时；
* 禁止工具；
* 模型输出 Schema；
* 提示注入。

## 16.11 测试要求

必须覆盖：

* 未注册工具拒绝；
* 任意 Python 拒绝；
* 任意 Shell 拒绝；
* 任意 SQL 拒绝；
* 跨项目工具拒绝；
* 缺少 Approval 拒绝；
* 过期 Approval 拒绝；
* 内容变化后 Approval 失效；
* 工具幂等；
* ToolCall 审计；
* ModelInvocation 脱敏；
* 模型输出 Schema 错误；
* 来源缺失；
* 工具循环限制；
* PDF 提示注入；
* Agent 不修改统计数字；
* Agent 不完成用户审批。

## 16.12 安全要求

* 模型不是权限边界；
* 工具执行必须经过 Service；
* Agent 不接触数据库 Session；
* 敏感字段最小化发送；
* Prompt 区分系统规则、用户任务和不可信文档；
* 不记录完整 Token；
* 不记录完整敏感数据；
* Tool 参数二次校验；
* Worker 再次校验 Approval。

## 16.13 演示成果

```text
用户打开 Agent 面板
→ Agent 读取项目状态
→ 指出当前缺少数据质量检查
→ 用户同意创建检查
→ Agent 调用受控工具
→ 创建 Job
→ 前端显示进度
→ Agent 汇总结构化结果
→ 提醒用户批准 CleaningPlan
→ Agent 不替用户批准
```

## 16.14 完成条件

1. Agent 只能调用白名单工具；
2. Agent 无任意代码能力；
3. Agent 不直接写数据库；
4. 有副作用工具受 Approval 和幂等保护；
5. ToolCall 和 ModelInvocation 可审计；
6. 提示注入测试通过；
7. Agent 建议与系统事实明确区分；
8. Agent 可完成 P0-Must 主流程的阶段导航；
9. Agent 失败不影响用户直接使用结构化页面。

## 16.15 可并行任务

* Agent Schema；
* Tool Registry；
* Guardrail；
* 前端 Agent 面板；
* Agent 安全测试；
* Prompt 和黄金响应。

## 16.16 阻塞下一阶段的缺陷

* 任意工具可调用；
* 缺少 Approval 可执行；
* Agent 跨项目；
* ToolCall 无审计；
* 模型可修改统计数字；
* 提示注入可改变工具行为；
* Agent 失败导致核心页面不可用。

## 16.17 Codex 推荐任务顺序

1. AgentRun；
2. ToolCall；
3. ModelInvocation；
4. 只读工具；
5. Tool Registry；
6. Guardrail；
7. 建议工具；
8. 有副作用工具；
9. ApprovalGate；
10. 前端面板；
11. Agent 安全测试；
12. M8 E2E。

---
