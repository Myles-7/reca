# M0 Regression Baseline

- 文档名称：M0 Regression Baseline
- 所属入口文档：[TEST_AND_ACCEPTANCE.md](../TEST_AND_ACCEPTANCE.md)
- 文档状态：Conditional Approval
- Migration status: COMPLETE

## 权威范围

本文件是 M0 回归基线的唯一完整定义：六项 required CI、clean-room 验收合同、两个已知 LOW 风险，以及 M1-M9 不得退化的规则。

## 不负责的内容

不负责后续里程碑新增功能的测试指标、产品范围或实现细节；这些内容由入口、其他测试子文档和路线图负责。

## 返回入口文档

返回 [TEST_AND_ACCEPTANCE.md](../TEST_AND_ACCEPTANCE.md)。

## 已迁入的原章节

- 原 4.8 M0 Regression Baseline
- M0 clean-room 验收合同与已知 LOW 风险

## 临时状态说明

阶段 8 迁移已完成。本文件与入口文档共同构成测试与验收正式开发基准；发生冲突时视为文档缺陷，不得自行猜测或降低标准。

---

## M0 已验收基线

```text
commit: 79825914c7c975e8be256a5a89abe812f486769e
tag: m0-complete
M1 Entry Decision: ALLOWED
```

## 六项 required CI

| Job | 基线职责 |
| --- | --- |
| `backend-quality` | Ruff、mypy 与后端测试 |
| `frontend-quality` | Bun、格式、lint、生成 client 一致性、build 与前端 smoke |
| `migration-test` | PostgreSQL 空库迁移、重复迁移和 pgvector |
| `compose-smoke` | Compose、健康 API、Worker 与基础依赖 |
| `security-supply-chain` | Secret、依赖和 workflow 安全 |
| `e2e-smoke` | 浏览器 shell 与真实 API 边界 |

不得使用 `continue-on-error`、`|| true`、删除测试、扩大 ignore、降低阈值或伪造报告取得绿色状态。

## Clean-room 验收合同

涉及 Compose、迁移、Settings/Secret、Celery/Valkey/Worker、MinIO/GROBID、OpenAPI generated/adapter、安全供应链或验收脚本的变化，必须运行：

```powershell
./scripts/m0-acceptance.ps1
```

或：

```bash
./scripts/m0-acceptance.sh
```

clean-room 必须验证：

- 使用隔离的 Compose project；
- 使用随机临时 Secrets，不读取开发者 `.env`；
- PostgreSQL 空库迁移和重复迁移；
- pgvector 可用；
- Worker ping、`health_ping`、任务注册和重启；
- private MinIO 读写、匿名访问拒绝和重启持久性；
- API `live`、`ready`、`dependencies` 和 API 重启；
- generated client 与 OpenAPI 一致；
- Secret 扫描和供应链检查；
- scoped cleanup，不删除默认卷或无关 Docker 资源；
- 最终退出码与验收证据一致。

## 已知非阻断 LOW 风险

- `M0-ISSUE-0006`：Babel 7 LOW advisory。等待兼容升级，不隐藏 audit。
- `M0-ISSUE-0009`：Windows 默认 Playwright 入口 LOW。当前验证入口为 `bun run --cwd frontend test:shell`。

风险未解决前必须继续出现在里程碑和发布报告中。

## M1-M9 不退化规则

M1-M9 的新增测试是叠加关系，不得替换、删除或降低本基线。任何 required CI、clean-room 检查或 LOW 风险披露退化都阻止里程碑 Exit 和发布。

新的 Competition Edition 安全分层不改变上述要求。`M0-ISSUE-0006` 和 `M0-ISSUE-0009` 仍是已披露、非阻断 LOW 风险；“非阻断”不允许删除披露，“继续披露”也不把 LOW 本身升级为校赛发布阻断项。

## 原章节保留

### 4.8 M0 Regression Baseline

M1—M9 的每个 PR 都必须继续通过以下 required CI jobs：`backend-quality`、`frontend-quality`、`migration-test`、`compose-smoke`、`security-supply-chain`、`e2e-smoke`。不得以 `continue-on-error`、`|| true`、忽略文件、删除测试或降低门槛获得绿色。

涉及基础设施、迁移、客户端生成、配置、安全或 Compose 的变更必须运行 clean-room：隔离 Compose、随机临时 Secret、空库和重复迁移、pgvector、Worker ping/`health_ping`/重启、MinIO 私有读写及匿名拒绝、live/ready/dependencies、API 重启、generated client 一致性、Secret 扫描和 scoped cleanup。新增业务迁移必须在此空库/重复迁移基线上继续通过。

M0 的已知非阻断风险为 `M0-ISSUE-0006`（Babel 7 LOW advisory）与 `M0-ISSUE-0009`（Windows 默认 Playwright 入口 LOW）；必须保留记录并使用经过验证的平台安全命令，不能把风险伪装为零。

---
