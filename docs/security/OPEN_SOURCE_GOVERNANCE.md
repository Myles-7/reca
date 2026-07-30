# Open Source Governance

- 文档名称：Open Source Governance
- 所属入口文档：[SECURITY_AND_OPEN_SOURCE.md](../SECURITY_AND_OPEN_SOURCE.md)
- 文档状态：Conditional Approval
- Migration status: COMPLETE

## 权威范围

本文件是依赖、SBOM、开源目标、根许可证待决状态、第三方使用方式、THIRD_PARTY_NOTICES、Vendor、数据集与 PDF 权利、云服务条款、ARS-Codex 清洁室、贡献、许可证审查、发布清单和第三方材料分类的唯一完整定义。

## 不负责的内容

不负责运行时身份权限、文件解析执行控制或安全事件处置。根许可证选择仍由项目负责人治理决定。

## 返回入口文档

返回 [SECURITY_AND_OPEN_SOURCE.md](../SECURITY_AND_OPEN_SOURCE.md)。

## 已迁入的原章节

- 原第 35-48、50-51、63、67、69-70 章

## 临时状态说明

阶段 9 迁移已完成。本文件与入口文档共同构成安全与开源治理正式开发基准；发生冲突时视为文档缺陷，不得自行猜测、降低安全要求或选择根许可证。

---

## 35. 依赖与供应链治理

### 35.1 依赖来源

依赖必须来自：

* 官方包仓库；
* 官方 GitHub Release；
* 可信镜像；
* 已审查的 Vendor 文件。

不得从不明网盘复制二进制。

### 35.2 依赖锁定

必须锁定：

* Python 依赖；
* Node 依赖；
* Docker 镜像版本；
* GROBID 版本；
* 数据库版本；
* Valkey 版本；
* MinIO 版本。

避免正式版本使用未固定的 `latest`。

### 35.3 哈希和完整性

包管理器支持时启用完整性校验。

### 35.4 新增依赖审查

新增依赖前检查：

1. 是否真的需要；
2. 是否已有依赖可满足；
3. 项目活跃度；
4. 最近发布；
5. 安全记录；
6. 维护者可信度；
7. 许可证；
8. 传递依赖；
9. 包体积；
10. 是否访问网络或执行安装脚本。

### 35.5 安装脚本

Node 等生态中的安装脚本可能执行代码。

新增依赖时应关注：

* `postinstall`；
* 原生二进制；
* 预编译下载；
* 不明安装行为。

### 35.6 依赖扫描

CI 建议执行：

* Python 依赖漏洞扫描；
* npm audit 或等效工具；
* GitHub Dependabot；
* Docker 镜像扫描；
* Secret 扫描。

### 35.7 漏洞处理

#### Critical/High

* 阻止发布；
* 升级、替换或移除；
* 无修复时需书面风险接受和隔离措施。

#### Medium

* 评估是否可利用；
* 登记；
* 设定修复时间。

#### Low

* 可随周期处理。

### 35.8 恶意包与名称混淆

注意：

* Typosquatting；
* 同名不同源；
* 拼写错误包；
* 新发布且无维护记录包。

---

## 36. 软件物料清单

### 36.1 SBOM

发布版本建议生成软件物料清单，至少包含：

* 包名；
* 版本；
* 来源；
* 许可证；
* 直接或传递依赖；
* 哈希；
* 用途。

格式可采用：

* CycloneDX；
* SPDX；
* 或项目自定义清单。

### 36.2 Docker 镜像

记录：

* 镜像名；
* Tag；
* Digest；
* 来源；
* 许可证；
* 用途。

### 36.3 SBOM 更新

依赖变更时更新。

发布包和测试报告应引用对应 SBOM。

---

## 37. 开源治理目标

### 37.1 项目开源原则

RECA 可开源的内容包括：

* 自研业务代码；
* API 契约；
* 数据模型；
* 测试框架；
* 示例数据生成脚本；
* 不含敏感信息的演示项目；
* 复现流程；
* 开源声明。

### 37.2 不应公开

* 用户真实项目；
* 未授权 PDF；
* 未发表论文；
* L3 数据；
* API Key；
* Secret；
* 生产配置；
* 私有备份；
* 供应商受限材料；
* 未获得再分发许可的数据集。

