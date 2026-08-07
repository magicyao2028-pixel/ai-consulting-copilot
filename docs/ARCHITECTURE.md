# Architecture

## v0.1 components

| Component | Responsibility |
| --- | --- |
| `models.py` | Validate engagement, evidence fields, reliability and unique IDs. |
| `copilot.py` | Apply evidence gates, thresholds, recommendation and governance rules. |
| `report.py` | Render the same structured result as a cited Markdown memo. |
| `cli.py` | Read local JSON and write reproducible JSON and Markdown artifacts. |
| `site/` | Present the synthetic reference case without a server. |

## Data boundary

The public workflow reads one local JSON file and writes local report files. It does not call a model, network service or company system. The structured JSON is the source of truth; Markdown and the static site are presentation layers.

## Future boundary

Later rounds may add contradiction detection, freshness, configurable thresholds, reviewer feedback, a local API and an optional grounded model adapter. Authentication, persistence, concurrency and monitoring are intentionally deferred.
