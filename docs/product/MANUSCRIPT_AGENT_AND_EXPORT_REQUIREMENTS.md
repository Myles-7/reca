# 论文、证据链、导出与 Agent 需求

| 项目 | 内容 |
| --- | --- |
| 所属入口文档 | [PRODUCT_REQUIREMENTS.md](../PRODUCT_REQUIREMENTS.md) |
| 文档状态 | APPROVED FOR M1 DEVELOPMENT |
| Migration status | COMPLETE |

## 权威范围

本文件是 DOCX、Claim、MANU-P0-018、证据链、ReproPackage、单总控 Agent 和 AI 治理需求的唯一完整定义位置。

## 不负责的内容

项目、文献、数据分析、UX、API 字段和测试指标。

## 文档导航

- [主产品需求文档](../PRODUCT_REQUIREMENTS.md)
- [项目、研究问题与候选问题](./PROJECT_AND_RESEARCH_REQUIREMENTS.md)
- [文献与原文证据](./LITERATURE_AND_EVIDENCE_REQUIREMENTS.md)
- [数据、分析与图表](./DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md)
- [论文、证据链、导出与 Agent](./MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md)
- [UX、非功能与追踪](./UX_NONFUNCTIONAL_AND_TRACEABILITY.md)

---

# 23. 模块十一：DOCX 论文质控

python-docx 负责常见段落、Run、表格、样式、关系和图片处理；lxml/受控
OOXML 仅补充经过黄金样例验证的字段、批注、编号或关系读取能力。所有修改
生成派生 ManuscriptVersion，原 DOCX 永不覆盖。

Competition Core 使用简单确定性引用核对和格式化；选定 CSL Styles 以固定
Commit、文件哈希、`<rights>` 和 Locale 的资源快照接入。完整 Citation
Engine 必须隔离并通过许可证决策，citeproc-js 当前仍需实验和治理审查。
Zotero 兼容只覆盖明确支持的 RIS、BibTeX、CSL JSON 等交换格式，不建设或
复制完整 Zotero 桌面/Web 产品。

<a id="manu-p0-001"></a>
## 23.1 MANU-P0-001 DOCX 上传

仅支持 DOCX。

原文件保存为只读 Artifact。

<a id="manu-p0-002"></a>
## 23.2 MANU-P0-002 文档解析

读取：

* 段落；
* 标题样式；
* 表格；
* 图题；
* 表题；
* 参考文献区域；
* 文内引用；
* 数字表达；
* 基础文档顺序。

复杂公式、文本框、修订记录只读或提示不支持。

<a id="manu-p0-003"></a>
## 23.3 MANU-P0-003 引用提取

支持常见：

* 作者—年份；
* 顺序编码；
* 中文括号；
* 英文括号。

P0 不保证覆盖所有自定义格式。

<a id="manu-p0-004"></a>
## 23.4 MANU-P0-004 文内与文末双向核对

检查：

* 文内有、文末无；
* 文末有、正文未引用；
* 作者年份不一致；
* 顺序号异常；
* 重复条目。

<a id="manu-p0-005"></a>
## 23.5 MANU-P0-005 项目文献库核对

论文引用与项目 LiteratureRecord 比较。

状态：

* 已匹配；
* 可能匹配；
* 未匹配；
* 元数据冲突。

<a id="manu-p0-006"></a>
## 23.6 MANU-P0-006 DOI 格式检查

检查 DOI 基础格式，不保证在线真实性核验。

<a id="manu-p0-007"></a>
## 23.7 MANU-P0-007 样本量检查

提取常见样本量表达，并比较：

* 摘要；
* 方法；
* 结果；
* 表格；
* AnalysisResult。

<a id="manu-p0-008"></a>
## 23.8 MANU-P0-008 统计数字核对

可核对：

* p 值；
* 相关系数；
* 回归系数；
* 样本量；
* 百分比；
* 均值；
* 标准差。

正式核对优先基于项目内部 AnalysisResult。

<a id="manu-p0-009"></a>
## 23.9 MANU-P0-009 图文一致性

检查：

* 正文引用图表编号；
* Figure 与正文数字；
* 图表编号顺序；
* 图注基础信息。

<a id="manu-p0-010"></a>
## 23.10 MANU-P0-010 因果夸大

识别：

* “导致”；
* “决定”；
* “证明”；
* “产生影响”；

并结合分析类型判断是否可能过度。

<a id="manu-p0-011"></a>
## 23.11 MANU-P0-011 样本外推

检查：

