# 研证链 AI（RECA）

> 面向高校科研训练的全流程可信科研工作台。
> Research Evidence Chain Agent

RECA 将研究问题、真实文献、原文证据、数据版本、确定性分析、图表、论文论述、人工确认和复现材料连接为可追溯的科研证据链。

## 文档信息

| 项目 | 内容 |
| --- | --- |
| 文档名称 | `README.md` |
| 文档角色 | 项目总入口 |
| 文档状态 | Conditional Approval |
| 当前产品版本 | RECA 0.1 Competition Edition |
| 当前工程阶段 | M0 COMPLETED；M1 Entry `ALLOWED` |
| 最后更新 | 2026-07-30 |

本文件只负责项目定位、当前工程事实、启动入口和正式文档导航。业务需求、架构、数据模型、契约、测试、安全和实施顺序以各自权威文档为准。

## 文档组成

本入口文档与其列出的子文档共同构成本领域的正式开发基准。
入口文档负责核心决策、红线和索引，子文档负责详细规范。
两者发生冲突属于文档缺陷，开发者和 Codex 不得自行猜测。

| 入口文档 | 权威范围 |
| --- | --- |
| [README.md](./README.md) | 项目入口、当前工程状态和启动导航 |
| [AGENTS.md](./AGENTS.md) | Codex 与仓库级开发规则 |
| [PRODUCT_REQUIREMENTS.md](./docs/PRODUCT_REQUIREMENTS.md) | 产品范围和需求 ID |
| [ARCHITECTURE.md](./docs/ARCHITECTURE.md) | 系统架构、模块边界和技术决策 |
| [DATA_MODEL_AND_WORKFLOW.md](./docs/DATA_MODEL_AND_WORKFLOW.md) | 领域对象、状态机、版本和约束 |
| [API_AI_TOOL_CONTRACTS.md](./docs/API_AI_TOOL_CONTRACTS.md) | API、AI Schema 和 Agent Tool 契约 |
| [TEST_AND_ACCEPTANCE.md](./docs/TEST_AND_ACCEPTANCE.md) | 测试策略、指标、验收和发布门禁 |
| [SECURITY_AND_OPEN_SOURCE.md](./docs/SECURITY_AND_OPEN_SOURCE.md) | 安全、隐私、依赖和开源治理 |
| [IMPLEMENTATION_ROADMAP.md](./docs/IMPLEMENTATION_ROADMAP.md) | 里程碑、依赖、范围与交付顺序 |

`docs/archive/` 为非权威历史材料。历史内容不得覆盖上述正式开发文档。

## M0 As-Built

M0 已完成于提交 `79825914c7c975e8be256a5a89abe812f486769e`，标签 `m0-complete` 已核验指向该提交。

当前结论：

- required CI 六项全部 PASS；
- 最新隔离 clean-room acceptance exit code 为 `0`；
- OPEN BLOCKER、CRITICAL、HIGH 均为 `0`；
- `M1 Entry Decision: ALLOWED`；
- M1 必须从最新 `main` 建立专用分支。

六项 required CI：

1. `backend-quality`
2. `frontend-quality`
3. `migration-test`
4. `compose-smoke`
5. `security-supply-chain`
6. `e2e-smoke`

正式证据：

- [M0 Development Summary](./docs/reports/M0_DEVELOPMENT_SUMMARY.md)
- [M0 Acceptance Report](./docs/acceptance/M0_ACCEPTANCE_REPORT.md)
- [M0 Final Review](./docs/acceptance/M0_FINAL_REVIEW.md)
- [M0 Issue Register](./docs/acceptance/M0_ISSUE_REGISTER.md)
- [M0 Continuous Execution](./docs/development/M0_CONTINUOUS_EXECUTION.md)

### 当前两个 LOW 风险

- `M0-ISSUE-0006`：TanStack Router plugin 依赖链中的 Babel 7 LOW advisory 暂无兼容修复；不得通过隐藏 audit 或破坏性升级伪装为零风险。
- `M0-ISSUE-0009`：Windows 默认 Playwright 入口可能无法解析 Bun；当前经过验证的入口是 `bun run --cwd frontend test:shell`。

两个风险均为 OPEN、LOW、非阻断，必须继续保留在问题台账和回归检查中。

## 已实现与计划能力

M0 交付的是可继续开发的工程底座，不是已经完成的科研产品。

