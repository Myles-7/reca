# Open Source Governance

- 文档名称：Open Source Governance
- 文档版本：1.3.0
- 所属入口文档：[SECURITY_AND_OPEN_SOURCE.md](../SECURITY_AND_OPEN_SOURCE.md)
- 文档状态：APPROVED FOR M1 DEVELOPMENT
- 最后更新时间：2026-07-31
- Migration status: COMPLETE

## 变更记录

| 版本 | 日期 | 状态 | 变更说明 |
| --- | --- | --- | --- |
| 1.0.0 | 2026-07-31 | Conditional Approval | 文档拆分后的依赖、许可证、Vendor、来源和发布治理基线 |
| 1.1.0 | 2026-07-31 | Conditional Approval | 采用 effect-first 复用模式、保守许可证分类和条件式 Adapter 政策 |
| 1.2.0 | 2026-07-31 | Conditional Approval | 增加全部研究项目的许可证分类矩阵、隔离条件和实际状态边界 |
| 1.2.1 | 2026-07-31 | Conditional Approval | 明确阶段 11 审查时 ARS-Codex 尚未进入仓库的事实状态；政策不变 |
| 1.3.0 | 2026-07-31 | Project Owner Decision | 采用最大合法复用边界：宽松许可证默认直接采用，特殊许可证在满足实际义务时允许最宽集成模式，不再以额外内部审批或净室重写作为默认门槛 |

## 权威范围

本文件是依赖与供应链、第三方复用模式、许可证分类、来源台账、Fork、
Vendor、Submodule、选择性复制、归属、Adapter、数据/PDF 权利、ARS-Codex
和根许可证状态的唯一完整定义。

不负责运行时身份权限、文件执行控制或事件处理。返回
[安全与开源治理入口](../SECURITY_AND_OPEN_SOURCE.md)。根许可证选择仍由
项目负责人单独决定。

## 1. 最大合法复用原则

在许可证允许、来源明确并能够维护的前提下，RECA 优先复用成熟开源项目，
以提升作品效果、开发速度和演示稳定性。自行重新实现不再是默认要求。

项目负责人的默认授权边界为 `MAXIMUM_LAWFUL_REUSE`：在固定版本的实际
许可证和其他适用权利允许的最大范围内，可以直接使用包、服务、Fork、完整
Vendor、Submodule、选择性复制、修改 Prompt/工作流/脚本/测试，或组合这些
方式。工程实现应选择交付最快、效果最好且可验证的模式，不因“更保守”而
默认改写已有成熟实现。

具体执行规则：

- MIT、BSD、Apache、PostgreSQL License 等经核验的宽松许可证内容，默认
  允许直接依赖、Fork、完整 Vendor、Submodule、选择性复制和修改；无需为
  “是否允许复用”再取得单独项目级批准，可在同一实现 PR 中完成来源登记；
- Copyleft、文件级许可证、非商业或自定义许可证内容不因类别名称被一律
  禁止；只要当前使用、修改、托管和分发方式能够满足实际条款，即可采用
  许可证允许的最宽集成模式；
- `RESEARCH_REFERENCE`、`DESIGN_REFERENCE` 和 `DEFERRED` 是当前工程建议，
  不是永久禁用标签。实现 Spike 证明价值且许可证条件可满足时，可在同一
  变更中更新研究记录、ADR、Notices 和集成状态；
- 不强制为直接复用增加无收益的 Adapter、隔离服务或清洁室重实现；只有
  领域泄漏、替换、离线测试、安全或实际许可证义务产生明确收益时才采用；
- 署名、许可证文本、NOTICE、源码提供、相同许可证、非商业用途、商标、
  数据和素材权利等上游义务不是 RECA 内部审批项，不能由本政策豁免。

开源复用必须同时满足：

1. 效果和维护收益明确；
2. 来源与固定版本可追溯；
3. 实际许可证文本已核验；
4. 归属、许可证和适用 NOTICE 被保留；
5. 复制路径和修改可识别；
6. 特殊限制与 RECA 自研内容可区分；
7. 不把第三方贡献表述为 RECA 全部原创；
8. 不绕过 Service、权限、科研真实性、数据版本和审批边界。

