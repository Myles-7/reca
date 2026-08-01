# Open-Source Research Phase 4: Manuscript, Citation and Frontend Projects

Document version: `1.0.0`

Document status: `Conditional Approval`

Last updated: 2026-07-31

## 1. Scope

This phase researched only:

- `python-openxml/python-docx`;
- `citation-style-language/styles`;
- `Juris-M/citeproc-js`;
- `TanStack/table`;
- `xyflow/xyflow`;
- `zotero/zotero`;
- `zotero/web-library`.

Research used fixed clones of the actual GitHub repositories and inspected
licenses, manifests, source structure, tests, examples, CI and relevant current
RECA manuscript, evidence, architecture and roadmap boundaries. Temporary clones
remained outside the workspace. No upstream source, style, locale, fixture,
script, test, asset or dependency was copied into RECA.

## 2. Executive decisions

```text
DOCX stack
python-docx direct dependency
+ lxml-backed controlled OOXML enhancement
+ immutable original and derived ManuscriptVersion

Citation stack
P0 simple deterministic GB/T template
+ selectively pinned CSL style assets
+ full CSL processor deferred pending license/alternative review

Literature workbench UI stack
TanStack Table v8 direct dependency
+ RECA-owned workbench components
+ Zotero UX/data-exchange reference only

Evidence graph UI stack
backend graph authority
+ @xyflow/react visualization

License isolation
CSL styles isolated under CC BY-SA metadata
citeproc-js deferred under CPAL/AGPL review
Zotero source not copied under AGPL
```

Recommendations are research decisions, not implementation status.

## 3. Decision matrix

| Project | Recommended mode | Runtime status | Milestone | Primary decision/risk |
| --- | --- | --- | --- | --- |
| python-docx | `DIRECT_DEPENDENCY + CONTROLLED_OOXML_ENHANCEMENT` | Planned, not installed by this phase | M6 | high-level API plus narrow lxml enhancement; never overwrite original |
| CSL Styles | `SELECTIVE_COPY` | No styles copied | M3/M6/P1 | copy three files only; preserve CC BY-SA rights/authors |
| citeproc-js | `DEFERRED` | Not installed | P1 processor decision | mature but CPAL/AGPL obligations require explicit review |
| TanStack Table | `DIRECT_DEPENDENCY` on stable v8 | Planned, not installed by this phase | M2-M7 | default branch is v9 beta; UI state is not business state |
| xyflow / React Flow | `DIRECT_DEPENDENCY` | Planned, not installed by this phase | M7 | visualization only; backend graph remains authoritative |
| Zotero desktop | `DESIGN_REFERENCE + DATA_EXCHANGE` | Not installed | optional M2/M3 enhancement | do not copy AGPL desktop source or duplicate sync/project model |
| Zotero Web Library | `DESIGN_REFERENCE` | Not installed | M2/M3 UX | independently implement patterns; do not copy AGPL UI source/assets |

## 4. Fixed upstream facts

| Project | Default branch | Research commit | Latest release/tag | License |
| --- | --- | --- | --- | --- |
| python-docx | `master` | `e45454602b53e8e572b179ccf1c91093ec9f4ed7` | `v1.2.0` | MIT |
| CSL Styles | `master` | `1de508b010b2643c8b13b082947f1054bc33357f` | `v0.2.170` | styles: CC BY-SA 3.0 per README and inspected `<rights>` |
| citeproc-js | `master` | `cc9153c45293af878de08cafddbefe6ea150c380` | npm `2.4.63` | repository text: CPAL-1.0 or AGPL-3.0-or-later; package metadata has conflicting `AGPL-1.0` identifier |
| TanStack Table | `beta` | `d66b39f01e23eeb4e2befc7777194104967212d3` | stable npm v8 `8.21.3`; HEAD v9 beta `9.0.0-beta.65` | MIT |
| xyflow | `main` | `360f5b13e2bc6899ea06b4be1a49b068d86926cf` | `@xyflow/react` `12.11.2` | MIT |
| Zotero | `main` | `4ec5ba9c279841b09231db82a61e30bd9e7dc6ef` | latest repository tag `9.0.6`; HEAD `10.0.SOURCE` | AGPL-3.0 |
| Zotero Web Library | `master` | `556d0bf6b1b48fa8402a91afa62b15533b713013` | `v1.8.1` | AGPL-3.0 |

All repositories were active and not archived when inspected. A research HEAD,
release tag and package release are distinct evidence. Implementation must pin
the selected released package or individual asset, not silently follow a default
branch.

Detailed records:

- [python-docx](../../source-research/projects/python-docx.md)
- [CSL Styles](../../source-research/projects/csl-styles.md)
- [citeproc-js](../../source-research/projects/citeproc-js.md)
- [TanStack Table](../../source-research/projects/tanstack-table.md)
- [xyflow / React Flow](../../source-research/projects/xyflow.md)
- [Zotero](../../source-research/projects/zotero.md)
- [Zotero Web Library](../../source-research/projects/zotero-web-library.md)