### 37.3 开源不等于数据开放

代码许可证、数据许可证、文献版权和模型条款相互独立。

不能因为代码开源，就自动公开用户数据或论文全文。

---

## 38. RECA 自有许可证

### 38.1 许可证选择原则

RECA 根许可证应考虑：

* 比赛要求；
* 团队开源目标；
* 第三方依赖兼容性；
* 是否允许商业使用；
* 是否要求衍生作品开源；
* 是否需要专利条款；
* 学校知识产权规定。

### 38.2 推荐选项

若学校和比赛无特殊要求，可考虑宽松许可证，例如：

* Apache License 2.0；
* MIT License。

Apache-2.0 具有较明确的专利条款。

最终选择必须经过团队和学校确认。

### 38.3 根许可证范围

根许可证只覆盖团队有权授权的自研代码。

不自动覆盖：

* 第三方代码；
* 数据集；
* PDF；
* 模型；
* 字体；
* 图标；
* 模板；
* Vendor 资源。

### 38.4 文件头

不强制每个源文件都加入长许可证头。当前根项目许可证状态为 `PENDING_GOVERNANCE_DECISION`：仓库没有 `LICENSE`，文档不得声称存在或擅自选择许可证；第三方许可仍由 `THIRD_PARTY_NOTICES.md` 分别记录。项目负责人正式决定后，才可新增真实 `LICENSE` 并更新治理记录、README 和本节。

第三方复制或修改文件需保留原声明。

---

## 39. 第三方许可证分类

### 39.1 宽松许可证

一般较容易使用：

* MIT；
* BSD-2-Clause；
* BSD-3-Clause；
* Apache-2.0；
* ISC。

仍需：

* 保留版权；
* 保留许可证；
* 遵守 NOTICE 要求。

### 39.2 弱 Copyleft

例如：

* LGPL；
* MPL-2.0。

需评估：

* 动态或静态链接方式；
* 是否修改库；
* 修改文件是否需公开；
* 分发义务。

### 39.3 强 Copyleft

例如：

* GPL；
* AGPL。

需重点评估：

* 是否与 RECA 根许可证兼容；
* 是否导致整个组合或网络服务需要开放源代码；
* 比赛提交是否构成分发；
* Docker 服务是否独立交互；
* 是否修改组件。

未经明确审查，不得随意引入核心代码路径。

### 39.4 非商业或研究专用许可证

例如带有：

* Non-Commercial；
* Research Only；
* Academic Use Only；
* No Derivatives。

这些不属于标准开源许可证，可能限制：

* 比赛公开；
* 商业部署；
* 再分发；
* 修改。

必须单独审查。

### 39.5 无许可证项目

公开仓库没有许可证时，默认不认为可复制、修改或分发代码。

可用于阅读和学习思想，但不能直接复制进入仓库。

---

## 40. 第三方项目使用方式

### 40.1 四层使用策略

RECA 对第三方开源能力采用四层策略。

#### 第一层：工程底座复用

例如：

* FastAPI 全栈模板；
* React 生态；
* Docker Compose。

要求：

* 许可证兼容；
* 保留声明；
* 明确修改内容。

#### 第二层：独立服务接入

例如：

* GROBID；
* PostgreSQL；
* MinIO；
* Valkey。

尽量通过网络接口使用，保持组件边界清晰。

#### 第三层：库依赖

例如：

* pandas；
* SciPy；
* statsmodels；
* Matplotlib；
* python-docx；
* pypdf；
* PyAlex。

通过包管理器引入并锁定版本。

#### 第四层：研究思路借鉴

例如参考其他项目的：

* 检索流程；
* 排名融合；
* Agent 编排思想；
* UI 模式。

若不复制代码，只借鉴一般思想，也应避免复制受版权保护的具体实现和文档文本。

### 40.2 不建议整仓复制

除底座模板外，不应将多个大型开源项目直接复制到同一仓库形成难以维护的拼接系统。

### 40.3 Fork

Fork 项目时：

* 保留原许可证；
* 保留历史；
* 说明修改；
* 跟踪上游安全更新；
* 避免删除版权信息。

### 40.4 代码片段

复制第三方代码片段前：