* 从局部样本扩大到所有学生；
* 从单校扩大到全国；
* 从横断面扩大到长期效果；
* 从当前文献集合扩大到整个领域。

<a id="manu-p0-012"></a>
## 23.12 MANU-P0-012 学术共识夸大

检查：

* 单篇研究写成广泛共识；
* 少量文献写成一致结论；
* 忽略反例。

<a id="manu-p0-013"></a>
## 23.13 MANU-P0-013 术语一致性

检查：

* 同一变量多种名称；
* 中英文不一致；
* 缩写未定义；
* 研究对象名称变化；
* 方法名称不一致。

<a id="manu-p0-014"></a>
## 23.14 MANU-P0-014 基础格式

检查：

* 标题层级；
* 图表编号；
* 缩写首次出现；
* 数字与单位；
* 中英文标点；
* 多余空格。

<a id="manu-p0-015"></a>
## 23.15 MANU-P0-015 问题清单

每个问题包含：

* Issue ID；
* 严重程度；
* 章节；
* 段落位置；
* 原文；
* 问题类型；
* 原因；
* 证据；
* 建议；
* 是否可自动修复；
* 状态。

<a id="manu-p0-016"></a>
## 23.16 MANU-P0-016 自动修复边界

P0 可自动修复：

* 多余空格；
* 明确的低风险标点；
* 部分基础样式；
* 简单标题样式。

P0 不自动修复：

* 统计数字；
* 引用内容；
* 研究结论；
* 因果表述；
* 公式；
* 复杂图表；
* 修订记录。

<a id="manu-p0-017"></a>
## 23.17 MANU-P0-017 验收标准

* 原文件不覆盖；
* 问题可定位；
* 数字可与分析结果核对；
* 引用可双向检查；
* 因果风险可识别；
* 高风险问题不自动改；
* 输出问题清单；
* 处理失败不损坏原文件。

<a id="manu-p0-018"></a>
## 23.18 MANU-P0-018 修订漂移审核

系统比较两个 ManuscriptVersion 时，必须生成只读审核结果，不自动修改
论文。至少检查：

* 数字、样本量、p 值和统计量变化；
* 引用删除或替换后结论仍保留；
* “可能”“在本样本中”等限定词被删除；
* “相关”被升级为“导致”等因果表述；
* 样本内结论扩大为普遍结论；
* Figure、DatasetVersion 或 AnalysisResult 版本不一致；
* 新增 Claim 缺少 EvidenceSpan 或 AnalysisResult。

该审核是风险提示和复核输入，不是自动接受或拒绝论文的机制。

**Competition Core** 仅依赖确定性或高稳定规则：数字/样本量/p 值/统计量变化、引用删除、因果关键词升级，以及 Figure、AnalysisResult、DatasetVersion 版本不一致。**P0-Full** 可在不阻塞 Core 的前提下增加模型辅助的限定词、范围、新 Claim 和复杂语义漂移检测。该需求的正式 Job 类型为 `MANUSCRIPT_REVISION_AUDIT`，结果类型为 `REVISION_DRIFT_AUDIT`；输入为 before/after ManuscriptVersion 与引用的结果版本，永不修改原 DOCX。

---

# 24. 模块十二：科研证据链

<a id="evid-p0-001"></a>
## 24.1 EVID-P0-001 Claim

Claim 表示：

* 综述结论；
* 数据结果表述；
* 论文论述；
* 方法判断；
* 候选研究问题依据。

<a id="evid-p0-002"></a>
## 24.2 EVID-P0-002 Claim 类型

* `LITERATURE_CLAIM`；
* `DATA_CLAIM`；
* `ANALYSIS_CLAIM`；
* `MANUSCRIPT_CLAIM`；
* `TOPIC_CLAIM`。

<a id="evid-p0-003"></a>
## 24.3 EVID-P0-003 Claim 与文献证据

关系：

* 支持；
* 反对；
* 限定；
* 不确定。

<a id="evid-p0-004"></a>
## 24.4 EVID-P0-004 Claim 与数据

关联：

* Dataset；
* DatasetVersion；
* 数据身份证；
* 数据限制。

<a id="evid-p0-005"></a>
## 24.5 EVID-P0-005 Claim 与处理

关联：

* CleaningPlan；
* DataTransformation；
* 上游版本；
* 下游版本。

<a id="evid-p0-006"></a>
## 24.6 EVID-P0-006 Claim 与分析

关联：

* AnalysisPlan；
* AnalysisRun；
* AnalysisResult；
* CodeArtifact；
* 环境。

<a id="evid-p0-007"></a>
## 24.7 EVID-P0-007 Claim 与图表

