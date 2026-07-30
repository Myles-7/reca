# RECA M0 Development Summary

> Status: FINAL HISTORICAL MILESTONE RECORD
> Authority: M0 completion evidence only; do not use this file as requirements authority for M1 or later.
> Current planning: `README.md` and `docs/IMPLEMENTATION_ROADMAP.md`; evidence: `docs/acceptance/`, `m0-complete`.

## 1. 执行摘要

M0 的目标是把 RECA 从批准的产品、架构和安全文档，落实为可继续开发的模块化单体工程底座，而不是提前交付科研业务。最终交付包含 FastAPI、React/Vite/TypeScript、PostgreSQL+pgvector、Valkey、Celery、MinIO、GROBID、Docker Compose、Alembic、现代 OpenAPI client 与 GitHub Actions 质量门禁。

M0 已完成。最终主分支提交为 `79825914c7c975e8be256a5a89abe812f486769e`（PR [#1](https://github.com/Myles-7/reca/pull/1) 的 squash merge commit），完成标签 `m0-complete` 已核验指向该提交。最新 required CI 全部 PASS，最新隔离 clean-room 验收 exit code 为 `0`。问题台账最终为 OPEN BLOCKER=0、OPEN CRITICAL=0、OPEN HIGH=0，因此结论为 `M1 Entry Decision: ALLOWED`。

本报告的正式依据为 Git 历史与标签、PR #1、`docs/acceptance/` 下的验收材料、`docs/development/M0_CONTINUOUS_EXECUTION.md`、`THIRD_PARTY_NOTICES.md` 和实际工程文件；不以聊天记录作为证据。

## 2. M0 范围与非目标

M0 建立的是工程底座：可构建和隔离运行的服务拓扑、配置与密钥边界、数据库迁移、受控异步 smoke task、健康与可观测性、前端系统壳、自动生成客户端、质量门禁和 clean-room 验收。

M0 没有实现下列 M1 或后续业务能力：`ResearchProject`、`ProjectMember`、`Artifact`、`ApprovalRecord`、正式 Job 或 `ProcessingRun` 状态机、SSE、文献检索、PDF 业务解析、`EvidenceSpan`、数据集/清洗/分析业务、图表、DOCX 质控、Claim、证据图谱、Agent，以及正式演示科研数据。对象存储、GROBID 和 Worker 在 M0 中仅作为经验证的基础设施能力，不构成科研工作流。

## 3. 开发过程概览

| 阶段 | 目标与主要交付 | 验证与重要证据 | 主要问题与处理 |
|---|---|---|---|
| M0-01 | 受控导入固定上游模板，保留认证、用户、SQLModel、Alembic、React/Vite 与测试基础；删除模板 Item 示例业务；建立 RECA 目录骨架与来源记录。 | `m0-01-checkpoint`；来源记录 `docs/source-research/full-stack-fastapi-template.md`。 | 严格排除上游 `.git`、`.env`、运行数据和根许可证，正式运行不依赖 `upstream-lab`。 |
| M0-02 | 建立 Compose 服务：frontend、api、postgres、valkey、minio、grobid；固定镜像、网络、卷和容器健康检查。 | `m0-02-checkpoint`；`docker compose config` 与 Compose smoke。 | 内部服务未不必要公开；Worker 留待 M0-05。 |
| M0-03 | 建立单一 Pydantic Settings 入口，明确 local/test/demo/production、可选 Provider 与 Secret 脱敏。 | `m0-03-checkpoint`；配置测试、前端公开变量检查。 | `MODEL_API_KEY`、`OPENALEX_API_KEY` 未配置时以 `UNCONFIGURED` 表示，不阻断 API。 |
| M0-04 | 增加 live/ready/dependencies 健康端点、request ID、结构化日志、统一错误响应与 OpenAPI 约束。 | `m0-04-checkpoint`；健康、日志与 operationId 测试。 | 将进程存活与依赖就绪明确分离，避免 health check 调用模型或 OpenAlex。 |
| M0-05 | 修复/保留 Alembic，启用 pgvector；引入唯一 Celery App 和无业务副作用的 `health_ping`。 | `m0-05-checkpoint`；空库/重复迁移、pgvector、Worker ping 与任务执行。 | 不创建 Job、ProcessingRun 或业务队列表。 |
| M0-06 | 建立前端应用壳、登录基础、首页、系统状态页、错误/加载/404 和 shell Playwright。 | `m0-06-checkpoint`；production build 与浏览器 shell 测试。 | 状态页只显示真实 API 健康数据，不伪造科研指标。 |
| M0-07 | 建立后端、前端、迁移、Compose、E2E、安全供应链 CI jobs。 | `m0-07-checkpoint`；`.github/workflows/m0-quality.yml`。 | 不以 `continue-on-error`、`|| true` 或安全扫描忽略规则掩盖失败。 |
| M0-08 | 建立独立 project 的 clean-room 验收脚本和正式验收记录。 | `m0-08-checkpoint`；`scripts/m0-acceptance.ps1`、`.sh`。 | 使用随机临时凭据与 scoped cleanup，不触碰开发者卷。 |
| 集中修复与审查 | 处理 Worker/MinIO、pgvector、CI、OpenAPI 迁移、生成格式、adapter 错误映射、重启稳定性和最终 Git 收尾。 | `m0-fix*` tags、M0-FIX-7 revalidation、PR CI run `30468798214`。 | 解决所有 HIGH；保留两个明确、非阻断的 LOW 风险。 |

`m0-01-checkpoint` 至 `m0-08-checkpoint`、`m0-fix-checkpoint`、`m0-fix-2-checkpoint`、`m0-fix-3-checkpoint`、`m0-fix-6-checkpoint`、`m0-fix-7-final` 组成阶段快照。最终合并采用单一 PR squash commit，因此 `pre-m0-baseline..m0-complete` 的主线提交表现为 merge commit `7982591`。

## 4. 最终系统基础架构

RECA M0 保持模块化单体。API 位于 `backend/app/`，由 FastAPI 提供 HTTP、认证用户基础、健康接口和 OpenAPI；前端位于 `frontend/`，以 React、Vite 和 strict TypeScript 提供应用壳。`docker-compose.yml` 负责本地可重复拓扑：PostgreSQL（含 pgvector）保存关系数据，Valkey 作为 Celery broker/短期 result backend，Celery Worker 执行受控 `health_ping`，MinIO 提供私有 S3 兼容基础，GROBID 作为真实但未接入 PDF 业务的容器，frontend 与 api 提供浏览器访问边界。

Alembic 管理数据库结构；`backend/app/cli/pgvector_smoke.py` 与 `minio_smoke.py` 将基础设施验证从 PowerShell 内联命令中移出；OpenAPI 由后端暴露并生成前端 typed client；GitHub Actions 运行质量、安全、迁移、Compose 与 E2E smoke。上述组件均有明确 M0 边界：不存在业务项目模型、科研数据管道或 Agent。

## 5. 后端交付

`backend/app/core/config.py` 提供类型化、单一配置入口，区分应用、环境、认证、PostgreSQL、Valkey、MinIO、Celery 预留、GROBID、模型服务、OpenAlex、日志、CORS、Demo Mode、文件和超时限制。production 使用占位或过短 `SECRET_KEY`、无效 URL、危险 CORS 通配符、核心配置缺失等情况会安全失败；配置 repr、异常和日志不输出密码、Token、API key、完整连接串或 MinIO secret。前端仅使用白名单公开变量。

健康 API 位于 `backend/app/api/routes/health.py`：`/api/v1/health/live` 仅报告进程存活；`ready` 检查 PostgreSQL、pgvector、Valkey、MinIO；`dependencies` 以 Pydantic schema 返回 api、postgres、pgvector、valkey、minio、grobid、model、openalex 的状态。模型与 OpenAlex 未配置时返回 `UNCONFIGURED`，健康检查不会发起生成或检索业务调用。

`backend/app/core/observability.py` 与 `backend/app/main.py` 提供 `X-Request-ID` 接收/生成/回传、稳定结构化日志字段及统一错误响应。日志和响应避免 Authorization、Cookie、请求体、连接串、堆栈和内部路径。认证与用户模板基础被保留，未扩展为项目权限系统。后端健康、配置、迁移、Worker 和路由测试由 `backend/tests/` 覆盖，并纳入 `backend-quality`。

## 6. 数据库与异步任务

保留模板用户基础迁移，并在 `backend/app/alembic/versions/0002_enable_pgvector_extension.py` 启用 pgvector。验收确认空库 `alembic upgrade head` 成功，第二次执行幂等，`python -m app.cli.pgvector_smoke` 验证 extension、`vector` 类型及最小向量操作。数据库配置和迁移使用 UTC 导向的后端时间处理；没有创建任何 M1 业务表。

`backend/app/core/celery.py` 建立唯一 Celery App，Valkey 为兼容 broker，Worker 仅注册 `backend/app/workers/health.py` 中的 `health_ping`。该 task 不读取用户科研数据、不访问模型/OpenAlex、不创建 Job 或 ProcessingRun，返回稳定、非敏感结果。最终 clean-room 验证了 `celery inspect ping`、registered task、实际 task result 与 Worker 重启恢复。

## 7. 对象存储与外部依赖

MinIO 集成仅提供对象存储底座。`backend/app/cli/minio_smoke.py` 使用类型化配置和随机测试 bucket/object，验证认证写入、认证读取、内容一致性、未签名匿名 GET 被拒绝、重启后对象可读及 finally 清理。它不创建 Artifact 模型、上传 API 或科研 bucket 业务。

GROBID 使用固定 `lfoppiano/grobid:0.8.2` 真实容器和健康检查；M0 不执行 PDF 解析。Model 与 OpenAlex 不是 M0 启动依赖，未配置时在 dependency API 和状态页以 `UNCONFIGURED` 显示，而非伪造健康状态。

## 8. 前端交付

前端提供首页、`/login`、`/system-status` 与 `/404`，以及全局布局、Error Boundary、加载/错误/空状态和键盘可访问性基础。首页明确标注 RECA、Research Evidence Chain Agent、研证链 AI、当前工程基础阶段、环境和 Demo Mode；不展示项目数、文献数、数据集、分析结果或 Agent 状态等虚假业务数据。

系统状态页通过现代生成客户端读取 live、ready、dependencies，并以文字、图标和辅助说明呈现 `HEALTHY`、`DEGRADED`、`UNAVAILABLE`、`UNCONFIGURED`、`LOADING`、`UNKNOWN`。网络中断、HTTP 5xx/503 与未知响应会展示失败，而不降级为 HEALTHY；`frontend/src/api/adapter/index.ts` 将 generated fetch client 的 result/error 结构转换成稳定、脱敏的 `ApiError`，使 UI 不依赖生成器内部异常形态。

客户端生成采用 `@hey-api/openapi-ts@0.99.0`，输出位于 `frontend/src/api/generated/`。`frontend/openapi-ts.config.ts` 显式使用现代 TypeScript、client-fetch 与 SDK 插件；手工 adapter 与 generated 目录隔离。`bun run generate-client` 使用本地锁定生成器并执行 Biome 格式化，`check-generated-client` 检查必要现代文件和非空输出；CI 生成后对 generated 目录做 diff。该迁移移除了生产调用对旧 legacy client 的依赖，并经 Windows、Linux CI、type/build 与 Playwright 验证生成稳定。

## 9. 基础设施和开发体验

Compose 使用固定版本镜像，不使用关键 `latest`。服务分为浏览器可达与内部网络；PostgreSQL、Valkey、MinIO 管理面、GROBID 不被无必要绑定至所有公网接口。`postgres_data`、`valkey_data`、`minio_data` 为持久卷；PostgreSQL、Valkey、MinIO、GROBID 均有容器级健康检查。API/前端不读取 `upstream-lab`。

`scripts/compose.ps1` 与 `scripts/compose.sh` 提供一致的配置、构建、启动、状态、日志、重启和停止语义。`.env.example` 只包含说明性占位符。`scripts/m0-acceptance.ps1`/`.sh` 使用隔离 Compose project `reca_m0_acceptance`、随机运行时 Secret、专属环境文件、逐步日志与 scoped `down -v` 清理；不使用开发者 `.env`、卷、Docker Socket 或用户 Home 挂载。

## 10. CI、测试与验收

PR #1 的最终 required CI 均为 PASS：

| Required job | 最终结果 |
|---|---|
| `backend-quality` | PASS |
| `frontend-quality` | PASS |
| `migration-test` | PASS |
| `compose-smoke` | PASS |
| `security-supply-chain` | PASS |
| `e2e-smoke` | PASS |

仓库内正式证据 `docs/acceptance/M0_ACCEPTANCE_REPORT.md` 的 M0-FIX-7 final revalidation 记录：最新隔离运行 exit code `0`，通过镜像构建/启动、空库和重复迁移、pgvector、API live/ready/dependencies 与 request ID、Worker ping/registered/health_ping、MinIO 私有读写和匿名拒绝、前端页面、shell Playwright、两次 API 重启恢复、数据库与对象持久性、容器日志/仓库 Secret 扫描、Python audit、许可证与来源策略扫描及隔离资源清理。Node audit 的 LOW advisory 被报告为 `PASS_WITH_LOW_ADVISORY`，没有被删除或伪装为零漏洞。

## 11. 安全与开源合规

M0 保留 `.env.example` 而不跟踪真实 `.env`；Secret 扫描对真实私钥、Token、高熵凭据与敏感日志模式保持有效。前端 build 只接收公开变量，adapter/日志/错误响应不暴露凭据。容器不挂载 Docker Socket 或用户 Home，内部服务通过 Compose 名称通信。

上游固定为 `c9e70d65c74f7adda417fc8de0757207ff77514c`，官方来源与导入方式记录在 `docs/source-research/full-stack-fastapi-template.md`；MIT 许可证副本位于 `vendor/licenses/full-stack-fastapi-template-LICENSE.txt`。`THIRD_PARTY_NOTICES.md` 记录上游、镜像与新增依赖的版本、许可证状态和用途。RECA 根目录没有自行添加 `LICENSE`，其许可证状态仍由项目治理决定。Python audit 通过；Node 依赖不存在 Critical 或 High finding，Babel 7 LOW advisory 保留在台账。

## 12. 主要问题及解决过程

| Issue | Severity | Root Cause | Resolution | Final Status |
|---|---|---|---|---|
| M0-ISSUE-0006 | LOW | TanStack Router plugin 依赖的 Babel 7 没有兼容的修复版本；强制 Babel 8 会破坏 router compiler。 | 不隐藏 audit，不做破坏性升级；保留风险和后续维护目标。 | OPEN，非阻断。 |
| M0-ISSUE-0007 | HIGH | Worker 临时目录权限、MinIO SigV4 换行、PowerShell pgvector quoting 与验收证据缺口曾使 clean-room 非零。 | 受控 tmpfs/Worker 配置、MinIO smoke、独立 pgvector CLI 与完整 revalidation。 | RESOLVED。 |
| M0-ISSUE-0008 | HIGH | `.env.example` 误报、Linux client generation、测试邮箱和 API readiness 竞态导致 required CI 失败。 | 最小化修正扫描、跨平台生成、fixture 与等待脚本；重跑 PR CI。 | RESOLVED。 |
| M0-ISSUE-0009 | LOW | Windows 默认 Playwright config 经 `cmd.exe` 无法解析 Bun。 | shell suite 使用 Windows-aware config；默认入口修复留给后续维护。 | OPEN，非阻断。 |
| OpenAPI legacy migration | HIGH（纳入 M0-ISSUE-0008 修复链） | 新版生成器不产生旧 legacy surface，旧 UI 仍依赖 `HealthService` 等。 | 保留安全的 `@hey-api/openapi-ts@0.99.0`，迁移生产调用至 typed adapter 与现代 generated SDK。 | RESOLVED。 |
| Biome/generated consistency | HIGH（纳入 M0-ISSUE-0008 修复链） | 未格式化临时生成结果与已格式化提交输出比较。 | generation 与 comparison 使用同一 Biome 格式化流程。 | RESOLVED。 |
| Adapter error mapping | HIGH（M0-FIX-7） | client-fetch 将失败表示为 result object，原 `data!` 未稳定触发 UI error path。 | adapter 统一分类并抛出脱敏 `ApiError`；shell Playwright 6/6 PASS。 | RESOLVED。 |
| API restart / clean-room exit evidence | HIGH（M0-FIX-7） | 迁移与重型服务并发、前台工具超时和重启后等待不足使证据不可靠。 | 分阶段启动、一次性迁移容器、有界 readiness、独立追踪进程、`summary.json` 与 `exit-code.txt`。 | RESOLVED。 |
| `m0-complete` 指向错误 | Git 收尾事件 | 首次 tag 创建发生在本地 main 未快进时。 | 获得明确授权后仅删除错误的 `m0-complete`、重建 annotated tag 到 `7982591` 并验证远端。 | RESOLVED。 |

## 13. 技术决策与取舍

1. 保留 `@hey-api/openapi-ts@0.99.0`，而不是回退到含 Critical/High 漏洞的旧生成器；通过 adapter 隔离 generated API 变化。
2. generated 文件仅由生成流程维护，`frontend/src/api/adapter/` 承担手工兼容、Base URL、认证和错误映射；不手工重建旧生成器。
3. 生成流程与 Biome 格式化绑定，保证 Windows/Linux 和 CI 的确定性，而不是关闭生成一致性检查。
4. 对 Babel LOW 风险保持可见、可复现的记录；不通过 ignore、退出码掩盖或破坏性 Babel 8 升级获得表面绿色。
5. clean-room 使用独立 Compose project、随机临时凭据和 scoped cleanup，优先证明可重复性与不破坏开发者状态。
6. 不为了验收速度引入项目、Artifact、Job 或 Agent 等 M1 业务范围。
7. Git 收尾不使用 force push 或 `reset --hard`。错误 `m0-complete` tag 仅在明确授权下删除该单一远端 tag 后重建，未改变分支历史或其他 tag。

## 14. 最终交付物

| Category | Deliverable | Location / Evidence |
|---|---|---|
| 后端基础 | FastAPI、配置、健康、观测、认证/用户基础 | `backend/app/`、`backend/tests/` |
| 数据库 | Alembic 用户基础与 pgvector migration/smoke | `backend/app/alembic/`、`backend/app/cli/pgvector_smoke.py` |
| Worker | Celery App、Valkey broker、`health_ping` | `backend/app/core/celery.py`、`backend/app/workers/health.py` |
| 对象存储 | 私有 MinIO smoke 与清理 | `backend/app/cli/minio_smoke.py` |
| 前端基础 | 应用壳、状态页、生成 client、adapter | `frontend/src/`、`frontend/openapi-ts.config.ts` |
| Compose | 六项服务、网络、卷、healthcheck | `docker-compose.yml` |
| CI | 六个 required jobs | `.github/workflows/m0-quality.yml` |
| clean-room | Windows/Linux 验收入口 | `scripts/m0-acceptance.ps1`、`scripts/m0-acceptance.sh` |
| 安全与来源 | Notices、上游记录与许可证副本 | `THIRD_PARTY_NOTICES.md`、`docs/source-research/`、`vendor/licenses/` |
| 问题台账 | 全部问题及状态历史 | `docs/acceptance/M0_ISSUE_REGISTER.md` |
| 验收与审查 | Clean-room 及独立审查证据 | `docs/acceptance/M0_ACCEPTANCE_REPORT.md`、`M0_FINAL_REVIEW.md` |
| PR / merge | M0 continuous engineering foundation | PR #1；merge commit `7982591` |
| Completion tag | 已核验的 M0 完成标记 | `m0-complete` → `7982591` |

## 15. 剩余风险和后续项

`M0-ISSUE-0006` 仍为 OPEN LOW：`bun audit` 的一个 Babel 7 advisory 没有兼容的安全补丁；台账建议在 TanStack Router plugin 支持 Babel 8 后进行 M1 dependency maintenance。它不阻断 M0，因为 Critical/High 为零，风险没有被隐藏，且核心前端回归通过。

`M0-ISSUE-0009` 仍为 OPEN LOW：通用 `bun run --cwd frontend test` 在 Windows 上的 inherited Playwright server 不能解析 Bun。可用的 M0 workaround 是 `bun run --cwd frontend test:shell`；应在 M1 开发体验维护中让默认配置复用 platform-safe executable resolution。它不影响 CI E2E 或已验证的 shell suite。

两个 safety stash 仍保留：`m0-final-local-generated-route-tree-20260729` 与 `m0-final-main-sync-generated-route-tree-20260730`。它们不是 M0 正式交付物，也不应在 M1 中直接应用；应先由维护者审查其生成文件差异。

## 16. M1 进入条件

以下 M0 退出条件均已满足：

| 条件 | 结果 |
|---|---|
| OPEN BLOCKER = 0 | PASS |
| OPEN CRITICAL = 0 | PASS |
| OPEN HIGH = 0 | PASS |
| required CI | PASS |
| latest clean-room | PASS，exit code 0 |
| main merged | PASS，`7982591` |
| `m0-complete` correct | PASS，指向 `7982591` |

结论：`M1 Entry Decision: ALLOWED`。M1 应从最新 `main` 创建新的专用分支，不再继续使用 `codex/m0-continuous`。

## 17. 附录

| Item | Value |
|---|---|
| 报告生成日期 | 2026-07-30 |
| 报告生成时 HEAD | `79825914c7c975e8be256a5a89abe812f486769e` |
| Baseline tag | `pre-m0-baseline` |
| Completion tag | `m0-complete` |
| Merge commit | `79825914c7c975e8be256a5a89abe812f486769e` |
| PR | [#1](https://github.com/Myles-7/reca/pull/1)，MERGED |
| Checkpoint tags | `m0-01-checkpoint`、`m0-02-checkpoint`、`m0-03-checkpoint`、`m0-04-checkpoint`、`m0-05-checkpoint`、`m0-06-checkpoint`、`m0-07-checkpoint`、`m0-08-checkpoint`、`m0-fix-checkpoint`、`m0-fix-2-checkpoint`、`m0-fix-3-checkpoint`、`m0-fix-6-checkpoint`、`m0-fix-7-final` |
| Required CI | `backend-quality`、`frontend-quality`、`migration-test`、`compose-smoke`、`security-supply-chain`、`e2e-smoke` |
| 主要正式证据 | `docs/acceptance/M0_ISSUE_REGISTER.md`、`M0_ACCEPTANCE_REPORT.md`、`M0_FINAL_REVIEW.md`、`docs/development/M0_CONTINUOUS_EXECUTION.md` |