* 检查许可证；
* 检查来源；
* 记录 URL 或 Commit；
* 保留必要声明；
* 写入 `THIRD_PARTY_NOTICES.md`。

### 40.5 AI 生成代码

AI 生成代码仍需：

* Code Review；
* 检查是否与已知第三方代码高度相似；
* 检查许可证风险；
* 不因 AI 生成就跳过开源审查。

---

## 41. 第三方组件治理表

正式发布前维护以下清单：

| 组件                | 用途       | 使用方式 | 许可证           | 是否修改 |  是否分发 | 声明位置                | 风险状态 |
| ----------------- | -------- | ---- | ------------- | ---: | ----: | ------------------- | ---- |
| React             | 前端框架     | 依赖   | 待锁定版本核验       |    否 |     是 | Third Party Notices | 待确认  |
| FastAPI           | API 框架   | 依赖   | 待锁定版本核验       |    否 |     是 | Third Party Notices | 待确认  |
| PostgreSQL        | 数据库      | 独立服务 | 待核验           |    否 |  镜像部署 | Third Party Notices | 待确认  |
| pgvector          | 向量扩展     | 扩展   | 待核验           |    否 |     是 | Third Party Notices | 待确认  |
| MinIO             | 对象存储     | 独立服务 | 必须重点核验当前版本许可证 |    否 | 视部署而定 | Third Party Notices | 重点审查 |
| Valkey            | 队列与缓存    | 独立服务 | 待核验           |    否 |  镜像部署 | Third Party Notices | 待确认  |
| GROBID            | PDF 解析   | 独立服务 | 待核验           |    否 |  镜像部署 | Third Party Notices | 待确认  |
| pandas            | 数据处理     | 依赖   | 待核验           |    否 |     是 | Third Party Notices | 待确认  |
| SciPy             | 统计       | 依赖   | 待核验           |    否 |     是 | Third Party Notices | 待确认  |
| statsmodels       | 统计       | 依赖   | 待核验           |    否 |     是 | Third Party Notices | 待确认  |
| Matplotlib        | 图表       | 依赖   | 待核验           |    否 |     是 | Third Party Notices | 待确认  |
| python-docx       | DOCX     | 依赖   | 待核验           |    否 |     是 | Third Party Notices | 待确认  |
| pypdf             | PDF 回退   | 依赖   | 待核验           |    否 |     是 | Third Party Notices | 待确认  |
| PyAlex            | OpenAlex | 依赖   | 待核验           |    否 |     是 | Third Party Notices | 待确认  |
| OpenAI Agents SDK | Agent 编排 | 依赖   | 必须核验正式版本      |    否 |     是 | Third Party Notices | 待确认  |

许可证不能仅凭记忆填写，发布时必须以所锁定版本的官方许可证文件为准。

---

## 42. `THIRD_PARTY_NOTICES.md`

### 42.1 必须包含

每个需要声明的第三方组件记录：

* 名称；
* 版本；
* 官方项目地址；
* 用途；
* 许可证名称；
* 版权声明；
* 是否修改；
* 原许可证文本位置；
* NOTICE 要求；
* 是否包含在 Docker 镜像；
* 是否存在额外条款。

### 42.2 示例结构

```markdown
### Component Name

- Version: x.y.z
- Purpose: ...
- Source: official project repository
- License: ...
- Usage: dependency / service / modified source
- Modified: No
- License text: vendor/licenses/component-LICENSE.txt
- Notice obligations: ...
```

### 42.3 禁止

不得只写：

> 本项目使用了若干开源项目。

必须可逐项追溯。

---

## 43. Vendor 目录

### 43.1 使用条件

仅在以下情况使用 `vendor/`：

* 需要固定第三方模板；
* 包管理器无法可靠获取；
* 需要保存许可证文本；
* 需要保存 CSL 等静态资源。

### 43.2 目录结构

```text
vendor/
├── licenses/
│   ├── component-a-LICENSE.txt
│   └── component-b-NOTICE.txt
├── csl/
└── README.md
```

### 43.3 Vendor 文件要求

记录：

* 来源；
* 版本；
* 获取日期；
* SHA-256；
* 许可证；
* 是否修改。

### 43.4 禁止 Vendor

不得将未授权论文、模型权重或数据集复制到 Vendor。

