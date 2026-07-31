# GROBID source research

Document version: `1.0.0`

Document status: `Conditional Approval`

Research status: `ALREADY_INTEGRATED`

Last researched: 2026-07-31

Phase summary: [Literature and evidence research](../../reports/OPEN_SOURCE_RESEARCH_PHASE_2_LITERATURE.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/grobidOrg/grobid> |
| Default branch | `master` |
| Pinned research commit | `c3229a4b9ba1e9eb8ec8327c2ec9eed1581d410c` |
| Latest release/tag | `0.9.0` |
| License | Apache-2.0 |
| License file | `LICENSE` |
| Main language | Java |
| Minimum runtime | Current source uses Java 21 toolchains |
| Dependency/build manifest | Gradle build files |
| Container/service requirements | GROBID service, models, PDFALTO and substantial CPU/RAM |
| Test framework | Gradle/JUnit plus evaluation and service tests |
| CI workflows | CRF/DeLFT/ONNX builds, evaluation, CodeQL, Trivy and release workflows |
| Maintenance status | Active; repository was not archived at the research commit |

The pinned default branch is newer than RECA's current smoke image
`lfoppiano/grobid:0.8.2`. This phase does not update that image.

## Repository structure

| Path | Purpose |
| --- | --- |
| `grobid-core/` | parsing engines, document model, TEI production and PDFALTO integration |
| `grobid-service/` | REST resources and service lifecycle |
| `grobid-home/` | models and runtime configuration |
| `config/` | full and example configuration |
| `doc/` | service and model documentation |
| `Dockerfile.crf`, `Dockerfile.delft` | CRF and deep-learning service images |
| `monitoring/` | service monitoring assets |

## Core capabilities

The REST service includes health/version endpoints and document processing for
headers, full text, assets and references. Full-text processing can consolidate
headers, citations and funders; preserve raw fields; generate IDs; segment
sentences; and request coordinates for selected TEI elements.

TEI output can contain structured header metadata, body sections, bibliographic
references and coordinates. It is parser output with model uncertainty, not a
validated representation of the PDF.

## Relevant modules

`grobid-service` supplies the HTTP boundary, `grobid-core` supplies parsing and
TEI generation, `grobid-home` supplies models/configuration, and PDFALTO supplies
layout-aware PDF conversion. RECA integrates the service, not these Java modules
inside the Python backend.

## Dependencies

The service depends on the Java/Gradle application, GROBID model assets and
PDFALTO; optional DeLFT variants add deep-learning dependencies. Container image,
models and native PDFALTO resources must be treated as one pinned runtime unit.

## Layout and language behavior

GROBID is designed for scholarly PDFs and handles many headers, references,
languages and layouts better than plain text extraction. Double-column,
scanned, malformed, unusual-font and heavily graphical documents can still
produce reordered, missing or incorrect text. Requested coordinates help
traceability but do not eliminate the need to compare against the source page.

## Batch and resource behavior

GROBID supports concurrent service requests and batch clients. The inspected
configuration exposes service concurrency, PDF/token limits, PDFALTO timeout
and memory controls; the full configuration uses a PDFALTO timeout around 120
seconds and a memory limit around 6096 MB. Exact values must be tuned to the
pinned image and Competition Edition host.

CRF/Wapiti models are the normal lightweight path. DeLFT/deep-learning models
increase resource and startup requirements. Model preload reduces request
latency at the cost of memory.

## Failure types

Observed service mappings include:

- `204 NO_CONTENT` when parsing produces no usable model result or input fails;
- `400`/conflict-style client errors for invalid requests;
- `503 SERVICE_UNAVAILABLE` when no engine is available;
- `500 INTERNAL_SERVER_ERROR` for processing failures;
- timeout, oversized input and malformed PDF behavior at lower layers.

RECA must preserve the original Artifact and record a degradation/failure reason.
No empty or malformed TEI may be promoted to a successful parsed Document.

## Required conversion flow

```text
PDF Artifact
-> GROBID TEI
-> RECA Converter
-> DocumentPage / DocumentChunk / LiteratureReference
```

The converter owns TEI validation, page mapping, normalized reference objects,
chunk boundaries, source offsets, parser version and lineage. GROBID types and
TEI nodes do not become core domain objects.

## pypdf fallback boundary

`pypdf` remains a controlled fallback for text extraction when GROBID is
unavailable or fails. It may support page-level text and simple metadata, but it
does not reproduce GROBID's structured reference/full-text semantics. A fallback
result must record parser kind and degradation; it must not silently masquerade
as equivalent TEI output.

## Tests

Upstream tests and evaluation corpora cover parser/service behavior. RECA needs
its own fixed legal test PDFs for single/double-column, multilingual, complex
references, malformed input and scanned/no-text cases. Golden checks must focus
on lineage, page mapping, chunk/reference stability and failure classification,
not exact reproduction of every upstream TEI byte.

## Operational requirements

- pinned image and model family;
- private service network and health/version checks;
- CPU/RAM, concurrency, timeout and upload limits;
- original PDF and raw TEI retained as immutable Artifacts;
- retry only for transient busy/unavailable failures;
- pypdf fallback with explicit degradation metadata.

## RECA current state

GROBID is present only as M0 smoke/health infrastructure. The formal M2 parsing
flow and TEI converter are planned, not implemented.

## Recommended integration mode

`INDEPENDENT_SERVICE + ADAPTER_INTEGRATION`

Use the pinned service through a small client boundary and a RECA-owned TEI
converter. The service boundary is justified by Java/models/resource isolation;
the converter is justified by domain and evidence-truth separation.

## What to reuse

- official service image and REST endpoints;
- header, full-text and reference extraction;
- selected TEI coordinates and generated IDs;
- busy/error semantics and health/version endpoints;
- upstream evaluation ideas for a small RECA golden corpus.

## What not to reuse

- TEI as the database schema;
- parser coordinates/text as automatically valid `EvidenceSpan`;
- GROBID filesystem paths as Artifact identifiers;
- upstream concurrency defaults without host measurement;
- DeLFT merely because it exists;
- GROBID success status as formal RECA processing success.

## Domain boundary

GROBID creates parsing candidates. RECA validates TEI, maps pages, stores chunks
and references, and later validates evidence against the immutable PDF. Only
RECA Services may create formal objects and statuses.

## Milestone

- M2: pinned service, Worker client, TEI Artifact and converter.
- M3: page/text validation for extraction candidates and EvidenceSpan.

## Risks

- high memory/CPU and cold-start cost;
- model/image drift changing TEI output;
- layout errors in double-column or graphical PDFs;
- coordinates unavailable for required elements;
- transient saturation confused with corrupt input;
- fallback semantics hiding lower-quality parsing.

## Validation spike

Run the pinned image against a small licensed corpus covering simple,
double-column, multilingual, reference-heavy, scanned and corrupt PDFs. Measure
startup, memory, latency, `503` behavior and coordinate coverage. Convert TEI to
RECA candidate DTOs and verify page text against the original PDF before any
EvidenceSpan is accepted.

## Attribution requirements

Preserve Apache-2.0 license and NOTICE obligations for redistributed software or
images. Record exact image tag/digest, repository Commit and model family. Test
PDFs and evaluation data need separate licenses.

## Update strategy

Pin image digest and converter schema together. An upgrade requires golden-corpus
comparison, resource measurement, error mapping and converter compatibility. Do
not follow default-branch models automatically.
