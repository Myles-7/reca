# citeproc-js source research

Document version: `1.0.0`

Document status: `Conditional Approval`

Last researched: 2026-07-31

Phase summary: [Manuscript, citation and frontend research](../../reports/OPEN_SOURCE_RESEARCH_PHASE_4_MANUSCRIPT_FRONTEND.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/Juris-M/citeproc-js> |
| Default branch | `master` |
| Pinned research commit | `cc9153c45293af878de08cafddbefe6ea150c380` |
| Research commit date | 2026-07-05 |
| Package/latest version | npm `citeproc` `2.4.63`; repository package reports the same version |
| License | Repository `LICENSE`: CPAL-1.0 or AGPL-3.0-or-later; npm metadata says `CPAL-1.0 OR AGPL-1.0`, an unresolved inconsistency |
| License files | `LICENSE`, `CPAL`, `AGPLv3` |
| Main language | JavaScript |
| Runtime dependencies | None declared by npm package |
| Test framework | citeproc test runner/Mocha-style integration corpus; more than 1,300 fixtures described upstream |
| Maintenance status | Active; repository was not archived at the research commit |

## Repository structure

| Path | Purpose |
| --- | --- |
| `src/` | processor state, CSL nodes, sorting, disambiguation, locale and output logic |
| `citeproc_commonjs.js` | CommonJS package bundle |
| `citeproc.js` | browser/raw bundle |
| `locale/` | pinned CSL locale submodule/content |
| `csl-schemata/` | CSL and CSL-M validation schemas |
| `fixtures/std`, `fixtures/local`, `fixtures/styles` | integration and style fixtures |
| `demo/` | browser integration example |
| `juris-modules/` | CSL-M legal citation modules |

## Core capabilities

citeproc-js is a mature CSL processor for citation clusters, bibliography
generation, sorting, name disambiguation, locale fallback and multilingual/legal
CSL-M extensions. The calling application supplies `retrieveItem` and
`retrieveLocale`, initializes a `CSL.Engine`, updates item IDs, processes citation
clusters and calls `makeBibliography`.

Relevant APIs include `updateItems`, `processCitationCluster`,
`previewCitationCluster` and `makeBibliography`. Processor state includes citation
order and disambiguation; it is not just a stateless string formatter.

## Node and browser use

The npm package exposes a CommonJS bundle and the repository also includes a raw
browser bundle. Both can render CSL when supplied style XML, locale XML and item
metadata. Browser use would put the licensed processor into RECA's distributed
frontend bundle. Node use can keep it in a controlled process, but process
isolation does not remove license obligations.

## Tests

The repository describes more than 1,300 integration fixtures and includes
standard CSL, processor-specific and style-level cases. This is strong functional
evidence, but the old README's example Node/test versions are not a current
runtime support statement. RECA must test the exact package on its own Node/Bun
environment and selected styles/locales.

## License analysis

The repository license text permits a choice between CPAL-1.0 and AGPL v3 or a
later version, while `package.json` declares `CPAL-1.0 OR AGPL-1.0`. This version
identifier mismatch is unresolved and must be clarified against the distributed
package and upstream before adoption. Both apparent paths require explicit review:

- AGPL-3.0 includes source-availability obligations for modified network-used
  versions;
- CPAL treats external deployment as distribution, requires source availability
  for modifications, change notices and specified attribution;
- CPAL Exhibit B names Frank Bennett, the phrase “citeproc-js implements the
  Citation Style Language”, and <https://citationstyles.org/>; it states the
  display requirement also applies to Larger Works;
- bundling, modification, hosted use and distribution choices may produce
  different obligations.

No architecture label such as “worker” or “service” neutralizes these terms.
This report does not provide a legal conclusion.

## Integration comparison

| Option | Technical fit | License/operations assessment | Decision |
| --- | --- | --- | --- |
| isolated Node worker | strong functional isolation; easy CommonJS call | still requires CPAL/AGPL compliance, source/attribution review | best citeproc-js shape if later approved |
| isolated service | clear protocol and version boundary | extra service; network-use obligations remain especially relevant | only if multiple consumers justify it |
| frontend package | lowest call latency | distributes copyleft/attribution-sensitive code in main UI bundle | reject for Competition Edition |
| alternative processor | may provide CSL with simpler license/runtime | must be researched and golden-tested separately | preferred investigation for full CSL |
| simple deterministic template | small, auditable and matches basic P0 GB/T scope | limited style coverage; no full CSL semantics | preferred P0 implementation |

## RECA current state

P0 requires basic GB/T citation formatting, while complete CSL and multiple
formats remain P1. citeproc-js is not installed and this phase copies none of its
code, fixtures, locales or processor bundles.

## Recommended integration mode

`DEFERRED` for runtime adoption.

Use a simple deterministic RECA template for the narrow P0 GB/T output. For P1
full CSL, first compare permissively licensed processors. If citeproc-js remains
the best choice after legal/governance review, use an isolated pinned Node worker
with a small RECA-owned request/response protocol and full source/attribution
compliance.

## What to reuse

- CSL processor behavior and API concepts as design evidence;
- citation-cluster, locale, disambiguation and bibliography golden cases;
- isolated worker protocol shape if legally approved;
- standard CSL fixtures only after their separate licenses are verified.

## What not to reuse

- citeproc-js in the main frontend bundle;
- processor internal state as RECA manuscript or citation business state;
- code/fixtures/locales copied before license and attribution records exist;
- isolation as a claim that CPAL/AGPL no longer applies;
- a full CSL runtime merely to satisfy the current basic GB/T P0 requirement.

## Domain boundary

```text
normalized RECA reference metadata + citation order
-> deterministic formatter or isolated CSL processor
-> rendered citation/bibliography + warnings + manifest
-> Manuscript check/export Artifact
```

The processor cannot create or validate LiteratureRecord truth, EvidenceSpan or
ManuscriptVersion. RECA records style, locale, processor and input hashes.

## Milestone

- M6 P0: simple deterministic basic GB/T formatting/checks.
- P1: full CSL processor after alternative and license review.

## Risks

- CPAL attribution/source obligations being missed;
- AGPL network-use obligations being misunderstood;
- old CommonJS/technical debt increasing integration cost;
- inconsistent AGPL version metadata between package and repository license;
- processor state producing non-reproducible citation ordering if not captured;
- style/locale/processor versions drifting independently.

## Validation spike

Without shipping code, compare a disposable Node worker and one alternative
processor against the three selected CSL styles and golden references. Measure
correctness, determinism, startup cost and protocol simplicity. Complete a
license-obligation checklist before any adoption PR.

## Attribution requirements

If adopted, preserve the selected license, copyright, source availability,
change records and required attribution. Record package version, Commit, license
choice, source location and deployment mode. CSL styles/locales retain separate
licenses and attribution.

## Update strategy

Do not add citeproc-js until an ADR records processor comparison and license
choice. If adopted, pin the package and worker image and replay full citation
goldens before upgrades.