仓库公开、允许浏览或提供 Fork 按钮，不等于获得复制、修改或再分发许可。
本文档是工程治理政策，不构成法律意见。

## 2. 正式复用模式

每项第三方能力必须选择并记录一种主要模式；可以组合，但每种模式的边界
和文件必须可识别。

### 2.1 `PACKAGE_DEPENDENCY`

通过 Python、Bun/Node 或其他包管理器引入并锁定版本。适合成熟库和框架。

要求：锁文件、实际版本许可证核验、依赖来源、必要 NOTICE 和安全扫描。

### 2.2 `INDEPENDENT_SERVICE`

以独立进程、容器或远程服务使用，例如数据库、对象存储或解析服务。

要求：记录镜像/版本、许可证或服务条款、暴露端口、数据发送范围和失败
降级。网络服务是否使用 Adapter 由第 8 节决定。

### 2.3 `FORK`

保留上游 Git 历史或明确来源，在独立仓库/分支持续修改。

要求：保留原许可证和归属、固定 Fork 起点、记录修改、跟踪上游安全与许可
变化，并在分发前复审。

### 2.4 `VENDOR`

把第三方项目或其稳定快照放入 RECA 仓库的独立目录。

要求：目录隔离、原许可证、NOTICE（如适用）、上游仓库/Commit、修改记录
和构建边界。不得 Vendor 无许可证或来源不明内容。

### 2.5 `GIT_SUBMODULE`

以固定 Commit 的 Git Submodule 引用上游或 Fork。

要求：固定 Commit、初始化说明、许可证核验、离线/CI 可用性和更新责任。
Submodule 不是许可证隔离的自动保证。

### 2.6 `SELECTIVE_COPY`

复制明确的文件、代码片段、Prompt、工作流、脚本、测试结构或测试材料。

要求：逐路径记录来源和修改；保留文件级归属/许可证头（如要求）；在
`THIRD_PARTY_NOTICES.md` 和来源研究记录中说明；避免把不同许可证内容
无标识混入自研文件。

### 2.7 `RESEARCH_REFERENCE`

阅读、比较和吸收思想，不复制受版权保护的表达或文件。

要求：来源研究记录可保存仓库、Commit、许可证和借鉴结论。没有实际纳入
内容时，不应在 Notices 中错误声称存在运行时依赖或复制。

### 2.8 `CLEAN_ROOM_REIMPLEMENTATION`

团队根据公开思想或接口独立重新实现，用于许可证不适合、耦合过高或需要
完全自有实现的场景。

这是可选方案，不再是默认要求。使用时记录参考来源、隔离方式和独立实现
证据。它与 M0 infrastructure clean-room acceptance 无关。

## 3. 最小准入记录

复制、Fork、Vendor、Submodule 或修改第三方内容时，必须最迟在同一实现
PR 合并前，于 ADR、来源研究记录、依赖审查记录或等价台账中保存：

```yaml
project_name: ""
repository: ""
upstream_commit_or_tag: ""
license: ""
license_file_path: ""
integration_mode: ""
copied_paths: []
modified_paths: []
modification_summary: ""
attribution_location: ""
special_restrictions: []
commercialization_review_required: false
reviewed_by: ""
reviewed_at: ""
```

规则：

- `license` 不得仅凭记忆填写；
- `license_file_path` 指向固定版本中的实际文本或官方材料；
- 没有复制时 `copied_paths` 明确为 `none` 或空列表；
- 修改后更新 `modified_paths` 和摘要；
- 特殊许可证内容必须标记商业化/用途变化复审；
- 记录描述实际状态，不能把计划中的 Vendor 或依赖写成已引入。

## 4. 许可证分类

使用以下义务分类，不在未经核验时给出法律结论。分类用于识别必须履行的
条件，不作为比上游许可证更严格的内部禁用等级：

### 4.1 `PERMISSIVE_REUSE_ALLOWED`

固定版本的实际许可证明确允许目标复制、修改和再分发，并且归属、NOTICE
等义务可满足。常见许可证名称只能作为线索，仍需核验实际文本。

### 4.2 `COPYLEFT_REVIEW_REQUIRED`

包含强/弱 Copyleft、文件级或网络交互义务。不是一律禁止，但必须确认：

