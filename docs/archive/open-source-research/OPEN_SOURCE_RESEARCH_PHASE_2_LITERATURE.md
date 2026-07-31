# Open-Source Research Phase 2: Literature, PDF and Evidence Projects

Document version: `1.0.0`

Document status: `Conditional Approval`

Last updated: 2026-07-31

## 1. Scope

This phase researched only:

- `J535D165/pyalex`;
- `grobidOrg/grobid`;
- `grobidOrg/grobid-client-python`;
- `mozilla/pdf.js`;
- `Future-House/paper-qa`;
- `asreview/asreview`.

Research used fixed clones of the actual GitHub repositories, repository
licenses, manifests, source trees, examples, tests, CI, service/deployment files
and current RECA requirements, models, API contracts, architecture and M2/M3
roadmap documents. Temporary clones remained outside the workspace. No upstream
code, Prompt, test, fixture or dependency was copied into RECA.

## 2. Decision summary

| Project | Recommended mode | Runtime status | Milestone | Adapter/provider boundary | Primary risk |
| --- | --- | --- | --- | --- | --- |
| PyAlex | `DIRECT_DEPENDENCY + LIGHTWEIGHT_PROVIDER` | Not installed | M2 | Yes, narrow OpenAlex provider returning RECA DTOs | provider objects/raw ranking becoming business state |
| GROBID | `INDEPENDENT_SERVICE + ADAPTER_INTEGRATION` | M0 image healthcheck only | M2-M3 | REST client plus RECA TEI converter | TEI/layout output mistaken for validated source truth |
| grobid-client-python | `SELECTIVE_COPY`, or `DIRECT_DEPENDENCY` after spike | Not installed | M2 | Transport only; no batch-filesystem/domain ownership | client/service drift and filesystem assumptions |
| PDF.js | `DIRECT_DEPENDENCY` | Not installed | M2-M3 | Focused viewer and backend-authorized file endpoint | DOM/render coordinates persisted as evidence truth |
| PaperQA2 | `SELECTIVE_COPY + DESIGN_REFERENCE` | Research only under DEC-006 | M3, selected ideas again at M8 | CandidateEvidence translation and deterministic validation | duplicate chunk/vector/Agent state and false evidence |
| ASReview | narrow `DIRECT_DEPENDENCY` or `SELECTIVE_COPY`; otherwise `DESIGN_REFERENCE` | Not installed | M3 spike; P1 enhancement | read-only ranking component | recommendation overwriting user LiteratureDecision |

Recommendations are research decisions, not implementation status. No formal
specification, API, Schema, Tool, dependency or service changed.

## 3. Fixed upstream facts

| Project | Default branch | Research commit | Latest release/tag | License | Minimum runtime |
| --- | --- | --- | --- | --- | --- |
| PyAlex | `main` | `875c708cbb6e449feebc46d2a7a26af8ed8b2fdd` | `v0.21` | MIT | Python `>=3.8` |
| GROBID | `master` | `c3229a4b9ba1e9eb8ec8327c2ec9eed1581d410c` | `0.9.0` | Apache-2.0 | current source uses Java 21 |
| grobid-client-python | `master` | `161e0f45189c8592b2e2c58e9638cc6218bc75fb` | `v0.1.5` | Apache-2.0 | Python package; exact RECA compatibility requires spike |
| PDF.js | `master` | `a80897dc9a2eb80c474717b683a4153f5b628ac7` | `v6.2.108` | Apache-2.0 | repository development: Node `>=22.13.0 || >=24` |
| PaperQA2 | `main` | `d7675d7b7eddeb3535e8c260399c5bbeeb818c50` | `v2026.03.18` | Apache-2.0 | Python `>=3.11` |
| ASReview | `main` | `d3e863c94e1945ace7848b6ca5bcf2fb1eecbdb5` | `v3.0.8` | Apache-2.0 | Python `>=3.10` |

All six repositories were active and not archived when inspected. Release tags
and default-branch Commits are different snapshots; implementation must pin the
selected release or image, not silently use these research heads.

## 4. Recommended literature loop

```text
PyAlex
-> GROBID
-> DocumentChunk
-> pgvector
-> PaperQA CandidateEvidence
-> EvidenceSpan Validation
-> ASReview Recommendation
-> User LiteratureDecision
```

The chain is an ownership sequence, not a single third-party pipeline:

1. PyAlex maps a RECA `QueryPlan` to OpenAlex and returns raw provenance plus
   normalized literature candidates.
2. A selected PDF is stored as an immutable Artifact.
3. GROBID produces candidate TEI; pypdf is an explicit degraded fallback.
4. A RECA converter creates versioned `DocumentPage`, `DocumentChunk` and
   normalized literature-reference candidates.
