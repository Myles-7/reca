# Test, Git, and Delivery Rules

- 文档名称：Test, Git, and Delivery Rules
- 所属入口文档：[AGENTS.md](../../AGENTS.md)
- 文档状态：APPROVED FOR M1 DEVELOPMENT
- Migration status: COMPLETE

## 权威范围

本文件详细规定测试执行、M0 回归、clean-room、Git、Commit、PR、文档验证和交付报告。

## 不负责的内容

测试指标与验收阈值仍以 `docs/TEST_AND_ACCEPTANCE.md` 为准；产品和技术语义由其权威文档决定。

## 1. M0 regression baseline

以下 required CI 不可删除或降级：

| Job | 目的 |
| --- | --- |
| `backend-quality` | Ruff、mypy、后端测试 |
| `frontend-quality` | Bun、格式、lint、生成 client、build |
| `migration-test` | PostgreSQL、空库与重复迁移、pgvector |
| `compose-smoke` | Compose、健康、Worker、基础服务 |
| `security-supply-chain` | Secret、依赖和 workflow 安全 |
| `e2e-smoke` | 浏览器 shell 与真实 API 边界 |

不得使用 `continue-on-error`、`|| true`、无理由 ignore、删除断言或降低阈值掩盖失败。

## 2. 当前命令

后端：

```bash
uv run ruff format --check backend
uv run ruff check backend
uv run mypy backend/app
uv run pytest backend/tests -m no_database
```

前端：

```bash
bun run --cwd frontend format:check
bun run --cwd frontend lint
bun run --cwd frontend generate-client
bun run --cwd frontend check-generated-client
bun run --cwd frontend build
bun run --cwd frontend test:shell
```

迁移：

```bash
uv run alembic upgrade head
uv run alembic upgrade head
```

Celery smoke：

```bash
docker compose exec -T worker celery -A app.core.celery:celery_app inspect ping
```

文档：

```bash
git diff --check
git diff --name-only
```

禁止新增或引用不存在的初始化数据脚本来伪造演示或验收数据。

## 3. Clean-room 触发规则

以下变化必须运行 `scripts/m0-acceptance.ps1` 或 `.sh`：

- Compose、镜像、网络、卷或健康检查；
- Settings、环境变量、Secret 或 CORS；
- Alembic 迁移、PostgreSQL 或 pgvector；
- Celery、Valkey、Worker、任务注册或重试；
- MinIO、GROBID 或外部依赖启动边界；
- OpenAPI 生成器、generated client 或 adapter；
- 安全扫描、依赖、workflow 或验收脚本。

clean-room 必须验证：

- 隔离 project 和临时随机 Secret；
- 空库和重复迁移；
- pgvector smoke；
- API live、ready、dependencies；
- Worker ping、registered task、`reca.health_ping` 和重启；
- MinIO 私有读写、匿名拒绝和重启持久性；
- generated client 一致性；
- 浏览器 shell；
- Secret 和依赖扫描；
- scoped cleanup；
- 最终 exit code 与证据文件。

不得读取开发者 `.env`，不得清理默认项目卷或无关 Docker 资源。

## 4. 已知 LOW 风险

- `M0-ISSUE-0006`：Babel 7 LOW advisory。等待兼容升级，不隐藏 audit。
- `M0-ISSUE-0009`：Windows 默认 Playwright 入口 LOW。使用 `bun run --cwd frontend test:shell`。

风险未解决前必须继续出现在报告中。

这两个 LOW 风险是披露项而非 Competition Edition 发布阻断项。供应链必须阻断 Secret 泄露、无许可证或来源不明复制、缺少强制归属以及与实际执行路径相关的可达 Critical 风险；与主演示无关的 MEDIUM、缺少完整 SBOM 或企业安全平台应记录为警告或未来生产强化。

## 5. 测试选择

开源集成任务必须执行并报告：读取研究记录、核验 pinned Commit/Tag、核验实际许可证、最小 Spike、与回退比较、边界决定、实现、上游改造测试、归属更新和限制记录。任何一步 `NOT RUN` 都要说明原因，不能用上游 CI 徽章或研究报告替代本仓库验证。

实际引入项目的最低验收维度为：Pinned version、License and attribution、Compatibility、Main demo effect、Failure behavior、Resource usage、Offline/Recorded behavior、Output schema conversion、Project isolation 和 Reproducibility。

- 文档改动：链接、路径、命令、稳定 ID、状态和 diff；
- 纯函数：单元测试；
- Service：权限、状态、幂等、事务和失败路径；
- 数据库：约束、迁移、并发和隔离；
- API：Schema、错误、权限和 OpenAPI；
- Adapter：正常、超时、不可用、无效响应和降级；
- 前端：状态、错误、权限、生成 client 和关键用户流；
- Agent：路由、Schema、来源、注入、Tool、审批和循环限制；
- 缺陷修复：必须增加回归测试。

Mock 可以用于局部单元测试，不能替代真实迁移、真实确定性统计基准、关键文件流、权限隔离和发布验收。

## 6. 测试结果报告

每条报告包含：

- 实际命令；
- PASS、FAIL 或 NOT RUN；
- 关键数量或失败原因；
- 是否使用 mock、缓存、离线快照或预处理结果；
- 剩余风险和未覆盖范围。

不得声称未运行的测试通过，也不得只写“测试正常”。

## 7. Git 工作规则

- 开始和结束都检查 `git status --short`；
- 保留用户和其他任务已有修改；
- 不使用 `git reset --hard`；
- 不破坏性 checkout 文件；
- 不 force push，除非用户明确授权；
- 不提交运行数据、Secret、临时证据或无关生成物；
- 锁文件只在依赖实际变化时更新；
- generated 文件只由正式生成流程更新；
- Commit 聚焦单一任务；
- 不虚构 Commit、tag、PR 或 CI 状态。

工作树已有重叠修改时，可以完成任务但不应把无法分离的用户修改混入 commit。交付中说明未提交原因。

## 8. Commit 与分支

- 从路线图要求的基线分支开始；
- M1 不继续使用 `codex/m0-continuous`；
- 分支名表达任务或里程碑；
- 提交信息使用祈使式、范围清晰；
- 提交前运行适用验证；
- 只暂存当前任务文件或可明确归属的 hunks；
- tag 和历史修改必须有明确授权。

## 9. Pull Request

PR 至少说明：

```text
Summary
Motivation
Scope
Data Model Changes
API Changes
Security Impact
Tests
Known Limitations
Third-Party Changes
```

没有变化的栏目可以写“None”，不能删除对安全、测试或第三方影响的审查。

## 10. 文档验证

文档变更至少检查：

- 相对链接存在；
- 不出现本机绝对路径；
- Bun、Celery、Alembic、Compose 命令准确；
- M0 commit、tag、CI、LOW 风险和 M1 决定准确；
- 根许可证仍为 `PENDING_GOVERNANCE_DECISION`；
- 需求 ID、API Path、Error Code、Schema、Tool、Enum、Milestone 未意外变化；
- 归档明确非权威；
- `git diff --check` 通过。

## 11. 交付前检查

- 所有请求项有对应实现或明确未决项；
- 验证与风险相称；
- 失败没有被隐藏；
- Git 差异无越界文件；
- 用户已有修改未回滚；
- 文档与实现事实一致；
- 交付回复包含关键结果、限制和 commit 状态。

## 返回入口文档

返回 [AGENTS.md](../../AGENTS.md)。