- 义务触发方式；
- 源码提供或同许可证要求；
- 动态/静态链接、修改文件和独立服务边界；
- 分发或网络提供时的额外义务；
- 与未来根许可证和发布方式的关系。

### 4.3 `NONCOMMERCIAL_RESTRICTION`

限制商业使用或将使用范围限定为非商业。必须记录用途意图和复审门，不能
仅因“校赛”就宣称法律上已满足非商业条件。

### 4.4 `NO_DERIVATIVES_RESTRICTION`

限制改编或衍生使用。选择性复制、修改、翻译、组合和格式转换可能受到
影响，必须单独审查；不应默认允许修改后纳入。

### 4.5 `CUSTOM_LICENSE_REVIEW`

自定义、研究专用、教育专用、源代码可见或含附加条款的许可证。逐条核验
用途、修改、分发、署名、专利、商标、托管和商业化条件。

### 4.6 `NO_LICENSE_DO_NOT_COPY`

公开仓库没有许可证时：

- 可以阅读、运行授权范围内的公开服务或研究思想；
- 不得复制、修改后分发、Vendor 或把代码/Prompt/测试纳入正式仓库；
- 取得作者明确授权后重新记录和分类。

### 4.7 `UNKNOWN_SOURCE_DO_NOT_COPY`

无法确认作者、仓库、Commit 或来源链的内容不得进入正式仓库。不得从不明
网盘、聊天粘贴、截图反推或无来源压缩包复制。

### 4.8 研究项目许可证分类矩阵

下表基于已固定的研究 Commit 或当前实际采用版本，用于选择工程边界，不构成法律意见。实际引入时仍须重新读取对应版本的许可证、NOTICE、文件级 rights 和打包内容；`RESEARCHED`/`PLANNED` 不代表已复制、安装或分发。

