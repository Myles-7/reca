# Great Expectations source research

Document version: `1.0.0`

Document status: `Conditional Approval`

Research status: `RECOMMENDED`

Last researched: 2026-07-31

Phase summary: [Data, statistics and reproducibility research](../../archive/open-source-research/OPEN_SOURCE_RESEARCH_PHASE_3_DATA.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/great-expectations/great_expectations> |
| Default branch | `develop` |
| Pinned research commit | `33614cd70a407f8b9589fa2cf5f1cb1d7d0723aa` |
| Research commit date | 2026-07-24 |
| Latest release/tag | `1.19.1` |
| License | Apache-2.0 |
| License file | `LICENSE` |
| Main language | Python |
| Minimum runtime | Python `>=3.10` at the research commit |
| Dependency manifests | `pyproject.toml`, `setup.py`, `requirements.txt`, constraints files |
| Core dependencies | pandas, NumPy, SciPy, Pydantic, Marshmallow, Jinja, Requests and Ruamel YAML, plus optional integrations |
| Container/service requirements | In-process core; production patterns may add Data Context, stores, rendered Data Docs and external backends |
| Test framework | Pytest with unit, integration, performance and renderer tests |
| CI workflows | quality, tests, integration, packaging, security and release workflows |
| Maintenance status | Active; repository was not archived at the research commit |

The repository required a sparse Windows checkout during research because some
test paths exceed common checkout limits. This did not change the inspected
Commit or license.

## Repository structure

| Path | Purpose |
| --- | --- |
| `great_expectations/expectations/` | expectation classes, registry and metrics |
| `great_expectations/core/expectation_suite.py` | suite configuration |
| `great_expectations/checkpoint/` | checkpoint orchestration and results |
| `great_expectations/validator/` | execution and validation behavior |
| `great_expectations/data_context/` | configuration, stores and project context |
| `great_expectations/render/` | validation rendering and Data Docs structures |
| `tests/` | expectations, validators, stores, checkpoints, rendering and integrations |

## Core capabilities

Great Expectations models reusable Expectations, groups them into
`ExpectationSuite`, runs validations through Validators and Checkpoints,
produces structured Validation Results, persists configuration/results in
Stores and renders Data Docs for human review.

## Relevant modules

The useful research surface is the taxonomy of expectation types, suite-level
aggregation, validation-result summaries, separation of configuration/execution/
rendering, and human-readable failure descriptions. Data Context, Checkpoint,
Store and deployment machinery are not needed for the P0 M4 runtime.

## Dependencies

The runtime surface is substantially larger than Pandera and adds its own
configuration, context, stores, rendering and integration concepts. Running it
beside Pandera would require duplicate schema translation, failure normalization,
version pinning, performance tests and reconciliation rules.

## Tests

Upstream tests cover expectation semantics, Validators, Checkpoints, Stores,
renderers, integrations and performance. RECA may adapt test taxonomy, message
quality and report-structure ideas. Any copied test or wording requires
Apache-2.0 attribution and path-level modification records.

## Operational requirements

A full deployment can require Data Context configuration, Stores, Checkpoints,
Data Docs build/hosting and datasource/execution-engine setup. None of these
should become a Competition Core prerequisite while RECA already owns runs,
issues, Artifacts and reports.

## RECA current state

Great Expectations is not installed or planned as the M4 authority. Pandera is
the named deterministic validation candidate. RECA owns `DataQualityRun`,
`DataQualityIssue`, DatasetVersion, report Artifacts and approval.

## Recommended integration mode

`DESIGN_REFERENCE + SELECTIVE_COPY` only after license/attribution review.

Do not run Great Expectations as a second P0 validation engine. Selectively
adapt rule taxonomy, report layout, wording and test patterns into RECA-owned
definitions when they improve the competition experience.

## Pandera overlap decision

| Concern | Pandera P0 role | Great Expectations research value |
| --- | --- | --- |
| dataframe schema/check execution | sole runtime authority | overlapping; do not execute in P0 |
| lazy failure aggregation | runtime result source | compare report organization only |
| rule suite identity | RECA versioned rules over Pandera | suite/versioning design reference |
| human-readable reports | RECA normalized issue UI | Data Docs/rendering inspiration |
| validation stores/checkpoints | RECA runs, Artifacts and Jobs | do not adopt as business state |
| test wording/taxonomy | RECA golden tests | selective reference/copy candidate |

Two runtime authorities would create ambiguous counts, severities and pass/fail
outcomes. A rule passes only according to the one versioned RECA/Pandera path.

## What to reuse

- expectation taxonomy and human-readable rule descriptions;
- suite-level status aggregation and validation-result summary ideas;
- configuration/execution/rendering separation;
- Data Docs information architecture for report UX;
- edge-case, failure-message and renderer test patterns.

## What not to reuse

- Great Expectations as a second P0 validation runtime;
- Checkpoint, Store or Data Context as RECA business objects;
- expectation IDs as stable RECA rule identities without normalization;
- generated Data Docs as the only persisted DataQualityRun result;
- full deployment/runtime merely to borrow report wording.

## Domain boundary

```text
Great Expectations source/design research
-> selected taxonomy, report or test idea
-> attribution and RECA-owned implementation
-> RECA rule definitions and DataQuality UI

Pandera runtime
-> DataQualityRun / DataQualityIssue business truth
```

No Great Expectations runtime object enters the domain.

## Milestone

- M4: design/test/report reference only.
- Later production analytics governance may reconsider a full platform through
  a separate ADR, but it must not duplicate P0 authority by default.

## Risks

- accidental dual validation authorities and conflicting outcomes;
- adopting a large Data Context/Store deployment for a small P0 need;
- copied wording/tests without attribution;
- expectation taxonomy being mistaken for existing Requirement IDs;
- report polish masking differences in actual validation semantics.

## Validation spike

No runtime spike is recommended for P0. Instead, compare one RECA/Pandera run
with selected GX report examples and prototype a RECA-owned summary for missing,
range and type issues. Evaluate clarity, actionability and attribution cost. Only
reconsider runtime use if Pandera demonstrably cannot meet an accepted need.

## Attribution requirements

Preserve Apache-2.0 and applicable notices for copied code, tests or text. Record
upstream Commit, source path, copied path and modifications. Referencing an idea
without copying still requires honest source-research documentation.

## Update strategy

Track GX only when revisiting report/test design. Do not follow every release or
add it to the runtime compatibility matrix. Any future runtime proposal requires
an ADR explaining why one validation authority is insufficient.