关联：

* Figure；
* 图表版本；
* 数据版本；
* 分析运行。

<a id="evid-p0-008"></a>
## 24.8 EVID-P0-008 Claim 与人工确认

关联：

* ApprovalRecord；
* 确认人；
* 确认时间；
* 确认内容。

<a id="evid-p0-009"></a>
## 24.9 EVID-P0-009 Claim 与审核

AuditResult 状态：

* 已验证；
* 待确认；
* 证据不足；
* 来源不完整；
* 数据不一致；
* 图表不一致；
* 可能过度推断；
* 用户驳回。

<a id="evid-p0-010"></a>
## 24.10 EVID-P0-010 证据范围

页面必须显示：

* 当前文献数量；
* 数据版本；
* AnalysisRun；
* 用户确认版本；
* 审核时间；
* 限制。

<a id="evid-p0-011"></a>
## 24.11 EVID-P0-011 图谱页面

使用 React Flow。

节点可点击：

* 文献节点打开详情；
* EvidenceSpan 跳转 PDF；
* DatasetVersion 查看身份证；
* AnalysisRun 查看方法和代码；
* Figure 打开图表；
* Approval 查看确认记录；
* Audit 查看审核结果。

<a id="evid-p0-012"></a>
## 24.12 EVID-P0-012 完整度

完整度用于提示，不作为科研质量分数。

可计算：

* 是否有来源；
* 是否有原文；
* 是否有数据版本；
* 是否有分析结果；
* 是否有确认；
* 是否有审核。

<a id="evid-p0-013"></a>
## 24.13 EVID-P0-013 失效传播

上游对象失效时：

* 关联 Claim 标记待审核；
* 图表显示警告；
* 论文问题重新检查；
* 不删除旧链路。

<a id="evid-p0-014"></a>
## 24.14 EVID-P0-014 验收标准

* 可展示完整链路；
* 节点可点击；
* 证据范围可见；
* 上游失效有提示；
* 图谱来自后端真实关系；
* 不在前端写死；
* Claim 可追溯到文献或分析结果。

---

# 25. 模块十三：科研复现包

<a id="export-p0-001"></a>
## 25.1 EXPORT-P0-001 导出入口

项目所有者或授权成员可创建导出任务。

<a id="export-p0-002"></a>
## 25.2 EXPORT-P0-002 导出内容

包含：

* 研究问题；
* 检索计划；
* 文献清单；
* 文献矩阵；
* EvidenceSpan；
* 文献决策；
* 数据身份证；
* 数据版本；
* 处理日志；
* 分析计划；
* 分析代码；
* 分析结果；
* 图表；
* 论文检查；
* 证据图；
* Agent 日志；
* 审批日志；
* 环境锁定信息。

<a id="export-p0-003"></a>
## 25.3 EXPORT-P0-003 manifest.json

记录：

* 文件路径；
* Artifact ID；
* SHA-256；
* 对象类型；
* 上游对象；
* 创建时间；
* 版本；
* 是否包含敏感内容。

<a id="export-p0-004"></a>
## 25.4 EXPORT-P0-004 README_REPRODUCE.md

说明：

* 项目背景；
* 数据来源；
* 运行步骤；
* 环境要求；
* 分析入口；
* 已知限制；
* 隐私提示。

<a id="export-p0-005"></a>
## 25.5 EXPORT-P0-005 导出前检查

检查：

* 数据许可；
* 敏感信息；
* 失效结果；
* 缺少文件；
* 证据不足；
* 未确认项。

<a id="export-p0-006"></a>
## 25.6 EXPORT-P0-006 异步导出

导出使用 Job。

<a id="export-p0-007"></a>
## 25.7 EXPORT-P0-007 导出版本

每次导出创建独立 Export 和 ReproPackage。

<a id="export-p0-008"></a>
## 25.8 EXPORT-P0-008 验收标准

* ZIP 可正常解压；
* manifest 完整；
* 文件哈希一致；
* 目录结构稳定；
* 失效对象有提示；
* 敏感内容有警告；
* 不覆盖历史导出。

---

# 26. 模块十四：科研总控智能体

M8 计划使用 OpenAI Agents SDK 承担 Runner、Function Tool、结构化输出、
HITL、usage 和受控 tracing 等运行机制。SDK Session 只用于对话连续性，
SDK Trace 只用于遥测，均不得替代 ResearchProject、AgentRun、ToolCall、
ModelInvocation 或 AuditLog。

