# Changelog

## 0.7.0 - 2026-08-27

- added a conflict-triage work item derived from the validated adjudication receipt;
- exposed decision-specific next actions while keeping evidence blocked and changes unapplied;
- extended trial and regression evidence without adding model, provider or external-action paths.

## 0.6.0 - 2026-08-24

- added an accountable conflict-adjudication receipt with reviewer alias, conflict evidence IDs, rationale and explicit decision;
- supported `retain_block`, `request_recollection` and `reconcile` as recorded human decisions without automatic evidence promotion or memo mutation;
- added a synthetic conflict fixture, validation tests and trial-readiness coverage;
- expanded the evidence index to eight claims while preserving abstention, citation and human go/no-go boundaries.

## 0.5.0 - 2026-08-20

- added a deterministic evidence-to-claim-to-decision lineage graph;
- blocked unknown and decision-ineligible citations while retaining excluded evidence for audit;
- added reproducible JSON/Markdown lineage reports, focused tests and a clean reviewer trial;
- screened OpenLineage and NetworkX without forcing unnecessary infrastructure or dependencies;
- linked a synthetic citation-integrity requirement to implementation and regression evidence.

## 0.4.0 - 2026-08-16

- added validated, named decision-threshold scenarios and a zero-dependency comparison CLI;
- compared multiple policy choices against one governed evidence register and exposed decision sensitivity;
- preserved stale, future-dated, unverified and contradiction gates across every scenario;
- kept normalized interview candidates outside scenario evidence and recorded the evidence IDs used;
- added a deterministic three-scenario fixture, reproducible output and focused regression tests.
- rejected non-finite threshold values before they can affect policy comparisons or JSON output.

## 0.3.0 - 2026-08-12

- added validated synthetic interview notes with consent and claim-kind controls;
- added deterministic normalization into pending candidate claims with an empty evidence register;
- added attributable human review decisions and provenance for approved observations;
- blocked opinions and requests from evidence promotion even when incorrectly marked approved;
- preserved freshness and contradiction gates for approved interview metrics and expanded the suite to 21 tests.

## 0.2.0 - 2026-08-08

- added explicit analysis dates and validated ISO evidence dates;
- added source-specific freshness windows with stale and future-dated exclusions;
- added material contradiction detection for duplicate current metrics;
- blocked recommendations until conflicting evidence is reconciled;
- expanded JSON/Markdown quality evidence and increased the suite to 13 tests.

## 0.1.0 - 2026-08-07

- added validated engagement and evidence models;
- added evidence-quality gates, deterministic pilot thresholds and abstention;
- added cited findings, options, risks, recommendations and a 30-day plan;
- excluded unverified evidence from recommendation logic;
- added JSON and Markdown reports, seven tests, CI and a static case page.