| 能力 | 当前状态 | 说明 |
| --- | --- | --- |
| FastAPI、认证用户基础和健康 API | IMPLEMENTED_IN_M0 | 已有 live、ready、dependencies 与统一观测基础 |
| React、Vite、TypeScript 应用壳 | IMPLEMENTED_IN_M0 | 已有登录、首页、系统状态、错误和 404 基础 |
| PostgreSQL 与 pgvector | IMPLEMENTED_IN_M0_SMOKE | 已验证迁移与最小向量操作，尚无科研业务表 |
| Valkey 与 Celery | IMPLEMENTED_IN_M0_SMOKE | 仅有无业务副作用的 `reca.health_ping` |
| MinIO | IMPLEMENTED_IN_M0_SMOKE | 仅验证私有读写、匿名拒绝和持久性 |
| GROBID | IMPLEMENTED_IN_M0_HEALTH | 仅验证容器健康，尚未接入 PDF 业务解析 |
| OpenAPI 生成客户端与 adapter | IMPLEMENTED_IN_M0 | generated 与手工 adapter 边界已建立 |
| ResearchProject、Artifact、ApprovalRecord | PLANNED_M1 | 尚未实现 |
| 研究问题、文献检索和 EvidenceSpan | PLANNED_M2_M3 | 尚未实现 |
| 数据质量、确定性统计和图表 | PLANNED_M4_M5 | 尚未实现 |
| DOCX、Claim、证据链和复现包 | PLANNED_M6_M7 | 尚未实现 |
| 单总控 Agent | PLANNED_M8 | M8 前不得接入正式 Agent 运行时 |
| 比赛演示与发布 | PLANNED_M9 | 尚未实现 |

M0 的 `health_ping`、MinIO smoke 和 GROBID healthcheck 不得描述为科研业务能力。

## 核心闭环

RECA 0.1 的目标闭环是：

```text
研究想法
→ 结构化研究问题与人工确认
→ 真实文献检索和 PDF 解析
→ EvidenceSpan 与文献矩阵
→ 数据版本和质量检查
→ CleaningPlan / AnalysisPlan 审批
→ 确定性统计和图表
→ DOCX、Claim 与修订漂移审核
→ 文献—数据—分析—图表—论文证据链
→ ReproPackage
```

核心边界：

- 数据库是业务状态事实来源，Agent Session 不是；
- 原始文件和原始数据版本不可覆盖；
- 正式统计数字只能来自确定性程序；
- 高风险写操作必须经过 Service、Schema 和 `ApprovalRecord`；
- AI 输出是建议或结构化候选，不自动成为业务事实；
- 采用单总控 Agent，不采用自由多 Agent；
- 工具白名单、项目隔离、审计和失败披露不可绕过。

详细需求见 [PRODUCT_REQUIREMENTS.md](./docs/PRODUCT_REQUIREMENTS.md)。

## 快速启动

### 环境要求

- Docker Desktop 或 Docker Engine + Compose v2
- Python 3.11
- `uv`
- Bun 1.2.22
- Git

前端统一使用 Bun。不要把其他 JavaScript 包管理器写成当前正式入口。

### 准备配置

PowerShell：

```powershell
Copy-Item .env.example .env
```

Bash：

```bash
cp .env.example .env
```

`.env.example` 仅包含说明性占位符。不要提交真实 `.env`、Token、密码或 Provider Secret。

当前启动边界仍使用以下环境变量名称：

- `VITE_API_URL`
- `VITE_APP_ENV`
- `VITE_DEMO_MODE`
- `BACKEND_CORS_ORIGINS`
- `GROBID_URL`

默认值和生产校验以 `.env.example`、`docker-compose.yml` 和 `backend/app/core/config.py` 为准。

### 启动 Compose

PowerShell：

```powershell
./scripts/compose.ps1 up
./scripts/compose.ps1 ps
```

Bash：

```bash
./scripts/compose.sh up
./scripts/compose.sh ps
```

查看日志和停止：

```powershell
./scripts/compose.ps1 logs
./scripts/compose.ps1 down
```

```bash
./scripts/compose.sh logs
./scripts/compose.sh down
```

### 当前服务入口

| 服务 | 地址 |
| --- | --- |
| Frontend | `http://localhost:5173` |
| API | `http://localhost:8000` |
| OpenAPI | `http://localhost:8000/docs` |
| Live | `http://localhost:8000/api/v1/health/live` |
| Ready | `http://localhost:8000/api/v1/health/ready` |
| Dependencies | `http://localhost:8000/api/v1/health/dependencies` |

内部 PostgreSQL、Valkey、MinIO 管理面和 GROBID 不应为了方便而额外公开。

## 当前真实命令

### Bun 与前端