5. pgvector ranks only project-scoped chunks with embedding lineage.
6. Selected PaperQA patterns rank, summarize and pack `CandidateEvidence`; they
   do not create EvidenceSpan.
7. Deterministic backend validation resolves exact source page, text,
   offsets/coordinates and Document version. Invalid candidates remain absent.
8. An ASReview-style component prioritizes literature candidates using only
   confirmed user labels.
9. The user remains the authority for `LiteratureDecision`.

This arrangement maximizes the visible demo loop while keeping every formal
fact in RECA's existing domain.

## 5. PyAlex decision

PyAlex is the smallest useful direct integration. Its search, filters, grouping
and cursor pagination avoid reimplementing OpenAlex URL/query mechanics. A
lightweight provider is still mandatory because dict-like PyAlex entities are
not stable DTOs and OpenAlex rank/metadata are not formal RECA decisions.

The provider must retain raw responses/provenance, normalize DOI and authors,
bound retries/rate limits, and support Recorded/Offline tests. Default retry is
zero, so RECA must configure explicit bounded handling for `429`, `500` and
`503` rather than assume resilience.

Detailed record: [pyalex.md](../../source-research/projects/pyalex.md)

## 6. GROBID and client decision

GROBID remains an independent service because its Java runtime, models,
PDFALTO, resource limits and concurrency are operationally distinct. It provides
valuable header/full-text/reference TEI and selected coordinates, but all output
is a parsing candidate.

The authoritative conversion is:

```text
PDF Artifact
-> GROBID TEI Artifact
-> RECA Converter
-> DocumentPage / DocumentChunk / LiteratureReference
```

The Python client has useful request, concurrency and `503` behavior, but its
directory traversal and output-file model conflict with RECA Artifacts. A spike
should compare a package dependency with selectively copying the minimal
Apache-licensed transport behavior. In both cases, the TEI converter remains
RECA-owned.

Detailed records: [grobid.md](../../source-research/projects/grobid.md) and
[grobid-client-python.md](../../source-research/projects/grobid-client-python.md)

## 7. PDF.js decision

Use `pdfjs-dist` as a direct frontend dependency for canvas rendering,
TextLayer, AnnotationLayer, navigation and viewport transforms. Serve PDF bytes
through a project-authorized backend endpoint or short-lived scoped URL with
range/CORS behavior tested.

RECA should render evidence highlights from normalized page/PDF coordinates and
convert them through `PageViewport`. TextLayer DOM ranges are interaction data,
not durable evidence. Backend validation alone can accept the page/text/source
mapping.

```text
PDF.js = display and interaction
PDF.js != evidence truth source
```

Detailed record: [pdfjs.md](../../source-research/projects/pdfjs.md)

## 8. PaperQA2 decision

PaperQA2 has strong evidence-retrieval, summarization, packing, citation-key and
test patterns. Its complete runtime also owns documents, chunks, embeddings,
indices, clients, Agent state and answer sessions, overlapping RECA's Artifact,
DocumentChunk, pgvector, Project and M8 Agent contracts.

The recommended use is selective:

- adapt evidence-summary and citation-constrained Prompt patterns;
- reuse or selectively copy small ranking, deduplication and packing helpers;
- reuse no-evidence, duplicate-context, citation and repeated-query test ideas;
- translate output into non-authoritative `CandidateEvidence`;
- validate exact page/text before any EvidenceSpan exists.

Do not install the full runtime for M3 unless a later ADR proves that selective
reuse cannot deliver the measured effect. DEC-006 should remain effective. A
future ADR update may allow specific Prompt/code/test assets by path and Commit,
but this phase does not modify it.

No-evidence output must say evidence is insufficient. Conflicting evidence must
remain source-separated and visible; it must not be collapsed into a confident
fact. In all cases:

```text
PaperQA result != EvidenceSpan
```

Detailed record: [paperqa2.md](../../source-research/projects/paperqa2.md)

## 9. ASReview decision

ASReview's active-learning algorithms and simulation methodology can reduce
screening effort after enough user labels exist. Its full LAB Web product also
brings a second project database, authentication, collaboration UI, task manager
and label history, all of which conflict with RECA ownership.

Use only a narrow read-only ranking component. It receives project-scoped
literature features and confirmed decisions, and returns ordering, scores and
optional stopping suggestions. It has no write path to `LiteratureDecision`.

Active learning remains P1/enhancement. An M3 validation spike can demonstrate
the effect behind the existing REVIEW-P0 screening workflow without adding a
Requirement ID or making it Competition Core. Manual screening remains the
fallback.

Detailed record: [asreview.md](../../source-research/projects/asreview.md)

## 10. Candidate versus business fact map