---

## 44. 数据集许可证治理

### 44.1 数据身份证

每个 Dataset 必须尽量记录：

* 发布者；
* 来源平台；
* 来源标识；
* DOI；
* 获取日期；
* 许可证；
* 推荐引用；
* 使用限制；
* 再分发限制；
* 已知限制。

### 44.2 许可证状态

* `VERIFIED`；
* `DECLARED_BY_USER`；
* `UNKNOWN`；
* `RESTRICTED`。

### 44.3 UNKNOWN

许可证未知时：

* 允许用户在有权环境中本地分析；
* 显示警告；
* 默认不公开分发；
* 导出就绪检查阻止公开包或要求明确确认。

### 44.4 RESTRICTED

受限数据：

* 限制下载；
* 默认不进入复现包；
* 不作为公开演示附件；
* 只导出分析代码和数据说明时需确认条款。

### 44.5 公开数据不等于无限制

即使无需登录获取，也要检查：

* 许可证；
* 使用条款；
* 引用要求；
* 再分发；
* 商业使用；
* 隐私条件。

### 44.6 示例数据

仓库中的示例数据应：

* 自建；
* 合成；
* 或具有明确开放许可；
* 不含真实敏感信息；
* 有来源清单。

---

## 45. 文献和 PDF 版权治理

### 45.1 元数据

文献题目、作者、年份、DOI 等元数据可通过 Provider 获取，但仍应遵守 Provider 使用政策。

### 45.2 摘要

摘要可能受版权或数据源条款约束。

系统应：

* 用于检索和科研辅助；
* 避免批量公开再分发；
* 记录来源；
* 不将 Provider 数据打包为独立数据库产品。

### 45.3 用户上传 PDF

用户应确认其有权：

* 持有；
* 阅读；
* 上传到当前系统；
* 用于个人或授权科研分析。

### 45.4 RECA 不提供

* 付费墙绕过；
* 未授权全文下载；
* 批量抓取付费数据库；
* 破解文档保护；
* 非法论文共享。

### 45.5 PDF 导出

复现包默认优先包含：

* 文献元数据；
* 引用；
* EvidenceSpan；
* 用户本地文件清单。

是否包含全文 PDF 由权限和许可证决定。

### 45.6 EvidenceSpan

证据片段应保持必要、适度。

公开展示时避免大段复制全文。

---

## 46. 模型、API 和云服务条款

### 46.1 服务条款登记

使用外部模型或 API 前记录：

* 服务条款；
* 数据使用政策；
* 费率；
* 请求限制；
* 禁止用途；
* 数据保留；
* 地区限制；
* 输出权利。

### 46.2 免费额度

免费额度不等于允许无限自动化调用。

必须遵守速率和用途限制。

### 46.3 模型输出权利

模型输出可用性仍需结合：

* 供应商条款；
* 第三方相似性；
* 开源许可证；
* 学术规范。

### 46.4 API 缓存

### 46.5 外部交叉模型与降级

跨 Provider 的交叉模型验证默认关闭。启用时要求用户明确同意本次内容外发，记录 Provider、模型、数据类别、来源 ID、输入哈希、consent record 与保留期限；失败时回退到单模型或人工审核并向用户披露影响。Adapter、模型或 SSE 降级必须记录 primary/fallback、原因码、影响、结果状态和用户可见消息，且不得扩大权限、提高 effective 数据访问等级，或把 `UNAVAILABLE`、缓存、局部文本和 `LOCATION_UNCERTAIN` 伪装为成功。

### 46.6 ARS-Codex 清洁室来源使用

`academic-research-skills-codex` 仅作为研究与测试设计参考。固定提交、许可证、审阅日期、复制内容为 none 的台账见 `docs/source-research/academic-research-skills-codex.md`；采用决定见 `docs/decisions/ADR-001-ARS-CODEX-USAGE.md`。上游 CC BY-NC 4.0 不构成 RECA 运行时依赖或根项目许可证；RECA 不复制其 Prompt、代码、脚本或测试材料，任何将来的复制都必须先更新第三方登记和许可证审查。

缓存 Provider 数据前检查服务条款。

缓存应记录：

* 来源；
* 获取时间；
* 是否实时；
* 数据版本。

---