| 项目 | 当前分类 | 默认治理边界 | 采用前必须确认 |
| --- | --- | --- | --- |
| Full Stack FastAPI Template | `PERMISSIVE_REUSE_ALLOWED`（MIT） | 已选择性内化的 M0 基线；不整体覆盖 RECA 特化树 | 保留 MIT snapshot、来源 Commit 和修改事实 |
| Celery | `PERMISSIVE_REUSE_ALLOWED`（BSD-3-Clause；文档另有 CC BY-SA） | 直接依赖；业务状态仍在 Job/ProcessingRun | 实际包及复制文档的不同许可证 |
| Valkey | `PERMISSIVE_REUSE_ALLOWED`（BSD-3-Clause，含文件级第三方许可） | 独立服务；仅作 broker/cache/短期状态 | 镜像内容、文件级 notices 和固定版本 |
| pgvector | `PERMISSIVE_REUSE_ALLOWED`（PostgreSQL License） | PostgreSQL 扩展独立服务边界 | 扩展/镜像版本、PostgreSQL License 归属 |
| pgvector-python | `PERMISSIVE_REUSE_ALLOWED`（MIT） | 计划直接依赖；不得泄漏 ORM 对象到公共契约 | 实际包版本和兼容性 Spike |
| PyAlex | `PERMISSIVE_REUSE_ALLOWED`（MIT） | 直接依赖加轻量 Provider | OpenAlex 服务条款、限流与原始响应权利另审 |
| GROBID | `PERMISSIVE_REUSE_ALLOWED`（Apache-2.0） | 独立服务；TEI 经 RECA 转换 | 镜像来源、NOTICE、模型/资源和 PDF 权利 |
| grobid-client-python | `PERMISSIVE_REUSE_ALLOWED`（Apache-2.0） | 先做 client 与自研 HTTP Spike；选择性 Vendor 需逐路径登记 | Vendor 路径、NOTICE、修改和文件系统边界 |
| PDF.js | `PERMISSIVE_REUSE_ALLOWED`（Apache-2.0） | 前端直接依赖；只负责显示和交互 | 包/worker 同版本、NOTICE、字体/示例资产 |
| PaperQA2 | `PERMISSIVE_REUSE_ALLOWED`（Apache-2.0） | 可选择性 Vendor 检索、Prompt 或测试；只产出候选证据 | 精确复制路径、NOTICE、修改及依赖许可证 |
| ASReview | `PERMISSIVE_REUSE_ALLOWED`（Apache-2.0） | Provider/算法边界；只给排序建议 | 是否复制 Web/素材、模型保存与依赖许可证 |
| Pandera | `PERMISSIVE_REUSE_ALLOWED`（MIT） | P0 唯一主要数据质量运行时 | 实际 extras、依赖和版本兼容 |
| SciPy | `PERMISSIVE_REUSE_ALLOWED`（BSD-3-Clause，含 bundled licenses） | 确定性统计直接依赖 | wheel/二进制捆绑许可证和运行平台 |
| statsmodels | `PERMISSIVE_REUSE_ALLOWED`（BSD-3-Clause） | 结构化数值直接依赖；Summary 非业务结果 | 依赖、版本和结果字段兼容 |
| Matplotlib | `CUSTOM_LICENSE_REVIEW`（Matplotlib 自定义许可及 bundled licenses/fonts） | 直接依赖可行；字体和打包资源单独登记 | 实际 wheel、字体、样式和输出分发义务 |
| DVC | `PERMISSIVE_REUSE_ALLOWED`（Apache-2.0） | Development-only/设计参考，不替代 DatasetVersion | 若真实安装，记录 CLI、远端和传递依赖 |
| Great Expectations | `PERMISSIVE_REUSE_ALLOWED`（Apache-2.0） | Design/test reference；不成为第二套 P0 运行时 | 复制测试/文案时逐路径登记 |
| python-docx | `PERMISSIVE_REUSE_ALLOWED`（MIT） | 直接依赖；受控 OOXML 增强；原 DOCX 不覆盖 | lxml 等依赖许可证和 OOXML fixture 权利 |
| CSL Styles | `COPYLEFT_REVIEW_REQUIRED`（仓库 CC BY-SA 3.0；文件 `<rights>` 可能不同） | 只快照最小 GB/T/APA 集合 | 每个 style/locale 的 Commit、hash、作者、rights 和修改共享义务 |
| citeproc-js | `CUSTOM_LICENSE_REVIEW`（CPAL/AGPL 元数据冲突未解决） | 默认延期；采用时必须隔离服务/worker或选择替代处理器 | 固定版本实际文本、网络/分发义务和替代 ADR |
| TanStack Table | `PERMISSIVE_REUSE_ALLOWED`（MIT） | 已存在直接依赖；选择状态不是业务决定 | 包版本、归属和功能里程碑状态 |
| xyflow / React Flow | `PERMISSIVE_REUSE_ALLOWED`（MIT） | 计划直接依赖；后端证据图是权威 | 包版本、归属和大型图性能 |
| Zotero | `COPYLEFT_REVIEW_REQUIRED`（AGPL-3.0 及第三方 notices） | 默认 `DESIGN_REFERENCE`；不复制桌面源码 | 交换格式/数据权利与任何源码复制义务 |
| Zotero Web Library | `COPYLEFT_REVIEW_REQUIRED`（AGPL-3.0） | 默认 `DESIGN_REFERENCE`；独立实现 UX | 不复制源码、样式或资产；如改变策略需单独审查 |
| OpenAI Agents SDK | `PERMISSIVE_REUSE_ALLOWED`（MIT） | M8 直接依赖候选；Session/Trace 非业务权威 | 实际版本、托管/MCP 工具条款和 trace 数据范围 |
| ARS-Codex | `NONCOMMERCIAL_RESTRICTION`（CC BY-NC 4.0） | 条件式选择性或完整 Vendor；当前未复制 | `NONCOMMERCIAL_INTENT_DECLARED`、逐路径归属/隔离及商业化复审 |

任何项目固定版本出现 `NO_LICENSE_DO_NOT_COPY` 或来源无法验证时，以该分类覆盖本表中的研究结论并停止复制。研究记录可以继续用于比较，但 Notices 不得制造已集成状态。

## 5. 宽松许可证复用

对核验为 `PERMISSIVE_REUSE_ALLOWED` 的内容，可以：

- 整体 Fork；
- 整体 Vendor；
- 选择性复制；
- 修改；
- 与 RECA 自研模块组合；
- 作为包依赖或独立服务。

必须：

