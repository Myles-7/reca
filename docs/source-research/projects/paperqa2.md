# PaperQA2 source research

Document version: `1.0.0`

Document status: `Conditional Approval`

Research status: `EXPERIMENT_REQUIRED`

Last researched: 2026-07-31

Phase summary: [Literature and evidence research](../../reports/OPEN_SOURCE_RESEARCH_PHASE_2_LITERATURE.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/Future-House/paper-qa> |
| Default branch | `main` |
| Pinned research commit | `d7675d7b7eddeb3535e8c260399c5bbeeb818c50` |
| Latest release/tag | `v2026.03.18` |
| License | Apache-2.0 |
| License file | `LICENSE` |
| Main language | Python |
| Minimum runtime | Python `>=3.11` |
| Dependency manifest | `pyproject.toml` plus parser packages under `packages/` |
| Runtime dependencies | `fhaviary`, `fhlmi`, `httpx`, `numpy`, `paper-qa-pypdf`, `pybtex`, Pydantic, Tantivy, Tenacity, Tiktoken and others |
| Optional services | Qdrant, external model APIs, Zotero and parser-specific services/packages |
| Test framework | Pytest, async tests, recorded HTTP cassettes and integration tests |
| CI workflows | Quality, tests, packaging and release workflows |
| Maintenance status | Active; repository was not archived at the research commit |

## Repository structure

| Path | Purpose |
| --- | --- |
| `src/paperqa/docs.py` | document loading, parsing, embedding/index lifecycle and evidence retrieval |
| `src/paperqa/types.py` | `Doc`, `Text`, `Context`, answer/session and metadata types |
| `src/paperqa/prompts.py` | evidence summary, QA, citation and search prompts |
| `src/paperqa/settings.py` | parser, model, retrieval, answer and Agent configuration |
| `src/paperqa/agents/` | search/gather/answer workflow and tools |
| `src/paperqa/clients/` | OpenAlex, Crossref, Semantic Scholar, Unpaywall and other clients |
| `packages/` | parser integrations and related packages |
| `tests/` | document, retrieval, Agent, client, CLI and recorded-network tests |
| `docs/` | usage, evaluation and design material |

## Core pipeline

PaperQA loads documents, parses and partitions text, infers/enriches citation
metadata, embeds/indexes chunks, retrieves relevant texts, summarizes them into
evidence `Context` objects and generates an answer constrained by citation keys.
Its Agent workflow can search for papers, add sources, gather evidence, reset
evidence and answer iteratively.

## Relevant modules

`docs.py`, `types.py`, `prompts.py` and the evidence-related parts of
`settings.py` are the main selective-reuse study surface. `agents/`, provider
clients and parser packages are useful references but should not become a
parallel RECA project/runtime stack.

## Dependencies

The base package already brings a substantial model/retrieval stack including
FutureHouse LLM/Agent libraries, HTTP clients, Pydantic, Tantivy, Tiktoken and a
PDF parser package. Optional extras add local embeddings, Qdrant, usearch,
Docling, PyMuPDF, office parsing and Zotero. This breadth is a core reason to
prefer selective reuse over full runtime adoption.

Default settings expose `evidence_k`, retrieval enablement, relevance cutoffs,
summary length, text-only fallback and Agent-visible evidence counts. The source
supports a local/Numpy-style vector path, Tantivy lexical indexing and optional
Qdrant/usearch integrations.

## Document loading and chunking

The parser package family supports PDF and optional office/document formats.
`Docs` owns its own documents, texts, embeddings and indices. That is convenient
for a standalone QA system but overlaps RECA's immutable Artifact, DocumentPage,
DocumentChunk, embedding lineage and pgvector model.

RECA must not run two authoritative ingestion/chunk/index pipelines. PaperQA
logic should consume RECA-owned chunks through a translation layer or be reused
selectively after extraction from its storage assumptions.

## Retrieval and evidence packing

The strongest reusable ideas are:

- combine retrieval with per-chunk relevance assessment;
- summarize evidence separately before final synthesis;
- bound the number and length of evidence items;
- preserve source/citation keys through packing;
- strip or reject citations not present in the supplied context;
- test duplicate contexts, empty evidence, repeated queries and retrieval
  ablations;
- keep no-evidence behavior explicit instead of forcing an answer.

These behaviors can improve the M3 demonstration without adopting the complete
runtime.

## Prompt reuse candidates

Apache-2.0 permits reuse with attribution. Candidate Prompt assets include the
single-excerpt evidence-summary structure, context packing, citation-key rules,
search-status prompts and instructions to answer only from supplied evidence.

Every copied Prompt must be rewritten into RECA's Git-managed PromptContract
manifest, output Schema and data-access rules. Upstream wording cannot bypass
page/source validation, and copied Prompt paths/Commit/modifications must be
recorded.

## Code and test reuse candidates

Potential `SELECTIVE_COPY` or narrowly `VENDOR` candidates are evidence ranking,
deduplication, packing/token-budget helpers, citation-key validation and their
focused tests. Recorded HTTP test patterns and no/duplicate/conflicting evidence
fixtures are more reusable than the full Agent or index implementation.

The full `Docs`, parser/index lifecycle, provider clients, CLI and Agent state
should not be copied into core RECA because they duplicate established domain
ownership and introduce a large fast-moving model/runtime stack.

## CandidateEvidence boundary

PaperQA-derived output is limited to a RECA-owned non-authoritative shape such as:

```text
CandidateEvidence
- project_id
- document_id / document_version
- document_chunk_id
- candidate_text
- candidate_page_hint
- retrieval_score
- relevance_summary
- source_pipeline_version
- prompt/model provenance
- validation_status
```

This is normative design guidance, not a new stable Schema in this research
phase. It must not be added to the API or database without the normal contract
process.

## EvidenceSpan validation

```text
PaperQA CandidateEvidence
-> reload immutable DocumentChunk and DocumentPage
-> resolve exact source text and page
-> validate offsets/coordinates against parser/source version
-> accept EvidenceSpan or record no validated span
```

A PaperQA `Context`, citation string, score or generated excerpt is never an
EvidenceSpan. Missing validation remains absence; no placeholder span is made.

For no evidence, return an explicit insufficient-evidence candidate result. For
conflicting evidence, retain separate source candidates and surface the conflict;
do not collapse it into a single confident answer before user review.

## CLI, API and Agent

The `pqa` CLI and upstream Agent are useful demonstrations, but RECA should not
adopt their project/session/tool state as authoritative. Any later runtime
component must remain behind RECA Services and the single-controller M8 Agent,
use whitelisted Tool contracts and operate on a minimized Project snapshot.

## Tests and evaluation

The repository has broad unit/integration coverage, network cassettes, parser
fixtures, Agent tool tests and evidence/citation tests. Reusable cases include:

- empty documents and no evidence;
- duplicate/nonduplicate contexts;
- citation stripping and hallucinated citation removal;
- retrieval cutoffs and evidence-count bounds;
- repeated queries over the same sources;
- parser location preservation;
- sequential Agent behavior and tool callbacks.

RECA evaluation must additionally score source-page validation and false
EvidenceSpan creation, because PaperQA's answer quality metric is not enough.

## Operational requirements

The full runtime brings Python 3.11+, multiple model clients, parser packages,
embedding costs, Tantivy and optional vector services. It would duplicate
pgvector and increase Competition Edition failure modes. Selective reuse needs
far less operational surface and can run inside RECA's existing model/retrieval
Services after explicit validation.

## RECA current state

DEC-006 currently keeps PaperQA as retrieval-chain research and rejects wholesale
runtime adoption. Formal RECA documents require validated EvidenceSpan and
database-owned Documents/Chunks. No PaperQA code, Prompt or dependency was added
by this phase.

## Recommended integration mode

`SELECTIVE_COPY + DESIGN_REFERENCE`

Do not adopt the full runtime now. DEC-006 should remain in force, but a later
decision may broaden it from design-only research to selective Apache-licensed
Prompt, packing helper and test reuse after a validation spike. This phase does
not modify DEC-006.

## What to reuse

- evidence-summary and citation-constrained Prompt patterns;
- bounded evidence gathering and packing logic;
- relevance cutoff, deduplication and no-evidence behavior;
- citation-key validation;
- focused evidence/Agent test structures and recorded-test approach;
- evaluation ideas for retrieval and source diversity.

## What not to reuse

- `Docs`, `Doc`, `Text` or `Context` as RECA domain models;
- PaperQA parsing/chunking/index as a second source of truth;
- Qdrant/usearch/Tantivy choices merely because upstream uses them;
- upstream Agent/project/session as RECA project state;
- generated answers or contexts as EvidenceSpan;
- inferred citation metadata as validated bibliography.

## Domain boundary

RECA supplies project-scoped DocumentChunks and receives CandidateEvidence only.
RECA pgvector/repositories own retrieval scope and embedding lineage. Deterministic
page/text validation owns EvidenceSpan. User and formal workflows own decisions.

## Milestone

- M3: validation spike and optional selective evidence-packing reuse.
- M8: only then consider mapping selected workflow/Prompt ideas into the single
  controller Agent; no early Agent runtime adoption.

## Risks

- duplicate chunk/vector stores and inconsistent retrieval results;
- Prompt/model dependency churn;
- citation-looking output mistaken for source validation;
- upstream Agent bypassing RECA Tool and approval contracts;
- Python/package footprint harming demo stability;
- copied Prompt/test attribution omitted;
- evaluation optimizing answer fluency instead of evidence correctness.

## Validation spike

Feed a fixed set of RECA DocumentChunks into an isolated prototype of the
evidence-ranking/packing path. Compare retrieval-only, summary and conflict/no
evidence cases. Require every candidate to round-trip to exact page text; measure
false-positive spans, source diversity, latency, token cost and behavior when no
valid span exists. Do not allow the prototype to write RECA domain objects.

## Attribution requirements

Preserve Apache-2.0 license and notices. For copied Prompt, code or tests, record
repository, Commit, source paths, copied paths and modifications in
`THIRD_PARTY_NOTICES.md` and source research. Model/provider terms remain
separate from the software license.

## Update strategy

Track selected upstream assets by exact source path and Commit, not the entire
runtime. Re-evaluate only when a targeted upstream change improves a measured
RECA evidence problem. Any full-runtime proposal requires a new ADR.