经 ADR-001 审查的 ARS Workflow、Prompt、Policy Marker、脚本和测试可选择性
复用，但必须映射到 RECA Project、Approval、Evidence、Prompt manifest 和
Tool 契约。单总控 Agent、M8 接入、白名单工具和确定性结果边界保持不变。

<a id="agent-p0-001"></a>
## 26.1 AGENT-P0-001 产品定位

P0 采用：

> 一个科研总控 Agent + 白名单工具组 + 可信审核步骤。

不采用自由多智能体互相对话。

<a id="agent-p0-002"></a>
## 26.2 AGENT-P0-002 阶段判断

Agent 可读取项目状态并判断：

* 当前阶段；
* 缺少内容；
* 待确认事项；
* 下一步建议。

<a id="agent-p0-003"></a>
## 26.3 AGENT-P0-003 任务规划

Agent 可生成结构化任务计划，但不能直接改变项目状态。

<a id="agent-p0-004"></a>
## 26.4 AGENT-P0-004 工具选择

Agent 只能调用：

* 文献工具；
* 数据工具；
* 分析工具；
* 图表工具；
* 论文工具；
* 证据审核工具；
* 导出工具。

<a id="agent-p0-005"></a>
## 26.5 AGENT-P0-005 用户确认

遇到高风险操作时，Agent 必须：

1. 说明操作；
2. 说明影响；
3. 创建审批请求；
4. 等待用户批准；
5. 不自行继续执行。

<a id="agent-p0-006"></a>
## 26.6 AGENT-P0-006 结构化输出

所有关键输出必须通过 Schema 校验。

<a id="agent-p0-007"></a>
## 26.7 AGENT-P0-007 运行记录

保存：

* AgentRun；
* 输入摘要；
* 模型；
* 提示版本；
* ToolCall；
* 结果；
* 错误；
* 耗时；
* Project ID。

<a id="agent-p0-008"></a>
## 26.8 AGENT-P0-008 审核步骤

重要结果后执行：

* 文献证据审核；
* 分析结果来源审核；
* 图表版本审核；
* 论文结论审核。

<a id="agent-p0-009"></a>
## 26.9 AGENT-P0-009 禁止行为

Agent 不得：

* 生成未检索文献；
* 计算统计数字；
* 修改原始数据；
* 批准自己的建议；
* 直接写数据库；
* 执行任意代码；
* 绕过权限；
* 隐藏工具错误；
* 把 Mock 结果当真实结果。

<a id="agent-p0-010"></a>
## 26.10 AGENT-P0-010 验收标准

* 只能调用白名单工具；
* 所有调用有记录；
* 未批准操作不能执行；
* 结果通过 Schema；
* 工具失败返回结构化错误；
* Agent 不直接写正式统计结果；
* Agent 不替用户确认。

---

# AI 治理与审计需求

以下五项需求原已在主 PRD 的可信工作流追踪矩阵中定义。本节将同一语义提升为唯一完整定义，不扩大 P0，也不授权自由多 Agent。

<a id="agov-p0-001"></a>
## AGOV-P0-001 PromptContract manifest 与模型调用治理

首次模型调用前必须在 M1 建立版本化 PromptContract manifest 和 ModelInvocation 记录。必须验证 manifest、输出 Schema 和数据访问契约；该治理需求属于 Competition Core，但不代表正式 Agent 已接入。

<a id="agov-p0-002"></a>
## AGOV-P0-002 模型数据访问等级强制

ModelInvocation 必须记录 requested、max 和 effective data access；请求超过允许上限时必须拒绝或缩减，不能只依赖 Prompt 声明。该需求在 M1 建立并属于 Competition Core。

<a id="agov-p0-003"></a>
## AGOV-P0-003 降级记录与用户披露

主 Provider 或能力不可用时必须产生 DegradationRecord DTO，并向用户披露 fallback Provider、原因和影响。不得静默跳过，也不得把降级显示为完整通过。该需求从 M1 起适用于发生外部能力调用的阶段。

<a id="agov-p0-004"></a>
## AGOV-P0-004 ProjectContextSnapshot 与 AgentRun 上下文

M8 单总控 Agent 必须使用由数据库派生的 ProjectContextSnapshot；AgentRun 记录使用的 snapshot 版本和哈希，并验证 stale/rebuild。Snapshot 是只读派生上下文，不是第二套业务事实来源。

<a id="agov-p0-005"></a>
## AGOV-P0-005 StageResolver 与受控路由

M8 的 StageResolver 必须结合项目阶段、对象和前置条件产生受控路由，ToolCall 只能选择白名单工具。阶段与前置条件决策必须进入黄金测试；该需求不允许自由多 Agent。