- 保留许可证文本；
- 保留版权归属；
- 按上游要求保留 NOTICE；
- 记录仓库和 Commit/Tag；
- 记录复制路径和修改；
- 不声称第三方内容全部原创；
- 复核商标、数据、模型、字体和素材是否另有条款。

## 6. Copyleft 与文件级许可证

Copyleft 不一律禁止。可采用：

- `INDEPENDENT_SERVICE`；
- 完整 `FORK`；
- 单独 `VENDOR`；
- 在确认义务后的 `PACKAGE_DEPENDENCY` 或 `SELECTIVE_COPY`。

要求：

- 不把许可证义务不明的文件无标识混入自研模块；
- 保存第三方许可证并识别受其覆盖的路径；
- 文件级许可证头按要求保留；
- 公开分发、托管或用途变化前重新审查；
- 根许可证待决状态不能覆盖第三方文件自身许可证。

无法判断义务时，使用独立服务、研究参考、清洁室重实现或暂不引入，直到
审查完成。

## 7. 归属与目录结构

### 7.1 整体或大量复制

建议结构：

```text
vendor/<project>/
├── LICENSE
├── NOTICE                    # 若适用
├── UPSTREAM.md
├── ORIGINAL_COMMIT
├── MODIFICATIONS.md
└── ...
```

- `UPSTREAM.md`：项目、仓库、版本、作者、集成模式和特殊限制；
- `ORIGINAL_COMMIT`：固定 Commit 或 Tag；
- `MODIFICATIONS.md`：修改文件、日期、目的和维护说明；
- 上游要求保留文件头时不得删除；
- Vendor 内容不得被代码格式化或批量重写工具无意改动。

本政策只定义结构；本阶段不创建 `vendor/`。

### 7.2 选择性复制

至少在以下位置记录来源：

```text
THIRD_PARTY_NOTICES.md
docs/source-research/<project>.md
```

如许可证要求文件头归属，则保留文件头。混合文件应明确标注第三方部分、
修改和适用许可证，或优先拆分成独立文件。

### 7.3 Notices 准确性

`THIRD_PARTY_NOTICES.md` 只记录实际依赖、分发、复制或 Vendor 的内容。
仅阅读一个项目不应被写成运行时依赖。实际纳入内容后必须及时更新。

## 8. Adapter 决策规则

取消“所有第三方能力必须经过复杂 Adapter”的绝对要求。

### 8.1 必须使用 Adapter

- 外部 API 容易变化、远程、限额或可能更换；
- 同一能力需要多个实现切换；
- 第三方对象不能进入领域层或持久化契约；
- 需要离线 Mock、Recorded 或本地替代；
- 存在许可证隔离；
- 存在明显安全边界；
- 统一超时、错误和降级能产生明显测试收益。

### 8.2 允许直接集成

- 成熟稳定库；
- 接口很小；
- 没有现实替换需求；
- 不污染领域模型；
- 直接使用明显提高开发速度；
- 维护和测试成本低于抽象成本。

### 8.3 不可绕过的边界

即使直接集成，也不得绕过：

- 业务 Service 和项目权限；
- 科研真实性与确定性统计；
- Artifact 和 DatasetVersion 不可变规则；
- 输入/输出 Schema；
- 高风险确认和 ApprovalRecord；
- ModelInvocation、ToolCall 和降级记录。

Adapter/直接集成决定记录在来源审查或 ADR 中。小型稳定工具库无需为形式
单独创建 ADR，但必须记录许可证和版本。

## 9. 依赖与供应链

### 9.1 Competition Required

- 依赖来自官方包仓库、官方 Release、可信镜像或已审查 Vendor；
- Python、Bun/Node 和服务镜像版本锁定；
- 新增安装脚本和可执行构建 Hook 经过审查；
- Secret 与依赖扫描继续属于 M0 required CI；
- 实际执行路径相关且可利用的 Critical 风险阻断交付；
- 锁定版本的实际许可证被记录。

### 9.2 Competition Recommended

- 自动 SBOM；
- 镜像组件清单；
- Medium/Low 漏洞自动修复或阻断；
- 依赖活跃度和维护者风险评分；
- 自动许可证扫描。

缺少企业 SBOM 不阻断校赛交付，但依赖和第三方清单必须足以追溯版本和
许可证。

