# Architecture

## v0.3 components

| Component | Responsibility |
| --- | --- |
| `models.py` | Validate engagement, evidence fields, reliability and unique IDs. |
| `quality.py` | Calculate evidence age, exclude stale/future items and detect current metric conflicts. |
| `interviews.py` | Validate synthetic notes, normalize candidate claims and enforce attributable approval. |
| `interview_cli.py` | Export pre-review candidates and post-review evidence as separate artifacts. |
| `copilot.py` | Apply evidence gates, thresholds, recommendation and governance rules. |
| `report.py` | Render the same structured result as a cited Markdown memo. |
| `cli.py` | Read local JSON and write reproducible JSON and Markdown artifacts. |
| `site/` | Present the synthetic reference case without a server. |

## Data boundary

The public workflow reads local JSON files and writes local report files. It does not call a model, network service or company system. Interview normalization and human review are deliberately separate artifacts: the first always has an empty evidence register, and the second records reviewer provenance before approved observations are exported.

## Future boundary

Later rounds may add configurable thresholds, reviewer feedback, a local API and an optional grounded model adapter. Authentication, persistence, concurrency and monitoring are intentionally deferred.