## 47. 字体、图标和视觉资源

### 47.1 字体

若打包字体，必须检查：

* 是否允许嵌入；
* 是否允许再分发；
* 是否允许 Web 使用；
* 是否要求声明。

优先使用系统字体或明确开放字体。

### 47.2 图标

使用图标库时记录许可证。

### 47.3 模板

演示模板、PPT、图片和 UI 素材也可能有版权。

不得从网络随意复制进入开源仓库。

### 47.4 论文截图

公开 README 中展示论文页面时，应注意版权和隐私。

可使用：

* 自建示例；
* 开放许可论文；
* 小范围合理展示；
* 经过模糊或替换的演示素材。

---

## 48. 开源贡献治理

### 48.1 Contributor 要求

外部贡献者提交代码时，应确认：

* 有权提交；
* 在项目负责人作出根许可证决定后，代码符合该项目许可证；
* 未包含第三方未授权代码；
* 未包含秘密；
* 未包含真实用户数据。

### 48.2 CLA 或 DCO

P0 可根据团队规模选择：

* Developer Certificate of Origin；
* Contributor License Agreement；
* 或 Pull Request 声明确认。

### 48.3 Pull Request 检查

PR 模板应包含：

* 新增依赖；
* 许可证；
* 数据文件来源；
* 是否包含模型输出；
* 是否涉及安全边界；
* 是否涉及敏感数据；
* 是否更新 Third Party Notices。

### 48.4 外部 Issue

用户报告安全问题时，不应要求在公开 Issue 中披露敏感细节。

仓库应提供私下安全联系渠道。

---

## 50. 许可证审查流程

### 50.1 新依赖流程

```text
提出依赖
→ 确认必要性
→ 查询官方许可证
→ 检查版本
→ 检查传递依赖
→ 判断使用方式
→ 判断分发方式
→ 记录义务
→ 安全审查
→ 批准
→ 锁定版本
→ 更新 Notices 和 SBOM
```

### 50.2 审查记录

建议维护：

```text
docs/open_source/DEPENDENCY_REVIEW.md
```

字段：

* 组件；
* 版本；
* 申请人；
* 用途；
* 替代方案；
* 许可证；
* 兼容结论；
* 安全状态；
* 审批人；
* 日期。

### 50.3 许可证变化

组件升级时重新检查许可证。

不能假设同一项目所有版本许可证相同。

### 50.4 Docker 镜像

镜像可能包含多个系统包和依赖。

不仅审查镜像顶部项目许可证，还要关注：

* 基础镜像；
* 操作系统包；
* 附带模型；
* 附带字体；
* 附带二进制。

---

## 51. 开源发布清单

### 51.1 代码

* [ ] 自研代码可授权；
* [ ] 无未授权复制代码；
* [ ] 无真实用户数据；
* [ ] 无未公开论文；
* [ ] 无生产配置；
* [ ] 无密钥；
* [ ] 无数据库备份；
* [ ] 无对象存储导出。

### 51.2 许可证

* [ ] 根 `LICENSE` 已确认；
* [ ] `THIRD_PARTY_NOTICES.md` 完整；
* [ ] Vendor 许可证文本完整；
* [ ] 所有直接依赖许可证已记录；
* [ ] 强 Copyleft 已专项审查；
* [ ] 无许可证组件未被复制；
* [ ] 数据许可证已区分。

### 51.3 文档

* [ ] README 说明数据与模型边界；
* [ ] SECURITY.md；
* [ ] 贡献指南；
* [ ] 已知限制；
* [ ] 第三方声明；
* [ ] 演示数据来源；
* [ ] 隐私说明。

### 51.4 安全

* [ ] Secret 扫描通过；
* [ ] Git 历史检查；
* [ ] 依赖漏洞检查；
* [ ] Docker 镜像检查；
* [ ] 测试文件无敏感数据；
* [ ] 示例 `.env` 无真实密钥。

---

## 63. 推荐仓库安全文件（目标结构）

