# Operations, Data, and Incidents

- 文档名称：Operations, Data, and Incidents
- 文档版本：1.1.0
- 所属入口文档：[SECURITY_AND_OPEN_SOURCE.md](../SECURITY_AND_OPEN_SOURCE.md)
- 文档状态：Conditional Approval
- 最后更新时间：2026-07-31
- Migration status: COMPLETE

## 变更记录

| 版本 | 日期 | 状态 | 变更说明 |
| --- | --- | --- | --- |
| 1.0.0 | 2026-07-31 | Conditional Approval | 文档拆分后的数据、备份、事件和演示运维基线 |
| 1.1.0 | 2026-07-31 | Conditional Approval | 聚焦 Competition Edition 恢复与降级，将企业运维移至未来生产 |

## 权威范围

本文件是 Competition Edition 的演示数据恢复、异步任务、外部服务降级、
本地备份、简化事件处理、演示环境和未来生产运维分类的唯一完整定义。

不负责认证实现、文件/模型/Agent 专项控制或第三方许可证分类。返回
[安全与开源治理入口](../SECURITY_AND_OPEN_SOURCE.md)。

## 1. Competition Edition 运维目标

RECA 0.1 不承诺企业可用性。运维目标是：

1. 主演示数据可以恢复或重复初始化；
2. Worker 或外部服务失败不破坏原始输入；
3. 失败、缓存和降级对用户可见；
4. 临时演示密钥可以撤销或更换；
5. 演示失败后可以回到已知正常状态；
6. 正式科研结果不会因重试或恢复被静默改写。

## 2. Competition Edition 必须保留

### 2.1 演示数据可恢复

- 主演示项目必须有本地备份、可重复初始化脚本或可验证的导入包之一；
- 恢复方式必须在比赛前实际执行一次；
- 恢复不能依赖未记录的个人机器状态；
- 恢复后能确认核心 Artifact、版本、审批、分析结果和证据关系；
- 若使用初始化数据，不得虚构真实来源或许可证。

本阶段不新增 seed 脚本；这里定义的是后续实现要求。

### 2.2 已知正常状态

演示前记录：

- Git Commit；
- Compose/服务版本；
- 数据库迁移状态；
- 主演示项目或导入包版本；
- 必要的本地模型/缓存状态；
- 临时演示凭据的撤销方式；
- 在线服务不可用时的离线路径。

演示失败时可以停止当前任务，恢复该状态，再重新开始。不得为了继续演示
而把失败任务或不完整结果手工标为成功。

### 2.3 外部服务降级

OpenAlex、GROBID、模型 Provider 或其他远程依赖失败时：

- 使用缓存、Recorded、离线或本地替代时明确标记来源；
- 记录 primary、fallback、原因、影响和结果状态；
- 不扩大权限或 `effective_data_access_level`；
- 不把局部文本、旧缓存、`UNAVAILABLE` 或 `LOCATION_UNCERTAIN` 显示为完整成功；
- 无可靠替代时停止相关正式流程并给出可执行的人工路径。

失败被标记为正式成功属于 `RELEASE_BLOCKER`。

### 2.4 Worker 安全恢复

- Job 参数使用对象 ID、版本和受控选项，不携带 Secret 或整份敏感文件；
- Worker 从授权 Service/Repository 读取需要的数据；
- 任务有超时、有限重试、取消和明确状态；
- 重试幂等或由唯一键防止重复正式版本；
- Worker 失败不删除、覆盖或污染原始输入；
- 部分输出不能自动升级为正式结果；
- 恢复或重试保留原 Job/ProcessingRun 关系和错误原因。

### 2.5 临时密钥

比赛和共享校内环境使用的临时 Token、API Key 或演示密码必须：

- 不进入仓库、前端包、截图或普通日志；
- 有明确所有者和用途；
- 可在泄露或演示结束后撤销/更换；
- 不与个人长期高权限密钥共用；
- 不打包进 ReproPackage 或公开演示材料。

## 3. Competition Recommended

以下措施提升演示可靠性，但不构成校赛发布阻断：

### 3.1 简单数据库导出

建议在重要演示前导出主项目所需的 PostgreSQL 数据或使用受控项目导出包。
备份文件应限制访问，不提交到公开仓库。

### 3.2 MinIO 演示文件副本

建议保留主演示所需 PDF、数据、DOCX 和导出物的本地受控副本，并校验
哈希。副本仍受原许可证和敏感数据限制。

### 3.3 容器资源限制

建议为解析器、Worker、GROBID 和模型辅助任务配置合理的内存、CPU、超时
和并发上限，避免单个任务拖垮演示机器。

### 3.4 基础服务状态检查

建议检查 API、数据库、Valkey、Worker、MinIO 和 GROBID 的健康状态。健康
检查只说明服务可达，不得描述为科研业务能力已完成。

### 3.5 简单日志保留

建议保留比赛前后必要的请求 ID、Job 状态、错误码和降级记录，避免保存
完整敏感请求、Prompt 或文件内容。

## 4. 数据分类与演示材料

Competition Edition 使用轻量分类：

