# python-docx source research

Document version: `1.0.1`

Document status: `APPROVED FOR M1 DEVELOPMENT`

Research status: `PLANNED`

Last researched: 2026-07-31

Last updated: 2026-07-31

Phase summary: [Manuscript, citation and frontend research](../../archive/open-source-research/OPEN_SOURCE_RESEARCH_PHASE_4_MANUSCRIPT_FRONTEND.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/python-openxml/python-docx> |
| Default branch | `master` |
| Pinned research commit | `e45454602b53e8e572b179ccf1c91093ec9f4ed7` |
| Research commit date | 2025-06-16 |
| Latest release/tag | `v1.2.0` / PyPI `1.2.0` |
| License | MIT |
| License file | `LICENSE` |
| Main language | Python |
| Minimum runtime | Python `>=3.9` |
| Runtime dependencies | `lxml>=3.1.0`, `typing_extensions>=4.9.0` |
| Dependency manifest | `pyproject.toml` |
| Test framework | Pytest, Behave, tox and strict warning handling |
| Maintenance status | Active; repository was not archived at the research commit |

## Repository structure

| Path | Purpose |
| --- | --- |
| `src/docx/document.py` | `Document`, paragraphs, tables, comments and sections |
| `src/docx/text/` | Paragraph, Run, hyperlink and text formatting APIs |
| `src/docx/table.py` | table, row and cell APIs |
| `src/docx/styles/` | paragraph, character, table and numbering styles |
| `src/docx/opc/` | Open Packaging Convention parts and relationships |
| `src/docx/oxml/` | typed and low-level WordprocessingML elements |
| `src/docx/image/`, `src/docx/drawing/` | image parsing and inline drawing support |
| `tests/`, `features/` | unit and behavior tests |

## Core capabilities

`Document` opens or creates a DOCX package and exposes block-level content,
sections, styles, core properties, relationships and comments. `Paragraph` and
`Run` support text and common formatting; `Table` supports rows, cells and table
styles. Images can be inserted as inline shapes. Core properties expose title,
subject, author, keywords, comments, revision and timestamps.

The OPC/relationship layer is important because images, hyperlinks, headers,
footers, styles, numbering, comments and other parts are connected by package
relationships rather than a flat XML file.

## Styles and numbering

python-docx provides public style collections and paragraph/character/table
style proxies. Numbering styles and numbering parts exist, but arbitrary custom
multilevel list construction is less complete than the common paragraph API.
RECA should prefer approved templates with known style and numbering definitions
instead of synthesizing every Word structure from scratch.

## OOXML support boundary

The high-level API covers common document editing, but DOCX is much larger than
the public object model. Important boundaries include:

- paragraphs nested inside tracked insertion/deletion revision marks are not
  returned by normal `Document.paragraphs`/iteration paths;
- tracked changes are not a complete first-class editing model;
- fields and citation field codes do not have a complete high-level API;
- numbering, complex section content, floating shapes and advanced Word features
  may require direct OOXML work;
- comments are supported in 1.2.0, but anchors must align to run boundaries and
  comments can be added only in the main document part;
- unsupported content can be preserved by package round-trip, but modifying its
  surrounding XML without golden tests risks loss or corruption.

## Controlled OOXML enhancement

Recommended stack:

```text
python-docx = DIRECT_DEPENDENCY
lxml = controlled OOXML foundation
RECA OOXML enhancer = narrow, allowlisted transformations only
```

Use python-docx for normal traversal and generation. Use `lxml`/typed OOXML only
for reviewed gaps such as field-code inspection, tightly scoped citation-field
handling, revision detection and template-specific numbering. If RECA imports
`lxml` directly, pin and test it explicitly rather than treating it as an
invisible transitive detail.

The enhancer must operate on a copied package, address parts by relationship,
reject ZIP/path anomalies, preserve unknown parts and validate the resulting
package. It must not accept arbitrary XPath/XML transformations from a user,
model or Agent.

## Original-file protection

```text
uploaded DOCX Artifact (immutable)
-> read-only parse/check
-> approved low-risk transformation on a working copy
-> new DOCX Artifact
-> new ManuscriptVersion with parent lineage
```

The original DOCX is never overwritten. Parse or save failure must leave the
original Artifact and ManuscriptVersion unchanged.

## Tests

Upstream tests cover document parts, paragraphs, runs, tables, styles, images,
relationships, comments, core properties and OOXML proxies. RECA additionally
needs a golden DOCX corpus with fields, tracked changes, comments, numbering,
tables, images, headers/footers, broken relationships and unfamiliar extension
parts. Tests must reopen output in python-docx and, where practical, Word or
LibreOffice, and compare package relationships and protected content.

## RECA current state

python-docx plus controlled OOXML handling is planned for M6 manuscript checks
and low-risk fixes. This research installs nothing and does not implement DOCX
processing. ManuscriptVersion, ManuscriptIssue, transformation, Artifact and
approval remain RECA-owned.

## Recommended integration mode

`DIRECT_DEPENDENCY + CONTROLLED_OOXML_ENHANCEMENT`

A generic third-party Adapter is unnecessary. Use a focused ManuscriptDocument
Service that returns RECA-owned locations/issues and hides python-docx/lxml
objects from APIs and persistence.

## What to reuse

- Document/Paragraph/Run/Table and common style APIs;
- OPC relationships and package-part abstractions;
- image and core-property handling;
- comments where run-boundary constraints are acceptable;
- upstream unit/behavior test patterns.

## What not to reuse

- in-place saving over the uploaded DOCX;
- paragraph indexes alone as permanent locations after a transformation;
- private OOXML methods as unversioned business contracts;
- arbitrary XML, XPath, macro or field execution;
- an assumption that all revisions, fields or citations are first-class objects.

## Domain boundary

python-docx/lxml produce deterministic structure observations and a derived file.
RECA owns issue classification, source locations, approval, version lineage,
Artifact hashes and whether a result becomes formal.

## Milestone

- M6: DOCX parsing, checks, MANU-P0-018 inputs and low-risk derived versions.
- M7: include immutable manuscript versions and checks in export lineage.

## Risks

- unsupported OOXML being silently dropped or reordered;
- revision-hidden content escaping checks;
- fields/citations being mistaken for plain text;
- numbering/style IDs changing across templates;
- ZIP relationships or external links introducing unsafe access;
- output opening in python-docx but failing in real office applications.

## Validation spike

Round-trip a corpus containing comments, tracked insertions/deletions, citation
fields, multilevel numbering, images, tables and unknown parts. Apply one
allowlisted punctuation/format fix to a copy, verify the original hash, validate
relationships and reopen the result in two independent readers.

## Attribution requirements

Preserve python-docx's MIT notice when redistributing copied code. Record exact
python-docx and lxml versions. Templates, fonts and test DOCX files require their
own provenance and license review.

## Update strategy

Pin released versions and keep private OOXML use in one tested module. Upgrade
only after the golden package corpus, protected-part comparison and office-reader
compatibility pass.

## Change record

| Version | Date | Status | Change |
| --- | --- | --- | --- |
| 1.0.0 | 2026-07-31 | Conditional Approval | Recorded the research evidence, recommendation and RECA authority boundaries |
| 1.0.1 | 2026-07-31 | APPROVED FOR M1 DEVELOPMENT | Synchronized documentation approval; research status and integration facts are unchanged |
