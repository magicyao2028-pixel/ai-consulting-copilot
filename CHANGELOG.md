# Changelog

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