| Upstream output | RECA interpretation | Formal authority |
| --- | --- | --- |
| OpenAlex/PyAlex Work | literature candidate plus raw provenance | RECA Literature Service and normalized record rules |
| GROBID TEI/header/reference | parser candidate | RECA converter and immutable source lineage |
| pypdf text | degraded page-text candidate | RECA converter with degradation metadata |
| PDF.js selection/highlight | user interaction candidate | backend source/version/page/text validation |
| pgvector nearest chunks | ranked project-scoped candidates | RECA repository scope and embedding lineage |
| PaperQA Context/answer/citation | `CandidateEvidence` or synthesis suggestion | deterministic EvidenceSpan validation and user review |
| ASReview score/predicted label/stop | screening recommendation | user-created LiteratureDecision |

## 11. Maximum demonstration value

The most effective Competition Edition slice is not a collection of upstream
UIs. It is one coherent RECA screen showing:

- reproducible OpenAlex search and candidate import;
- selected PDF with GROBID parsing status and explicit fallback;
- page/chunk navigation in PDF.js;
- project-scoped retrieval with source-diverse candidate evidence;
- click-through from a candidate summary to exact page text;
- rejection of an unvalidated candidate instead of a fabricated span;
- ranked next papers after several confirmed screening decisions;
- visible user ownership of inclusion/exclusion and evidence acceptance.

This demonstrates integration depth and scientific trust at the same time.

## 12. Current document conflicts and unresolved items

This phase found no reason to change stable identifiers, but later formal review
must resolve or clarify the following without changing their meaning casually:

| Topic | Current rule | Research pressure | Phase 2 disposition |
| --- | --- | --- | --- |
| PaperQA | DEC-006 research only; no wholesale runtime | selected Prompt/packing/test assets appear valuable | keep DEC-006; consider later asset-specific ADR amendment |
| PaperQA evidence | AI output cannot create EvidenceSpan | upstream Context/citation looks evidence-like | explicitly constrain to CandidateEvidence and validate source |
| ASReview | active learning is P1/enhancement | ranking could improve M3 demo | allow spike under existing REVIEW-P0; do not promote scope |
| ASReview decision | user owns LiteratureDecision | upstream persists labels/project state | use read-only recommendation component only |
| GROBID | M0 healthcheck only | M2 requires real parsing/conversion | research recommendation only; implementation status unchanged |
| GROBID fallback | pypdf controlled fallback | clients may hide processing differences | require explicit parser/degradation provenance |
| PDF.js | planned interaction layer | selection APIs can appear authoritative | document display-only truth boundary |
| Adapter policy | adapters are benefit-based, not universal | GROBID and providers need real boundaries | use narrow boundaries where domain/service isolation warrants them |

Potential wording conflicts were recorded only. Formal requirements, models,
contracts, architecture, roadmap and DEC-006 were not modified.

## 13. Stable contract preservation

- Requirement IDs: unchanged.
- Acceptance IDs: unchanged.
- API paths: unchanged.
- Error codes: unchanged.
- Schema names: unchanged.
- Agent Tool names: unchanged.
- Enum values: unchanged.
- Milestone IDs: unchanged.

`CandidateEvidence` in this research report is a design label for a future
non-authoritative translation object, not a newly adopted stable Schema name.
Any formal addition requires the normal contract process and baseline update.

## 14. Validation spikes in recommended order

1. PyAlex Recorded/Offline provider and normalization.
2. Pinned GROBID image, resource/error measurements and TEI Artifact retention.
3. Client-package versus minimal transport comparison.
4. RECA TEI converter golden corpus with pypdf degradation.
5. PDF.js authorized range loading and coordinate round-trip.
6. pgvector-to-PaperQA selective evidence packing with no/conflict evidence.
7. deterministic EvidenceSpan source validation.
8. ASReview-style ranking trained only on confirmed decisions.

Each spike is disposable until its domain boundary and attribution record pass.

## 15. Attribution and reuse requirements

- PyAlex: MIT notice.
- GROBID, grobid-client-python, PDF.js, PaperQA2 and ASReview: Apache-2.0 license
  and applicable NOTICE/attribution.
- Every copied Prompt, code, script, test or fixture requires source path,
  upstream Commit, copied path and modification record.
- Package/service use requires exact version/image records.
- OpenAlex data, PDFs, model services and upstream test datasets have separate
  terms; repository software licenses do not grant rights to all content.

No third-party record was added because this documentation task copied no
third-party content and introduced no runtime dependency.

## 16. No-code-change confirmation

This phase changed only six source-research Markdown files and this report. It
did not modify the nine formal entry documents, subordinate specifications,
application code, tests, dependencies, Compose, CI, migrations, generated
clients, lock files or third-party runtime records.
