# Zotero source research

Document version: `1.0.1`

Document status: `APPROVED FOR M1 DEVELOPMENT`

Research status: `RECOMMENDED`

Last researched: 2026-07-31

Last updated: 2026-07-31

Phase summary: [Manuscript, citation and frontend research](../../archive/open-source-research/OPEN_SOURCE_RESEARCH_PHASE_4_MANUSCRIPT_FRONTEND.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/zotero/zotero> |
| Default branch | `main` |
| Pinned research commit | `4ec5ba9c279841b09231db82a61e30bd9e7dc6ef` |
| Research commit date | 2026-07-30 |
| Latest repository tag | `9.0.6`; research HEAD identifies `10.0.SOURCE` |
| License | AGPL-3.0, with third-party notices where applicable |
| License file | `COPYING` |
| Main language | JavaScript with desktop application resources |
| Application architecture | Zotero desktop/Gecko application with local database, sync, translators, reader and word-processor integration |
| Test framework | large Mocha/Chai-style desktop integration and unit suite |
| Maintenance status | Active; repository was not archived at the research commit |

## Repository structure

| Path | Purpose |
| --- | --- |
| `chrome/content/zotero/` | desktop library UI and application controllers |
| `chrome/content/zotero/xpcom/` | data objects, sync, translators, storage and services |
| `reader/`, `note-editor/` | document reading and notes |
| `translators/` | import/export and web-translation ecosystem integration |
| `styles/` | citation-style integration assets/submodule |
| `test/tests/` | items, collections, creators, attachments, sync, cite and UI tests |

## Data model concepts

Zotero's library model distinguishes bibliographic Items, Creators, Collections,
Attachments, Tags, Notes and Related links. Items can have child attachments and
notes; collections organize items without changing item identity; tags and
saved/search views support cross-cutting retrieval; related links connect items
without claiming scientific evidence semantics.

These are mature reference-management concepts, but Zotero keys, library IDs and
sync versions must not become RECA database identifiers.

## Citation and data exchange

Zotero supports extensive import/export through translators and citation
formatting through CSL processors/styles. Relevant exchange formats include RIS,
BibTeX and CSL JSON, plus Zotero API JSON. RECA should prefer documented exchange
formats and an explicit importer/exporter over copying desktop internals.

Imported records remain candidates: normalize DOI, creators, title, dates,
collections/tags and attachment links, retain raw provenance, and apply RECA
deduplication/project rules before creating or updating LiteratureRecord.

## Sync and desktop architecture

Zotero has sophisticated local-first sync, deletion logs, versioning, group
libraries, attachment storage and conflict behavior. Reusing that desktop stack
would introduce a second project/library database, authentication model, sync
authority and file lifecycle. Those responsibilities already belong to RECA.

## UX lessons

Useful high-level patterns include a library/collection tree, dense item list,
detail/editor pane, expandable child attachments/notes, tag filtering, saved
searches, quick item creation, explicit duplicate/merge flows and citation export.
RECA should independently implement only the patterns that serve its research
workflow and preserve project/evidence distinctions.

## Tests

The upstream suite covers items, creators, collections, tags, attachments,
annotations, related items, translators, citation data and sync. These are useful
scenario references. Copying fixtures or tests requires AGPL and dataset/content
review; many fixtures contain third-party bibliographic content.

## RECA current state

Zotero is not a runtime dependency and its desktop source is not copied. RECA
already owns LiteratureRecord, Document/Artifact, project membership, screening,
EvidenceSpan and citation/export contracts.

## Recommended integration mode

`DESIGN_REFERENCE + DATA_EXCHANGE`

Do not copy or Vendor the desktop client. A later optional Zotero integration
should use exported RIS/BibTeX/CSL JSON or a narrow Zotero API provider, returning
RECA-owned candidate DTOs. That provider requires separate credential, API and
license review.

## What to reuse

- bibliographic data-exchange concepts and documented formats;
- collection/item/detail UX organization;
- attachment/note/tag/related-item workflow ideas;
- import, duplicate and sync-conflict test scenarios as references.

## What not to reuse

- Zotero desktop source or full runtime in RECA;
- Zotero database/sync state as project business truth;
- Zotero item keys as RECA IDs;
- Related links as ClaimEvidenceLink;
- translators, fixtures or UI assets copied without AGPL/third-party review.

## Domain boundary

```text
Zotero export/API response
-> raw import Artifact/provenance
-> RECA normalization and deduplication
-> candidate LiteratureRecord/attachment mapping
-> user/project workflow
```

Zotero never writes final screening decisions, EvidenceSpan or project state.

## Milestone

- M2/M3 or later enhancement: optional import/export provider.
- Not required for Competition Core.

## Risks

- AGPL source copying creating obligations incompatible with an unreviewed root
  license decision;
- duplicate project/library and sync authorities;
- translator or format drift;
- attachment links being treated as licensed/available full text;
- trademark/branding being reused without permission.

## Validation spike

Round-trip a small licensed bibliography through RIS, BibTeX and CSL JSON. Compare
creator order, dates, DOI, collections/tags, notes and attachment metadata. Verify
raw provenance, deterministic normalization and no direct Zotero IDs in contracts.

## Attribution requirements

Zotero source is AGPL-3.0 and the Zotero name is a registered trademark. Preserve
license and applicable third-party notices for any copied material. Data records,
PDFs, translator fixtures and styles retain separate rights.

## Update strategy

Treat desktop source as design evidence. If a provider is later implemented,
pin the API/export schema and recorded fixtures rather than tracking desktop HEAD.

## Change record

| Version | Date | Status | Change |
| --- | --- | --- | --- |
| 1.0.0 | 2026-07-31 | Conditional Approval | Recorded the research evidence, recommendation and RECA authority boundaries |
| 1.0.1 | 2026-07-31 | APPROVED FOR M1 DEVELOPMENT | Synchronized documentation approval; research status and integration facts are unchanged |