## 5. DOCX stack

### 5.1 Selected stack

```text
python-docx = direct high-level DOCX dependency
lxml = controlled OOXML foundation
RECA OOXML enhancer = allowlisted, narrow and golden-tested
```

python-docx covers the common `Document`, `Paragraph`, `Run`, `Table`, Style,
image, relationship, comment and core-property paths. Templates should provide
known styles and numbering where possible. lxml/OOXML enhancement is justified
only for reviewed gaps such as field inspection, citation fields, revision
detection and template-specific numbering.

### 5.2 Important limitations

- revision-mark content is not fully surfaced by normal paragraph iteration;
- tracked changes are not a complete first-class editing model;
- fields/citations and advanced numbering do not have complete high-level APIs;
- comments are now supported, but anchors align to run boundaries and comments
  are limited to the main document part;
- unknown OOXML can survive round-trip, but transformations near it require
  package-level golden tests.

### 5.3 Immutability

```text
original DOCX Artifact (immutable)
-> parse/check
-> approved low-risk change on a working copy
-> new Artifact
-> derived ManuscriptVersion with parent linkage
```

No API or library call may save over the original Artifact. A failure produces
no formal derived version.

## 6. Citation stack

### 6.1 Competition Edition path

Current P0 needs basic GB/T 7714, while complete CSL and formats such as
APA/Chicago remain P1. The lowest-risk path is a deterministic RECA formatter
for the narrow P0 output, with explicit reference metadata inputs and golden
tests. It does not attempt to implement the full CSL specification.

### 6.2 Minimum CSL style set

Do not copy the 10,852-style repository. The research allowlist is:

1. `china-national-standard-gb-t-7714-2015-numeric.csl`;
2. `china-national-standard-gb-t-7714-2015-author-date.csl`;
3. `apa.csl` (APA Style 7th edition).

Only the first maps directly to the basic current P0 path. The others support a
small demonstration/future P1 validation set and do not expand requirements.
No style is copied in this phase. Required locale assets must be researched and
pinned separately because locales live in another repository.

### 6.3 Style governance

Each selected style records source Commit/path, CSL ID, content hash, authors,
contributors, `<rights>`, locale and modifications. Inspected files use CC BY-SA
3.0. Modified versions must remain separately attributed and conservatively
isolated under their applicable share-alike terms. The RECA root license remains
`PENDING_GOVERNANCE_DECISION` and cannot overwrite style rights.

## 7. citeproc-js comparison

| Option | Capability | Cost/risk | Phase 4 decision |
| --- | --- | --- | --- |
| isolated Node worker | full CSL, good protocol boundary | CPAL/AGPL and source/attribution obligations remain | best citeproc-js shape if later approved |
| isolated service | reusable network boundary | extra service; network-use license analysis is central | only if multiple clients justify operations |
| frontend package | direct browser rendering | puts CPAL/AGPL code in distributed main bundle | reject |
| alternative processor | potentially simpler license/runtime | requires separate current-repository research and goldens | preferred next investigation for full CSL |
| simple deterministic template | smallest P0 implementation | limited to approved basic formats | adopt for P0 |

citeproc-js is functionally mature and describes more than 1,300 integration
fixtures. That does not remove license complexity. Its package metadata and
repository license text also disagree on the AGPL version identifier, which is
an adoption blocker until clarified. CPAL external deployment is
treated as distribution and includes source/change/attribution requirements;
its Exhibit B specifies attribution information. AGPL has network-use source
obligations for modified versions. Isolation contains architecture and dependency
risk, not license obligations.

Runtime adoption is therefore `DEFERRED` until a processor comparison and legal/
governance review are recorded in an ADR.

## 8. Literature workbench UI stack

### 8.1 TanStack Table

Pin stable `@tanstack/react-table` v8, matching current architecture. Do not use
the v9 beta default branch. The headless table supports controlled sorting,
filtering, selection, pagination, grouping, column state and composition with
virtualization.

Target surfaces:

- literature matrix and screening;
- DataQualityIssue lists;
- AnalysisResult tables;
- ManuscriptIssue workbench;
- approval queue.

Editable cells are an application pattern, not permission or persistence. Table
selection never equals LiteratureDecision, confirmation or ApprovalRecord.
Large lists need server-side query contracts; virtualization alone only reduces
render cost.

### 8.2 Zotero design/data-exchange value

Zotero demonstrates mature Item, Creator, Collection, Attachment, Tag, Note and
Related workflows, dense library navigation and formats such as RIS, BibTeX and
CSL JSON. RECA should use documented exchange formats or a future narrow provider
that normalizes into candidate DTOs. Zotero keys, related links, sync versions
and database state do not become RECA IDs or evidence truth.

