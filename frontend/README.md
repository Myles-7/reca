# RECA Frontend

RECA 前端是基于 React、Vite 与 strict TypeScript 的科研工作台。Bun 是仓库正式包管理器和脚本运行器。

## 技术基线

当前真实技术栈：

- React 19 + Vite；
- strict TypeScript；
- Bun；
- TanStack Router file-based routes；
- TanStack Query；
- Tailwind CSS + Radix UI primitives；
- Lucide icons；
- OpenAPI generated client；
- 手工 `api/adapter` 边界；
- Playwright shell/E2E。

视觉系统入口为 [DESIGN.md](./DESIGN.md)，Open Design 与 Codex 协作规则为 [FRONTEND_DESIGN_INTEGRATION_RULES.md](../docs/development/FRONTEND_DESIGN_INTEGRATION_RULES.md)。

## 开发命令

从仓库根目录执行：

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

以上命令与 `frontend/package.json` 当前 scripts 一致。Windows 默认 Playwright 入口存在已登记 LOW 风险，当前正式回归入口为 `test:shell`。

## 当前目录

`CURRENT`：

```text
frontend/src/
├── api/
│   ├── generated/          # 当前 OpenAPI generator output
│   └── adapter/            # 认证、错误和兼容边界
├── client/                 # 现存上游模板生成 surface；新业务不得绕过 api/adapter 使用
├── components/
│   ├── ui/                 # 共享视觉 primitives
│   ├── Common/
│   ├── Sidebar/
│   └── ...
├── features/
│   └── system-status/      # 当前 M0 feature
├── hooks/
├── routes/                 # TanStack Router file routes
├── shared/
├── main.tsx                # Provider 与 Router 装配
└── index.css               # 当前 token / theme source
```

`TARGET`：后续业务 feature 可按实际复杂度逐步形成 `api/`、`model/`、`hooks/`、`containers/`、`ui/` 等内部边界，并在真实需要时建立 mocks 或 design-system 目录。本 README 不要求移动现有文件，也不允许把 planned 目录描述为已存在。

## API 使用

正式链路：

```text
OpenAPI
→ src/api/generated
→ src/api/adapter
→ feature query / controller
→ ViewModel
→ UI
```

强制规则：

- Do not manually edit `src/api/generated/`；
- Do not fetch directly from feature UI；
- Use adapter / feature integration boundary；
- UI 不依赖 generated transport/result 细节或 Provider-specific DTO；
- Artifact/PDF URL 必须来自后端授权 API；
- API 契约变化后运行 `generate-client`，审查 diff，再同步 adapter、ViewModel 和测试。

详细规则见 [Frontend, API, and Artifact Rules](../docs/development/FRONTEND_API_AND_ARTIFACT_RULES.md)。

## Open Design 工作方式

Open Design 必须：

- 在真实 RECA `frontend/` 和当前技术栈内工作；
- 不建立第二套独立 Vite/React 产品；
- 使用 [DESIGN.md](./DESIGN.md) 和统一 Design Tokens；
- 以纯 UI、Props in / Events out 为优先；
- 使用冻结 ViewModel 的显式 Mock fixture；
- 不修改 backend、generated client、adapter、权限、Approval 或状态机所有权区域；
- 不把设计、Mock 或 planned component 写成已实现业务能力。

可执行 UI Contract 的事实来源：

- Route：`src/routes/` 中真实 TanStack Router route 定义；
- ViewModel：feature TypeScript `interface` / `type` 与 mapper 输出；
- Component Props / Events：对应 React component props 或复杂页面共享 contract 文件；
- Mock：导入正式 ViewModel 类型的 typed fixture；
- Markdown Registry：只记录 owner、milestone、freeze 状态、dependency 和 integration notes，不长期复制完整 TypeScript 类型。

普通 Open Design Mock 只用于 tests、preview、development fixture，或由现有 `VITE_DEMO_MODE` 边界显式启用并清楚标识的 Demo Mode。production data path 不得引用普通 design mock，不得用 fixture 静态替代正式 API integration，也不得把 Mock 当作 backend success 或正式验收证据。

Router、ViewModel、Mock、目录主责、并行分支和 UI Integration Gate 见 [Frontend Design Integration Rules](../docs/development/FRONTEND_DESIGN_INTEGRATION_RULES.md)。

## 当前模块导航

- [API integration](./src/api/README.md)
- [Feature ownership](./src/features/README.md)
- [Shared primitives](./src/shared/README.md)
- [Architecture](../docs/ARCHITECTURE.md)
- [Workbench ADR](../docs/decisions/ADR-006-RESEARCH-WORKBENCH-UX.md)

TanStack Table 已作为基础依赖存在；PDF.js 与 React Flow 仍是后续计划能力。Table selection 不是 Approval 或 LiteratureDecision，PDF viewer 坐标不是 EvidenceSpan 事实，React Flow edge 不是 ClaimEvidenceLink 权威。