| 类别 | 示例 | 演示处理 |
| --- | --- | --- |
| `PUBLIC_OR_LICENSED` | 开放元数据、明确许可数据、公开成果 | 可按许可证使用和展示 |
| `PROJECT_PRIVATE` | 未公开研究问题、私有 PDF、论文草稿 | 仅授权项目和必要模型范围 |
| `SENSITIVE_OR_RESTRICTED` | 身份、成绩、健康、受限数据、不可再分发材料 | 默认不进入公开演示或外部模型 |
| `SECRET` | Token、密码、连接串、密钥 | 永不进入模型、前端包、导出和普通日志 |

完整法规分类、DLP 和数据驻留属于 `FUTURE_PRODUCTION`。

演示材料必须满足：

- 使用合成、公开或获得许可的数据；
- 不展示真实 Secret、私人邮箱、数据库控制台或可复用签名 URL；
- 不公开未获授权的论文全文、敏感数据或其他项目内容；
- 录屏和截图在发布前复查；
- 数据和 PDF 的再分发权与代码许可证分开判断。

无权使用的敏感或受限材料进入演示属于 `RELEASE_BLOCKER`。

## 5. 简化事件流程

Competition Edition 使用以下流程：

```text
停止受影响服务
→ 保存必要日志
→ 撤销或更换泄露密钥
→ 恢复已知正常版本
→ 记录原因与修复
```

### 5.1 触发事件

至少包括：

- Secret、Token 或密码泄露；
- 跨项目数据访问；
- 原始文件被覆盖或正式结果被错误修改；
- Agent 越权或任意代码执行；
- 恶意文件影响宿主机路径或服务；
- 无许可内容进入仓库或公开演示；
- 关键外部失败被误标为成功。

### 5.2 最小记录

```text
detected_at
affected_service_or_project
summary
data_or_secret_involved
immediate_containment
credential_action
known_good_version
root_cause
fix
regression_check
owner
status
```

只保存定位和恢复所需信息，不把完整 Secret 或敏感数据复制进事件记录。

### 5.3 Git 中的 Secret

如果 Secret 进入 Git：

1. 立即撤销或更换；
2. 停止继续使用该凭据；
3. 评估是否已经推送或发布；
4. 必要时按明确范围清理历史；
5. 增加扫描或回归检查；
6. 不把“删除当前文件”当作凭据已安全。

历史重写属于高风险操作，必须明确范围和恢复方案。

## 6. 本地备份与恢复

### 6.1 Competition Required

- 主演示项目有一种可用恢复来源；
- 原始输入可通过哈希确认；
- 恢复不覆盖唯一原件；
- 恢复后的正式结果仍指向正确输入版本；
- 备份和演示导出不含 Secret；
- 许可证或敏感限制随材料一起保留。

### 6.2 Competition Recommended

- 比赛前数据库导出；
- 主演示 MinIO 对象副本；
- 恢复步骤清单；
- 至少一次人工恢复演练；
- 简单备份日期和内容记录。

## 7. Future Production

以下要求不阻塞 RECA 0.1 校赛版，统一移到未来公开/商业部署：

- 正式 RPO/RTO；
- 异地备份和多区域恢复；
- 自动故障转移；
- 正式事件指挥体系和 24x7 值守；
- 法律通知、监管报告和对外披露流程；
- 长期安全档案与取证保全组织；
- 企业监控中心、SIEM 和持续告警；
- 企业 Secret Manager 和自动密钥轮换；
- 完整数据保留、删除传播和法律请求政策；
- 多地区数据驻留与合规证明；
- 正式备份加密、访问复核和周期性灾备演练。

一旦 RECA 转向公开产品、商业 SaaS、大规模共享或承载高风险真实数据，
必须重新激活并细化本节，不能继续沿用 `DEMO_LOCAL` 假设。

## 8. 缺陷和发布判断

Competition Edition 使用入口文档定义的 `RELEASE_BLOCKER`。普通缺陷按
影响处理：

- 与实际执行路径相关的可利用 Critical 供应链风险阻断；
- Medium/Low 漏洞记录并按演示暴露面安排修复，不自动阻断；
- 缺少企业 SBOM、灾备、事件组织或长期归档不阻断；
- 任何科研真实性、原始不可变、Secret、路径执行、许可证或失败伪装问题
  仍按入口硬护栏处理。

## 9. M0 基线保护

六项 required CI 和 infrastructure clean-room acceptance 继续保持：

```text
backend-quality
frontend-quality
migration-test
compose-smoke
security-supply-chain
e2e-smoke
```

不得通过 `continue-on-error`、删除测试、降低阈值、跳过 Secret/依赖扫描或
伪造报告获得绿色。这里的 clean-room 是隔离 Compose、临时 Secret、空库
迁移和 scoped cleanup 的验收合同，与第三方开源
`CLEAN_ROOM_REIMPLEMENTATION` 无关。

## 10. Competition Edition 完成定义

- 主演示项目可恢复或可重复初始化；
- 外部服务失败有可见降级；
- Worker 失败不破坏原始输入；
- 临时密钥可撤销且不在仓库/前端/日志；
- 演示数据和材料有权使用；
- 失败后能恢复已知正常状态；
- 六项 M0 required CI 和 infrastructure clean-room 未被规避；
- Future Production 项未被错误描述为 Competition Edition 已实现。

本阶段不修改实际运维脚本、Compose、CI、备份实现或测试门禁。阶段 3 负责
同步详细验收文档。
