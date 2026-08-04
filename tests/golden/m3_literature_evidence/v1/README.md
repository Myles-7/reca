# M3 literature and evidence golden subset v1

This directory contains a deterministic RECA-authored synthetic acceptance fixture. It is not a
real paper and must never be presented as one. The fixture exists to test extraction structure,
EvidenceSpan location, history preservation, included-only analysis, and exactly-three topic source
constraints without redistributing a copyrighted publication or using production user data.

Source and reuse basis:

- author: RECA test maintainers;
- source: text embedded in `manifest.json`, generated specifically for repository tests;
- license/test basis: repository-authored synthetic fixture, redistributable with the repository;
- external content: none;
- personal or production data: none;
- annotation authority: deterministic human-authored expectations, not model output;
- parser modes: GROBID expectations model trusted coordinates; pypdf expectations require LOW,
  text-only degradation and no coordinates.

The formal 10-20 real-paper, double-reviewed golden collection required by the M3 metrics document
is not represented by this subset. Its absence is tracked in `M3_ISSUE_REGISTER.md`.