```text
reca/
├── LICENSE                    # 仅在根许可证决定后创建
├── SECURITY.md
├── THIRD_PARTY_NOTICES.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── .gitignore
├── .env.example
├── docs/
│   ├── SECURITY_AND_OPEN_SOURCE.md
│   └── open_source/
│       ├── DEPENDENCY_REVIEW.md
│       ├── DATASET_LICENSES.md
│       └── SBOM.md
├── vendor/
│   └── licenses/
└── scripts/
    ├── scan_secrets.sh
    ├── scan_dependencies.sh
    ├── generate_sbom.sh
    └── verify_third_party_notices.sh
```

---

## 67. 附录 C：开源依赖审查模板

```markdown
### Dependency Review

- Component:
- Requested version:
- Requester:
- Purpose:
- Direct or transitive:
- Runtime or development-only:
- Source repository:
- Official package:
- License:
- License verified from:
- Copyright notice:
- Copyleft obligations:
- Notice obligations:
- Modified source:
- Distributed with RECA:
- Docker image included:
- Known vulnerabilities:
- Maintenance status:
- Alternative considered:
- Security conclusion:
- License conclusion:
- Approved by:
- Review date:
```

---

## 69. 附录 E：第三方材料分类

| 材料              | 是否可直接放公开仓库 | 处理方式         |
| --------------- | ---------: | ------------ |
| 自研代码            |          是 | 使用根许可证       |
| MIT/Apache 依赖源码 |        视需要 | 保留许可证与声明     |
| 包管理器依赖          |          是 | 锁版本、记录许可证    |
| GPL/AGPL 组件     |      需专项审查 | 明确组合与分发影响    |
| 无许可证 GitHub 代码  |          否 | 不复制，仅学习思想    |
| 公开论文元数据         |        通常可 | 记录来源和服务条款    |
| 付费论文 PDF        |          否 | 用户本地使用，不公开分发 |
| 开放许可论文 PDF      |        按许可 | 保留作者和许可证     |
| 公开数据集           |       按许可证 | 记录引用和再分发条款   |
| 许可证未知数据         |        默认否 | 不公开打包        |
| 合成数据            |          是 | 标记为合成        |
| 真实学生敏感数据        |          否 | 不进入公开仓库      |
| 模型 API Key      |        永远否 | Secret 管理    |
| 模型响应快照          |        视内容 | 脱敏并检查条款      |
| 字体              |      按字体许可 | 保存声明         |
| 网络图片            |        默认否 | 使用自制或开放许可资源  |

---

## 70. 最终安全与开源结论

RECA 0.1 的安全和开源治理必须围绕以下底线建立：

```text
用户身份可信
→ 项目权限明确
→ 文件输入不可信
→ 原始文件不可变
→ 敏感数据最小使用
→ 模型不能成为安全边界
→ Agent 只能调用白名单工具
→ 高风险操作必须审批
→ 统计结果不得被模型修改
→ 日志和导出不得泄露秘密
→ 第三方代码必须审查许可证
→ 数据和论文必须分别确认使用权
→ 所有关键行为可以审计
```

RECA 0.1 发布前必须证明：

1. 未授权用户不能访问他人项目；
2. 知道 UUID 不能绕过权限；
3. 上传文件不能影响宿主机路径；
4. PDF、DOCX 和数据文件不会被执行；
5. 原始文件和原始数据版本不会被覆盖；
6. 敏感字段默认不会发送给模型；
7. Agent 不能执行 Shell、任意 Python 或任意 SQL；
8. Agent 不能批准自己的建议；
9. 未批准的数据处理和分析不能运行；
10. AnalysisResult 不允许被模型或普通 API 修改；
11. 日志、导出包和公开仓库中不存在有效密钥；
12. 复现包不会混入其他项目数据；
13. 第三方依赖版本、许可证和安全状态可追溯；
14. 未授权论文全文和受限数据不会进入公开仓库；
15. Security Blocker 和 Security Critical 均为 0。

最终安全门禁为：

```text
Security Blocker = 0
Security Critical = 0
跨项目访问成功次数 = 0
原始文件覆盖次数 = 0
未批准科研操作执行次数 = 0
Agent 任意代码执行能力 = 0
有效密钥公开数量 = 0
L3 数据默认外发次数 = 0
未审查直接依赖数量 = 0
未授权材料公开分发数量 = 0
```

只有满足上述要求，RECA 才能以可信、可复核、可复现和可合法分发的科研智能体项目进入比赛发布和开源阶段。

---