### 9.3 Future Production

正式漏洞 SLA、集中制品签名、组织级例外审批、企业 SBOM 平台、持续供应链
监控和法律审查工作流属于 `FUTURE_PRODUCTION`。

## 10. 数据、PDF、模型和素材权利

代码许可证不自动覆盖：

- 数据集；
- 论文全文和 PDF；
- 摘要与数据库内容；
- 模型权重和模型输出条款；
- 字体、图标、图片、模板和截图；
- 商标和品牌资产。

每类材料单独记录来源、权利状态、是否允许处理、是否允许公开展示和是否
允许导出/再分发。许可证未知或受限时，可以只保存引用、哈希、元数据和
获取说明，不把原材料打包进公开 ReproPackage。

## 11. ARS-Codex 专项政策

权威决策见 [ADR-001](../decisions/ADR-001-ARS-CODEX-USAGE.md)，来源事实见
[academic-research-skills-codex.md](../source-research/academic-research-skills-codex.md)。

当前用途状态：

```text
NONCOMMERCIAL_INTENT_DECLARED
```

这不是 `LEGALLY_CONFIRMED_NONCOMMERCIAL`。校赛、奖金、赞助、公开仓库、
下载分发或后续商业化是否满足 CC BY-NC 4.0，需要按实际用途复审。

核验固定 Commit 的实际许可证文本并满足归属条件后，可以：

- 选择性复制 Prompt；
- 复制工作流模板、脚本、测试结构和测试材料；
- Vendor 整体项目；
- Fork 后改造；
- 作为开发期资源；
- 经单独架构决策后成为运行组件。

前置条件：

- 保留 CC BY-NC 4.0 文本和作者/项目归属；
- 记录仓库、Commit、复制路径和修改；
- 与根项目许可证覆盖范围明确隔离；
- 不把上游贡献表述为 RECA 原创；
- 商业化、用途变化或公开产品部署前重新审查；
- 不自动改变单总控 Agent、M8 时序、Service、Approval、Evidence 和 Tool Contract。

截至阶段 11 审查基线，仓库没有复制、Vendor、Fork 或运行时引入任何
ARS-Codex 内容。后续只有在实际纳入 PR 完成路径级许可证、归属、修改和
Notices 记录后，才能改变该事实状态。

## 12. 根许可证

根项目许可证保持：

```text
PENDING_GOVERNANCE_DECISION
```

禁止：

- 根据模板或第三方项目许可证推断 RECA 根许可证；
- 声称仓库已有不存在的 LICENSE；
- 用未来根许可证覆盖第三方文件自身义务；
- 为减少声明而删除第三方许可证或归属。

项目负责人作出决定后，再新增真实 `LICENSE` 并同步 README、Notices、贡献
规则和本文件。

## 13. 最小审查流程

```text
确定复用资产与效果收益
→ 固定仓库和 Commit/Tag
→ 读取实际许可证及特殊文件
→ 选择许可证分类和集成模式
→ 记录复制路径、修改和归属位置
→ 检查 Service/数据/Agent/Adapter 边界
→ 更新 Notices（仅在实际纳入时）
→ 执行与风险相称的测试和发布扫描
```

如果许可证为 `NO_LICENSE_DO_NOT_COPY` 或来源为
`UNKNOWN_SOURCE_DO_NOT_COPY`，流程停止，不得通过改名、AI 改写或拆分文件
绕过。

## 14. 发布检查

Competition Edition 发布前确认：

- 无来源不明或无许可证复制内容；
- 实际纳入项目有固定版本、许可证和归属；
- 特殊许可证内容与自研内容可识别；
- 复制路径和修改记录完整；
- `THIRD_PARTY_NOTICES.md` 描述实际状态；
- 数据、PDF 和素材具有演示/分发权；
- 根许可证仍被准确标记为待决；
- 实际路径相关 Critical 供应链风险已处理；
- M0 required CI 和 infrastructure clean-room 未被规避；
- Future Production 项没有被错误声称为已完成。

阶段 3 将对齐测试、路线图、开发规则和详细契约。本阶段不复制第三方内容、
不新增依赖、不创建 Vendor/Submodule，也不修改 CI。
