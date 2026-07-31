# ASReview source research

Document version: `1.0.0`

Document status: `Conditional Approval`

Last researched: 2026-07-31

Phase summary: [Literature and evidence research](../../reports/OPEN_SOURCE_RESEARCH_PHASE_2_LITERATURE.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/asreview/asreview> |
| Default branch | `main` |
| Pinned research commit | `d3e863c94e1945ace7848b6ca5bcf2fb1eecbdb5` |
| Latest release/tag | `v3.0.8` |
| License | Apache-2.0 |
| License file | `LICENSE` |
| Main language | Python with React web application |
| Minimum runtime | Python `>=3.10` |
| Dependency manifest | `pyproject.toml`; `asreview/webapp/package.json` |
| Core dependencies | NumPy, pandas, scikit-learn, RISPy, Flask, SQLAlchemy and web dependencies |
| Container/service requirements | None for algorithms; full LAB adds Flask, SQLite/project files and web UI |
| Test framework | Pytest plus web/API/integration tests |
| CI workflows | Quality, tests, packaging, docs and release workflows |
| Maintenance status | Active; repository was not archived at the research commit |

## Repository structure

| Path | Purpose |
| --- | --- |
| `asreview/learner.py` | active-learning fit/query/label loop |
| `asreview/models/` | classifiers, features, balancers, queriers and stoppers |
| `asreview/data/` | CSV/RIS readers, records and search helpers |
| `asreview/simulation/` | simulation runner and CLI |
| `asreview/database/` | labels, records, rankings and project persistence |
| `asreview/project/` | project archive/schema/migration behavior |
| `asreview/webapp/` | Flask APIs, authentication, task manager and React LAB UI |
| `tests/` | algorithms, state, readers, simulation and project tests |

## Core capabilities

ASReview implements active-learning screening: users provide or discover seed
labels, a feature extractor transforms title/abstract text, a classifier learns
from included/excluded labels, a query strategy prioritizes records, and the
loop repeats as users label results. It supports simulation on fully labeled
datasets and pluggable model components.

The inspected model entry points include SVM, Naive Bayes, Random Forest and
logistic classifiers; TF-IDF and one-hot features; balanced sampling; random,
top-down, max and uncertainty query strategies; and stopping helpers such as
last relevant, number labeled, quantile labeled and fit readiness.

## Relevant modules

`learner.py` and `models/` are the narrow algorithm surface. `simulation/`
provides evaluation methodology. `database/`, `project/` and `webapp/` implement
the separate ASReview product state and should not be adopted as RECA ownership.

## Dependencies

Algorithm use centers on NumPy, pandas and scikit-learn. The full product adds
Flask, CORS/login/mail, SQLAlchemy, Waitress, a React application and supporting
packages. RECA should avoid that full dependency surface for a ranking feature.

## Seed, labels and decisions

ASReview uses prior/seed labels to make the learner trainable and stores record
labels/history. In RECA, those labels must map through RECA-owned literature
records and decisions. An ASReview score, predicted class, stopping suggestion
or imported label is a candidate/recommendation until the user records the
formal `LiteratureDecision`.

Final RECA decision values remain:

```text
INCLUDED
EXCLUDED
UNCERTAIN
```

No ASReview-specific project state or binary label may silently overwrite them.

## Prioritization and stopping

Prioritization is the most valuable capability for a large candidate set. RECA
can train on user-confirmed included/excluded decisions and request the next
ranked records. Uncertainty sampling can support ambiguous candidates; top-down
ranking can maximize likely inclusions.

Stopping models and progress estimates are advisory. They can inform a user that
screening may have reached diminishing returns, but cannot declare a review
complete or change formal inclusion/exclusion decisions.

## Data formats and persistence

ASReview reads CSV, TSV, RIS and related citation exports, and can persist a
project archive/database with labels and model state. RECA should reuse readers
or fixture ideas selectively only when they add value. It must not import the
ASReview project archive as its project/data model or maintain a second
authoritative label history.

Model artifacts may be cached with training-data hash, component versions and
parameters for reproducibility, but they are derived and invalidated when the
candidate set or confirmed decisions change.

## API, CLI and Web UI

The CLI supports LAB, simulation, algorithm listing and project migration. The
full Web UI provides project setup, labeling history, collaboration, auth and
administration. RECA already owns project, membership, navigation, Artifact and
decision workflows, so adopting ASReview LAB would duplicate and conflict with
them. A narrow backend ranking component is the appropriate boundary.

## Tests

Upstream tests cover learners, classifiers, feature extraction, query strategy,
balancing, stopping, simulation, readers/writers, database/project state and web
APIs. The varied RIS/CSV fixtures and simulation patterns are valuable test
references. Any copied fixture requires a separate license/source check.

RECA needs golden tests ensuring rankings are reproducible for a fixed seed,
project isolation is enforced, only confirmed decisions train the model, and no
recommendation writes `LiteratureDecision` automatically.

## Operational requirements

Selective algorithm use needs Python/scikit-learn and bounded training on title
and abstract features. Full LAB adds Flask, auth, SQLAlchemy, a React application,
project archives and task management, all of which are unnecessary duplicate
runtime for the RECA competition flow.

## RECA current state

Literature screening is part of the existing REVIEW-P0 workflow. Active learning
is currently P1/enhancement behavior rather than Competition Core. ASReview is
not installed or integrated, and this phase does not change that scope.

## Recommended integration mode

`SELECTIVE_COPY + DIRECT_DEPENDENCY` for a narrowly chosen algorithm package or
small ranking component after a spike; otherwise `DESIGN_REFERENCE`.

Do not adopt the full ASReview LAB Web runtime. Prefer using stable public model
components directly before copying internals. Selective copying is justified
only where a small component cannot be consumed cleanly and attribution is
recorded.

## What to reuse

- active-learning loop and component separation;
- TF-IDF plus simple classifier baselines;
- top-down and uncertainty ranking strategies;
- simulation and stopping-evaluation methodology;
- RIS/CSV reader and model test ideas;
- reproducible seed/parameter handling.

## What not to reuse

- ASReview project archive/database as RECA state;
- full LAB UI, auth, collaboration or task manager;
- binary label as the complete RECA decision model;
- model recommendation as a final inclusion/exclusion;
- stopping suggestion as formal review completion;
- model state without candidate/decision lineage.

## Domain boundary

```text
RECA LiteratureRecord candidates
+ user-confirmed LiteratureDecision history
-> ASReview-style ranking component
-> ranked recommendation + score/explanation metadata
-> user review
-> RECA LiteratureDecision
```

The component is read-only with respect to formal decisions. It receives only
project-scoped candidate features and confirmed labels.

## Requirement and scope mapping

Use the existing REVIEW-P0 screening behavior to expose ordering and suggested
next records; do not add a Requirement ID. Active learning remains an optional
enhancement/P1 unless a later scope decision explicitly promotes an implementation
slice. A deterministic/simple ranking fallback can preserve the core demo.

## Milestone

- M3: optional validation spike and simple recommendation proof of concept.
- P1/enhancement after M3: active-learning ranking and stopping suggestions.

It is not required for Competition Core and should not block the basic manual
screening/evidence matrix.

## Risks

- recommendations mistaken for user decisions;
- full Web runtime duplicating RECA project/auth models;
- cold-start bias or insufficient positive/negative seeds;
- non-reproducible ranking without fixed versions/random seeds;
- imported labels with ambiguous semantics;
- model artifacts becoming stale after decisions change;
- feature text leaking across projects.

## Validation spike

On a licensed labeled corpus, compare random/manual ordering with TF-IDF plus
simple top-down and uncertainty strategies. Train only on confirmed RECA
decisions, record random seed/model versions, measure recall/work saved, test
zero/one-class seeds and verify the component has no write path to
`LiteratureDecision`.

## Attribution requirements

Preserve Apache-2.0 license and notices. Record exact package/version or copied
source paths and Commit. Dataset and fixture licenses must be reviewed separately
from the software license.

## Update strategy

Pin the smallest stable component and retain reproducibility tests. Avoid tracking
the full LAB release unless RECA deliberately adopts that product surface, which
is not recommended.
