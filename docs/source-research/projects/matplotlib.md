# Matplotlib source research

Document version: `1.0.0`

Document status: `Conditional Approval`

Research status: `PLANNED`

Last researched: 2026-07-31

Phase summary: [Data, statistics and reproducibility research](../../archive/open-source-research/OPEN_SOURCE_RESEARCH_PHASE_3_DATA.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/matplotlib/matplotlib> |
| Default branch | `main` |
| Pinned research commit | `faf5d100aed23d3271245c2e800ea47f86dd858b` |
| Research commit date | 2026-07-30 |
| Latest release/tag | `v3.11.1` |
| License | Matplotlib license; permissive, with separately licensed bundled components/fonts |
| License path | `LICENSE/` |
| Main language | Python, C/C++ and JavaScript assets |
| Minimum runtime | Default branch: Python `>=3.12`, NumPy `>=2.0`; select a RECA-compatible release |
| Build/dependency manifests | `pyproject.toml`, Meson files, `environment.yml`, `tox.ini` |
| Container/service requirements | None; use a non-interactive backend in Worker/headless environments |
| Test framework | Pytest, image-comparison tests and backend-specific tests |
| CI workflows | multi-platform builds/tests, image tests, docs, wheels and release automation |
| Maintenance status | Active; repository was not archived at the research commit |

## Repository structure

| Path | Purpose |
| --- | --- |
| `lib/matplotlib/figure.py` | Figure object and layout ownership |
| `lib/matplotlib/axes/` | plotting APIs and Axes behavior |
| `lib/matplotlib/backends/` | Agg, SVG, PDF and interactive backends |
| `lib/matplotlib/font_manager.py` | font discovery, matching and cache behavior |
| `lib/matplotlib/tests/` | determinism, backend, font and image-comparison tests |
| `galleries/`, `doc/` | examples and API documentation |
| `LICENSE/` | project and bundled component/font license notices |

## Core capabilities

Matplotlib's Figure/Axes object model can deterministically render RECA's fixed
chart templates to PNG, SVG and PDF. Style, font lookup, backend, metadata,
dimensions and environment must be pinned or recorded for reproducibility.

## Relevant modules

- `Figure` and `Axes` for explicit object-oriented rendering;
- `FigureCanvasAgg`/`Agg` for headless raster rendering;
- SVG and PDF backends for vector exports;
- font manager for actual font selection and fallback diagnostics;
- `savefig` metadata, dimensions, DPI and format controls.

## RECA chart templates

| Template | Scope | Primary source |
| --- | --- | --- |
| `SCATTER` | P0-Must | approved variables and linked AnalysisResult where applicable |
| `GROUP_COMPARISON` | P0-Must | group estimates/CIs from AnalysisResult |
| `HISTOGRAM` | P0-Full | approved DatasetVersion and bin parameters |
| `BOXPLOT` | P0-Full | approved DatasetVersion and group/order parameters |
| `CORRELATION_MATRIX` | P0-Full | structured correlation AnalysisResults |

Figure values, annotations and error bars must derive from the linked data and
`AnalysisResult`; plotting code must not recompute a conflicting statistic.

## Backend and formats

Workers should select `Agg` before importing pyplot or use the object-oriented
backend API. PNG is suitable for stable previews; SVG/PDF support editable
vector output. Every format needs separate golden/structural tests because text,
metadata and layout differ by backend.

## Reproducibility

Record at least:

- template ID/version and plotting-code Artifact/hash;
- DatasetVersion, AnalysisRun and AnalysisResult IDs;
- normalized template parameters, ordering and axis limits;
- Matplotlib, NumPy and Python versions;
- backend, output format, dimensions, DPI and style version;
- actual font family, font file/hash/version and fallback decisions;
- locale/timezone and relevant environment metadata;
- output Artifact hash and deterministic metadata settings.

Upstream supports `SOURCE_DATE_EPOCH` in SVG/PDF reproducibility paths; SVG also
supports `svg.hashsalt`. Generated timestamps, random SVG IDs and unstable
metadata must be fixed or normalized when byte-level reproducibility is claimed.

## Fonts and Chinese text

Host font discovery is platform-sensitive. A Competition Edition Worker should
install and pin a CJK-capable font with redistribution terms reviewed. Record
the actual resolved font file. Missing glyphs or fallback changes must become a
Figure validation issue, not a silently accepted export.

## Tests

Upstream includes `test_determinism.py`, backend tests, font tests and visual
image comparisons. RECA needs golden renders for all five templates, structural
checks for SVG/PDF, figure-to-result numeric assertions, CJK glyph coverage,
headless rendering and repeated-run Artifact comparisons with documented
tolerances where byte identity is not portable.

## Operational requirements

- headless backend and bounded Worker memory/time;
- pinned style and font assets available in the render image;
- immutable input/result IDs and system-generated plotting code;
- new output Artifacts rather than overwriting prior figures;
- project-authorized download and no execution of user plotting code.

## RECA current state

Matplotlib is planned in M5 as the deterministic renderer. No plotting runtime
is added by this phase. `FigurePlan`, render run, `Figure`, validation issues,
code Artifact and image Artifact remain RECA-owned.

## Recommended integration mode

`DIRECT_DEPENDENCY`

Use Matplotlib inside fixed RECA template functions. The existing planned
Matplotlib boundary is a focused renderer, not a universal third-party Adapter.
Only normalized RECA inputs and outputs cross it.

## What to reuse

- Figure/Axes object model and headless backends;
- PNG/SVG/PDF exporters and metadata controls;
- style/font/determinism test patterns;
- image-comparison techniques for rendering regressions.

## What not to reuse

- arbitrary user/model-generated Python plotting code;
- host-dependent default fonts or interactive backends in Workers;
- pyplot global state as the reproducibility record;
- chart-calculated statistics that conflict with AnalysisResult;
- a rendered image without parameters, code and source lineage.

## Domain boundary

```text
FigurePlan + DatasetVersion + optional AnalysisResult
-> fixed RECA chart template
-> Matplotlib Figure/Axes
-> PNG/SVG/PDF + code Artifact + render metadata
-> Figure validation
-> immutable RECA Figure
```

## Milestone

- M5 P0-Must: `SCATTER`, `GROUP_COMPARISON`.
- M5 P0-Full: `HISTOGRAM`, `BOXPLOT`, `CORRELATION_MATRIX`.

## Risks

- platform font/layout differences;
- timestamps/random SVG identifiers breaking byte equality;
- hidden global style or backend state;
- plots recomputing or mislabeling formal statistics;
- bundled font/component licenses being overlooked;
- large figures exhausting Worker resources.

## Validation spike

Render all five templates in the exact Worker image to PNG, SVG and PDF. Repeat
runs with fixed metadata, verify hashes/structural equivalence, inspect CJK text,
assert every displayed number/error bar against AnalysisResult, and test missing
font, invalid dimensions and excessive-data failure paths.

## Attribution requirements

Preserve the Matplotlib license and review `LICENSE/` for bundled component/font
obligations. Record the exact package and font versions. A chosen CJK font needs
its own license and attribution record.

## Update strategy

Pin a released Matplotlib/NumPy combination and render-image font set. Upgrade
only after golden images, structural exports, glyph coverage, metadata and
figure-to-result assertions pass. Visual deltas require reviewed baselines.
