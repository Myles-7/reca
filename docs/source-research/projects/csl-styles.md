# CSL Styles source research

Document version: `1.0.0`

Document status: `Conditional Approval`

Research status: `PLANNED`

Last researched: 2026-07-31

Phase summary: [Manuscript, citation and frontend research](../../archive/open-source-research/OPEN_SOURCE_RESEARCH_PHASE_4_MANUSCRIPT_FRONTEND.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/citation-style-language/styles> |
| Default branch | `master` |
| Pinned research commit | `1de508b010b2643c8b13b082947f1054bc33357f` |
| Research commit date | 2026-07-28 |
| Latest release/tag | `v0.2.170` |
| License | Repository README: CC BY-SA 3.0 for styles; each selected style's `<rights>` must still be checked |
| License location | `README.md` and each style's `<rights>` metadata |
| Main content | CSL XML; Ruby/RSpec validation tooling |
| Test framework | RSpec, `csl` validator and Sheldon workflow |
| Maintenance status | Active; repository was not archived at the research commit |

## Repository structure

The research snapshot contains 2,856 independent styles in the root and 7,996
dependent styles under `dependent/`. `spec/` validates schemas, metadata,
independent/dependent placement and parent links. CSL locale files are maintained
in the separate `citation-style-language/locales` repository, not this one.

## Independent and dependent styles

An independent style contains complete citation/bibliography rules. A dependent
style points through `rel="independent-parent"` to an independent style and
mostly supplies journal/title metadata. RECA should not import dependent styles
without the referenced parent and should not flatten that relationship by hand.

## Locales

Styles may set `default-locale`, embed locale overrides or rely on processor
locale fallback. The selected GB/T files use `default-locale="zh-CN"`. A usable
runtime therefore needs the exact CSL locale files expected by the processor,
versioned separately from styles. This phase did not research or copy the
separate locales repository.

## GB/T 7714 and APA evidence

The snapshot includes GB/T 7714-1987, 2005, 2015 and 2025 variants. The relevant
2015 files include numeric, author-date and note styles. `apa.csl` identifies
itself as APA Style 7th edition. The inspected GB/T 2015 and APA files each state
CC BY-SA 3.0 in `<rights>`.

## Competition Edition minimum set

Do not copy the full 10,852-style repository. Recommended initial allowlist:

1. `china-national-standard-gb-t-7714-2015-numeric.csl` for the current P0 basic
   GB/T path;
2. `china-national-standard-gb-t-7714-2015-author-date.csl` as a small alternate
   Chinese scholarly demo style;
3. `apa.csl` for a recognizable international demonstration and future P1 path.

The second and third styles do not expand current P0 product scope. They are
small, versioned assets for validation/demonstration once a compatible processor
is selected. Full CSL, Chicago and arbitrary style installation remain P1.

## Validation

Every selected file should be pinned by upstream Commit and content hash,
validated against its declared CSL schema, checked for a resolvable parent when
dependent, and rendered against a golden metadata set. Locale and processor
versions belong in the same citation-render manifest.

## Modification and license impact

The repository requires clear CSL-project attribution and preservation of style
authors/contributors. CC BY-SA 3.0 is a share-alike content license. A modified
style should conservatively remain isolated as a separately attributed CSL asset
under its applicable license, with modification history and source available.
RECA must not claim the root license covers it or silently remove `<rights>`.

This is a governance classification, not a legal conclusion. Distribution and
modified-style obligations require review before release.

## RECA current state

P0 currently requires basic GB/T 7714 formatting; complete CSL and formats such
as APA/Chicago are P1. No CSL style file has been copied by this research phase.

## Recommended integration mode

`SELECTIVE_COPY`

Copy only the approved files and required locale assets after processor and
license decisions. Record each source path, Commit, hash, `<rights>`, authors and
modifications. Do not Vendor or Submodule the entire styles repository.

## What to reuse

- three allowlisted styles after validation;
- independent/dependent metadata and validation rules;
- upstream schema/metadata test ideas;
- explicit style IDs, updated timestamps, authors and rights metadata.

## What not to reuse

- the full style repository in the Competition Edition;
- dependent styles without parents;
- style titles as stable internal IDs without the CSL ID/hash;
- repository style updates without golden-render regression;
- any style whose `<rights>` conflicts with the intended use.

## Domain boundary

CSL files are versioned rendering inputs. They do not own LiteratureRecord,
reference metadata, citation truth, ManuscriptVersion or bibliography status.
RECA supplies normalized metadata and records the exact style/locale/processor
used to produce deterministic output.

## Milestone

- M3/M6: basic GB/T validation/rendering support where required.
- P1: broader CSL style and locale selection after processor decision.

## Risks

- copying thousands of styles without need or attribution inventory;
- style/locale/processor drift changing output;
- modifying a CC BY-SA style without preserving share-alike obligations;
- confusing GB/T 2015 and 2025 requirements;
- dependent-parent links becoming unavailable.

## Validation spike

Render the three allowlisted styles against one multilingual golden bibliography
and citation cluster. Record style/locale hashes, compare punctuation/order/name
handling, validate schema, and test missing fields. The spike must use the same
processor candidate evaluated for production adoption.

## Attribution requirements

Mention the CSL project and link to <https://citationstyles.org/>. Preserve style
authors, contributors, IDs and `<rights>`. Record Commit, copied paths, hashes and
modifications in source research and third-party notices when files are copied.

## Update strategy

Pin individual files, not repository HEAD. Review upstream changes file by file,
rerun golden rendering and accept only deliberate output changes.
