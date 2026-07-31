# PDF.js source research

Document version: `1.0.0`

Document status: `Conditional Approval`

Research status: `PLANNED`

Last researched: 2026-07-31

Phase summary: [Literature and evidence research](../../archive/open-source-research/OPEN_SOURCE_RESEARCH_PHASE_2_LITERATURE.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/mozilla/pdf.js> |
| Default branch | `master` |
| Pinned research commit | `a80897dc9a2eb80c474717b683a4153f5b628ac7` |
| Latest release/tag | `v6.2.108` |
| License | Apache-2.0 |
| License file | `LICENSE` |
| Main language | JavaScript |
| Minimum development runtime | Repository `package.json`: Node `>=22.13.0 || >=24` |
| Package manifest | `package.json`; published distribution is `pdfjs-dist` |
| Container/service requirements | Browser plus PDF/worker assets served over HTTP(S) |
| Test framework | Jasmine, Puppeteer, reference, unit and integration suites |
| CI workflows | Unit, integration, browser/reference, font, type, lint, CodeQL and release workflows |
| Maintenance status | Active; repository was not archived at the research commit |

The upstream repository development runtime does not automatically define the
minimum browser/runtime of a released `pdfjs-dist` build. Adoption must test the
exact package release against RECA's Bun/Vite/browser matrix.

## Repository structure

| Path | Purpose |
| --- | --- |
| `src/display/` | document loading, canvas, text, annotation and viewport APIs |
| `src/core/` | PDF parsing and worker-side implementation |
| `web/` | full viewer, page views, navigation, text/annotation layer builders |
| `examples/` | embedding and API examples |
| `test/unit`, `test/integration`, `test/pdfs` | unit, browser integration and reference corpus |
| `gulpfile.mjs` | generic/legacy builds and test tasks |

## Core capabilities

- page rendering to canvas;
- worker-based parsing;
- `TextLayer` for selectable/searchable positioned text;
- `AnnotationLayer` for links and PDF annotations;
- page navigation, zoom, rotation and viewport transforms;
- range/stream loading controls for large PDFs;
- optional full viewer UI and localization.

The relevant frontend abstraction is normally `pdfjs-dist`, not a fork of the
entire upstream viewer.

## Relevant modules

The public display API, worker, `PageViewport`, TextLayer and AnnotationLayer are
the primary integration surface. The full `web/` viewer is a design/reference
source unless RECA deliberately adopts its larger UI state machine.

## Dependencies

Use the released `pdfjs-dist` package and its matching worker asset. The large
upstream development dependency set is for building/testing PDF.js itself and
should not be copied into RECA. Exact Bun/Vite/browser compatibility remains a
package-version spike.

## Loading, CORS and authorized files

PDF.js supports URL and binary-data inputs and exposes request options including
HTTP headers, credentials and range behavior. RECA should not place long-lived
object-store credentials or model tokens in the browser. The preferred path is
an authorized backend file endpoint or short-lived project-scoped URL with
range support, correct CORS headers and content disposition.

For large files, preserve HTTP range requests and avoid copying the entire PDF
into React state. The worker asset must be pinned and bundled/served consistently
with the main package version.

## Page navigation and layers

The viewer exposes current page and scroll-to-destination behavior. A focused
RECA viewer can render canvas, TextLayer and AnnotationLayer while keeping its
own toolbar and evidence panel. The full upstream viewer is only justified if
its larger state, UI and customization cost is accepted explicitly.

## Evidence highlight mapping

`PageViewport` converts PDF-space points to viewport coordinates and back.
`PDFPageView.getPagePoint` delegates to `convertToPdfPoint`. RECA can render a
highlight from stored normalized page coordinates after applying page scale,
rotation and viewport transforms.

TextLayer DOM offsets are rendering artifacts and can change with zoom, fonts
or PDF.js releases. They may help a user select candidate text, but the backend
must resolve the selection against the immutable DocumentPage text and source
coordinate system before an EvidenceSpan is created.

```text
PDF.js = display and interaction
PDF.js != evidence truth source
```

## Custom highlighting

Use an RECA-owned overlay keyed by page number and normalized PDF coordinates.
Do not mutate upstream TextLayer internals as the storage model. Selection can
submit page, selected text, viewport/PDF coordinates and document version to a
backend validation endpoint. A mismatch produces a candidate-resolution error,
not a fabricated span.

## Tests

Upstream has extensive unit, integration, browser and reference-image coverage.
RECA needs focused browser tests for authorized loading, worker startup, page
jump, zoom/rotation, TextLayer selection, overlay transform, large-file range
requests, denied project access and stale DocumentVersion highlights.

## Operational requirements

- exact `pdfjs-dist` package and worker version alignment;
- backend authorization and project isolation for PDF bytes;
- range/CORS support where used;
- memory-aware page rendering and page cleanup;
- coordinate normalization independent of DOM layout;
- no browser-side trust decision for evidence.

## RECA current state

PDF viewing and EvidenceSpan interaction are planned for M2/M3. PDF.js is not a
current dependency and this research did not add it.

## Recommended integration mode

`DIRECT_DEPENDENCY`

Use released `pdfjs-dist` with a focused RECA viewer. Consider `SELECTIVE_COPY`
only for small Apache-licensed viewer utilities when a documented customization
cannot be maintained through public APIs. Do not Vendor the full viewer by
default.

## What to reuse

- display API and worker;
- canvas, TextLayer and AnnotationLayer;
- page navigation and viewport conversion;
- range loading and cancellation;
- upstream browser-test ideas for coordinates and rendering.

## What not to reuse

- PDF.js parsed text or DOM positions as formal evidence truth;
- the full viewer's state as RECA project state;
- public object-storage URLs without project authorization;
- annotations as `EvidenceSpan` without backend validation;
- latest master build merely to match upstream development.

## Domain boundary

PDF.js receives authorized bytes and RECA-owned Document/Evidence DTOs. It emits
interaction candidates. Backend Services validate document version, page, text
and coordinates, and alone may create or update EvidenceSpan.

## Milestone

- M2: document viewer and page navigation.
- M3: validated selection/highlight workflow for EvidenceSpan.

## Risks

- package/worker mismatch;
- memory pressure from many rendered pages;
- CORS/range configuration failures;
- DOM coordinates stored as durable evidence;
- rotation/crop-box transform errors;
- frontend authorization bypass through direct storage URLs.

## Validation spike

Load a protected 100+ page PDF through the backend, verify range requests, jump
to a page, rotate/zoom, select text and round-trip a rectangle between PDF and
viewport coordinates. Reject a stale DocumentVersion and verify a stored
highlight remains aligned after zoom.

## Attribution requirements

Preserve Apache-2.0 license and notices for redistributed files. Record the exact
`pdfjs-dist` version. Any selectively copied viewer code requires source path,
Commit and modification records.

## Update strategy

Upgrade released packages deliberately, always keeping worker and API versions
paired. Run the viewer interaction suite and coordinate golden cases before an
upgrade reaches a milestone branch.