### 8.3 Zotero Web Library UX

The Web Library's collection/list/detail layout, virtual item list, tag/search
filters, read-only/edit modes and mobile drill-down are strong design references.
RECA should independently implement selected patterns using its own components,
TanStack Table and API state conventions. It should not copy AGPL components,
reducers, SCSS, icons, fixtures or branding.

## 9. Evidence graph UI stack

Use `@xyflow/react` as a direct frontend dependency for Nodes, Edges, custom
renderers, pan/zoom, selection and view-state serialization.

```text
backend evidence graph = authority
React Flow = visualization
```

The backend owns ClaimEvidenceLink, project isolation, invalidation and graph
queries. React Flow receives an authorized projection. Dragging or connecting an
edge cannot create scientific evidence or bypass a Service/API. Automatic layout
is a separate decision; coordinates are presentation state only.

Large graphs require project-scoped subgraph queries, filters/clusters and
progressive expansion rather than loading everything into the browser.

## 10. License isolation decisions

| Asset/runtime | Isolation decision | Required record |
| --- | --- | --- |
| python-docx | normal MIT dependency | package version and notice |
| lxml | direct pin if RECA imports it; review its own license | version, use and notice |
| selected CSL styles | separate content assets, not root-licensed RECA source | style rights/authors/Commit/hash/modifications |
| citeproc-js | no adoption before CPAL/AGPL choice and ADR | license choice, deployment mode, source and attribution plan |
| TanStack Table | normal MIT dependency on stable v8 | package version and notice |
| xyflow | normal MIT dependency | package version and notice |
| Zotero desktop | no source copy; data exchange/design reference | source research and any future API/export record |
| Zotero Web Library | no source/asset copy; design reference | independent implementation confirmation |

License isolation does not mean domain isolation alone. Special-license files
must retain their own license and attribution, and the undecided RECA root
license cannot relicense them.

## 11. Cross-stack workflow

```text
LiteratureRecord metadata
-> deterministic citation normalization
-> basic P0 GB/T formatting
-> DOCX manuscript check
-> ManuscriptIssue
-> approved low-risk OOXML transformation on a copy
-> new ManuscriptVersion

Literature/evidence APIs
-> TanStack Table workbench
-> backend evidence graph query
-> React Flow projection
```

Zotero exchange and UX patterns may enrich the inputs and workbench, but never
take over project, evidence, approval or version state.

## 12. Validation spikes in recommended order

1. python-docx/lxml round-trip corpus with revisions, fields, comments, numbering,
   images, tables and unknown parts.
2. basic deterministic GB/T formatter against hand-reviewed references.
3. selected CSL styles and locales rendered in a disposable processor comparison.
4. legal/governance review of citeproc-js CPAL versus AGPL obligations.
5. stable TanStack Table v8 literature matrix with server-style pagination and
   virtualized accessibility tests.
6. independently designed Zotero-inspired desktop/mobile workbench prototype.
7. React Flow authorized subgraph projection and large-graph interaction test.
8. RIS/BibTeX/CSL JSON import/export round-trip with licensed sample metadata.

Each spike remains disposable until attribution, domain boundaries and golden
tests pass.

## 13. Risks and unresolved questions

| Topic | Unresolved question | Disposition |
| --- | --- | --- |
| OOXML | exact supported field/revision subset for MANU-P0-018 | define through golden corpus in M6 |
| citations | exact simple-template output rules and locale data | derive from current P0 requirement and goldens |
| CSL locales | exact files/version/license for selected styles | separate repository research before copy |
| processor | whether a permissive full-CSL processor meets needs | compare before citeproc-js adoption |
| citeproc-js | package/repository AGPL identifier conflict and CPAL versus AGPL compliance plan | upstream clarification and governance/legal review required |
| table | virtualization package and accessibility behavior | spike with stable v8 and current React |
| graph layout | whether Dagre/ELK or backend layout is needed | defer until representative graph measured |
| Zotero integration | export files versus API provider | optional enhancement, not Competition Core |

These do not change current P0 scope or contracts.

## 14. Stable contract preservation

This phase added source-research prose only:

- Requirement IDs: unchanged.
- Acceptance IDs: unchanged.
- API paths: unchanged.
- Error codes: unchanged.
- Schema names: unchanged.
- Agent Tool names: unchanged.
- Enum values: unchanged.
- Milestone IDs: unchanged.

Research labels such as `CONTROLLED_OOXML_ENHANCEMENT` and `DATA_EXCHANGE` are
integration recommendations, not new formal Enum or Schema values.

## 15. No-code-change confirmation

Phase 4 added only seven project research Markdown files and this report. It did
not modify the nine formal entry documents, subordinate specifications,
application code, tests, dependencies, Compose, CI, migrations, generated
clients, lock files or third-party notices. It copied no upstream code, style,
locale, Prompt, test, fixture, UI asset or document.
