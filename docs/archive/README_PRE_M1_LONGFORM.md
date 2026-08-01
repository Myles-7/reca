# README Pre-M1 Longform Archive

> 非权威历史材料。不得作为 RECA 0.1 或后续版本的开发、验收或许可证依据。

## 文档信息

| 项目 | 内容 |
| --- | --- |
| 来源 | 阶段 2 压缩前的 `README.md` |
| 原始规模 | 2186 行 |
| 归档日期 | 2026-07-30 |
| 文档状态 | Historical / Non-authoritative |
| 当前入口 | [README.md](../../README.md) |

## 归档边界

阶段 2 前的 README 同时承担产品愿景、P0 详细功能、架构、数据、测试、安全、路线图和 M0 运行记录，已经与正式权威文档形成大量重复。

本归档只保留旧 README 中具有独立历史意义的展示构想和归档政策。下列重复内容没有再次复制到本文件：

- 完整 P0 功能逐项描述；
- 完整数据模型和技术栈说明；
- 完整安全、测试和开源治理规则；
- 已由 M0 报告保存的工程交付历史；
- 已由 PRD、Architecture、Security、Test 或 Roadmap 权威定义的内容。

## 早期比赛演示构想

阶段 2 前 README 设想使用同一案例贯穿比赛展示：

> 生成式 AI 使用与师范生学习投入之间的关系。

当时列出的演示材料包括：

- 10 篇左右真实论文；
- 已核验文献元数据；
- 合法获取的论文全文；
- 一份来源和许可明确的教育数据；
- 一份包含测试错误的 DOCX；
- 预生成文献矩阵和 Embedding；
- 完整数据版本、分析结果、证据链和复现包。

早期构想将下列步骤列为现场优先实时执行：

- 一次研究问题解析；
- 一篇 PDF 抽取；
- 一次数据质量检查；
- 一次真实统计分析；
- 一次论文检查。

批量 PDF、全部 Embedding、多篇文献矩阵、完整证据关系、图表和复现包可以预处理，但必须明确标记“已预处理”。当时提出的演示保障为云端部署、本地 Docker 和完整录屏。

以上内容只记录早期比赛叙事，不锁定当前演示案例、数据许可、实时步骤或 M9 验收范围。当前决定以正式 PRD、测试文档、安全文档和路线图为准。

## 早期历史文档政策

旧 README 已明确：`docs/archive/` 用于保存早期分析和完整愿景，材料只用于追溯设计过程，不能覆盖当前正式文档，也不应被 Codex 当作同等优先级需求。

阶段 2 将该原则收敛为：

1. `docs/archive/` 中的材料全部非权威；
2. 正式开发必须先读取根 `AGENTS.md` 和对应领域入口文档；
3. 历史材料与正式文档冲突时，不得自行选择历史版本；
4. 需要恢复历史决定时，应查阅 Git、正式报告和 ADR，而不是复制旧 README 的重复规范。

## 正式替代来源

- 项目入口：[README.md](../../README.md)
- 开发规则：[AGENTS.md](../../AGENTS.md)
- 产品需求：[PRODUCT_REQUIREMENTS.md](../PRODUCT_REQUIREMENTS.md)
- 架构：[ARCHITECTURE.md](../ARCHITECTURE.md)
- 数据模型：[DATA_MODEL_AND_WORKFLOW.md](../DATA_MODEL_AND_WORKFLOW.md)
- 契约：[API_AI_TOOL_CONTRACTS.md](../API_AI_TOOL_CONTRACTS.md)
- 测试：[TEST_AND_ACCEPTANCE.md](../TEST_AND_ACCEPTANCE.md)
- 安全与开源：[SECURITY_AND_OPEN_SOURCE.md](../SECURITY_AND_OPEN_SOURCE.md)
- 路线图：[IMPLEMENTATION_ROADMAP.md](../IMPLEMENTATION_ROADMAP.md)
- M0 历史：[M0_DEVELOPMENT_SUMMARY.md](../reports/M0_DEVELOPMENT_SUMMARY.md)
