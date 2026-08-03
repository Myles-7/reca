# RECA Visual Refresh tokens

Status: preview-scoped. These tokens and components do not change the current
production page defaults.

## Activation

Import `visual-refresh.css` in a design preview or approved UI entry, then wrap
the target subtree:

```tsx
<div className="reca-visual-refresh">...</div>
```

Use `data-theme="dark"` only in design preview surfaces. Production theme
selection continues to come from the existing `.dark` provider boundary.

## Token groups

- Canvas and surfaces: `--reca-canvas`, `--reca-background`,
  `--reca-surface`, `--reca-surface-subtle`, `--reca-surface-raised`.
- Text and structure: `--reca-foreground`, `--reca-muted-foreground`,
  `--reca-border`, `--reca-border-strong`.
- Brand and focus: `--reca-primary`, `--reca-primary-foreground`,
  `--reca-focus-ring`.
- Formal semantic results: `--reca-success`, `--reca-warning`,
  `--reca-danger`, `--reca-degraded`, `--reca-unknown`.
- Provenance semantics: `--reca-evidence`, `--reca-approval`,
  `--reca-ai-suggestion`.
- Geometry: control/panel/dialog radius, sidebar/topbar/pane dimensions,
  control height, dense row height and spacing values.

## Promotion guidance

Candidates for future global promotion after cross-page review:

- canvas/surface/foreground/border roles;
- focus ring;
- primary mapping;
- control, panel and dialog radius;
- control height, dense table row height and common spacing;
- sidebar and topbar dimensions if the production shell adopts the refresh.

Keep feature-scoped until real workflows validate them:

- evidence, approval and AI-suggestion presentation;
- degraded and unknown copy rules;
- pane widths for literature/document workspaces;
- Job progress composition and Inspector spacing.

`success` is reserved for a formally confirmed result. Unknown tones fail closed
to the `unknown` presentation. Components accept display props only and do not
own permission, version, approval, Artifact, Evidence or Job state.