```bash
bun install --frozen-lockfile
bun run --cwd frontend dev
bun run --cwd frontend format:check
bun run --cwd frontend lint
bun run --cwd frontend build
bun run --cwd frontend generate-client
bun run --cwd frontend check-generated-client
bun run --cwd frontend test:shell
```

### 后端质量

```bash
uv sync --frozen
uv run ruff format --check backend
uv run ruff check backend
uv run mypy backend/app
uv run pytest backend/tests -m no_database
```

### Alembic

唯一迁移目录是 `backend/app/alembic/`。

```bash
uv run alembic upgrade head
uv run alembic upgrade head
```

第二次执行用于验证迁移幂等。不得引用任何非权威迁移目录。

### Celery

唯一 Celery App 是 `app.core.celery:celery_app`，源文件为 `backend/app/core/celery.py`。

```bash
docker compose exec -T worker celery -A app.core.celery:celery_app inspect ping
```

M0 唯一注册的 smoke task 是 `reca.health_ping`。它不是正式 Job、ProcessingRun 或科研异步任务。

### Clean-room 验收

PowerShell：

```powershell
./scripts/m0-acceptance.ps1
```

Bash：

```bash
./scripts/m0-acceptance.sh
```

clean-room 使用隔离 Compose project `reca_m0_acceptance`、随机临时 Secret 和 scoped cleanup，不读取开发者 `.env`，也不清理开发者默认卷。

涉及基础设施、迁移、客户端生成、配置、安全或 Compose 的变更必须运行 clean-room。普通文档变更只需执行与文档范围相称的静态检查，除非它改变上述运行契约。

## 核心目录

```text
reca/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── adapters/
│   │   ├── workers/
│   │   ├── cli/
│   │   └── alembic/
│   └── tests/
├── frontend/
│   ├── src/api/generated/
│   ├── src/api/adapter/
│   └── tests/
├── docs/
│   ├── acceptance/
│   ├── development/
│   ├── reports/
│   ├── source-research/
│   └── archive/
├── scripts/
├── .github/workflows/
├── docker-compose.yml
├── pyproject.toml
├── package.json
├── uv.lock
└── bun.lock
```

目标目录只在对应里程碑实际需要时创建。README 或路线图中的计划结构不是机械创建空目录的命令。

## M1 下一步

M1 已允许进入，但必须继续通过 M0 regression baseline。

M1 的首要工作是建立项目与文件基础，包括 `ResearchProject`、成员和项目隔离、`Artifact`、`ApprovalRecord`、正式 Job 基础、Prompt manifest 治理及相应 API、迁移和测试。准确范围与顺序以 [IMPLEMENTATION_ROADMAP.md](./docs/IMPLEMENTATION_ROADMAP.md) 为准。

不得在 M1：

- 提前实现文献、统计、论文或完整证据链业务；
- 接入正式 Agent 运行时；
- 引入自由多 Agent；
- 降低六项 required CI 或 clean-room 基线；
- 把计划对象写成已经实现。

## ARS-Codex 参考边界

`academic-research-skills-codex` 仅作为科研工作流、Prompt 契约、审核和测试方法的上游研究参考。

- RECA 不把 ARS-Codex Skill 作为运行时依赖；
- 不复制其自由会话状态作为业务状态；
- 不引入自动自由多 Agent；
- 不让模型替代确定性统计、绘图、解析、哈希或版本管理；
- 来源、固定 commit、许可证和清洁室重写决策记录在 [source research](./docs/source-research/academic-research-skills-codex.md) 与 [ADR-001](./docs/decisions/ADR-001-ARS-CODEX-USAGE.md)。

## 许可证状态

RECA 根目录当前没有项目 `LICENSE`，状态为 `PENDING_GOVERNANCE_DECISION`。

在项目负责人完成治理决定并创建真实 `LICENSE` 前：

- 不得声称 RECA 已采用某一根许可证；
- 不得根据上游模板许可证推断 RECA 根许可证；
- 第三方依赖和研究材料继续由 [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md) 与来源记录单独管理；
- 不得通过删除声明或模糊来源绕过许可证限制。

详细规则见 [SECURITY_AND_OPEN_SOURCE.md](./docs/SECURITY_AND_OPEN_SOURCE.md)。

## 历史长版 README

阶段 2 前 README 中仅具历史价值、且不再适合作为入口的独特叙事已迁入 [README_PRE_M1_LONGFORM.md](./docs/archive/README_PRE_M1_LONGFORM.md)。与 PRD、Architecture、Test、Security 和 Roadmap 重复的规范性长段落未重复归档。

旧长版曾建议创建 `docs/archive/README.md`；该建议未作为阶段 2 新文件执行，当前归档入口以上述 longform 文件为准。
