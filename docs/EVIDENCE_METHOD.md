# Evidence Method

## Reliability labels

- `verified`: accepted as checked within the synthetic engagement package;
- `indicative`: usable for direction with visible uncertainty;
- `unverified`: preserved in the register but excluded from recommendations.

These labels describe input governance, not independent auditing by the program.

## Decision gate

v0.4 requires three metrics: monthly support volume, repetitive-contact share and first-response hours. A pilot recommendation is only available when all three are usable. The default thresholds are 1,000 contacts, 40 percent repetitive share and eight response hours. They are explicit configuration, not universal standards.

Scenario comparison changes only those declared thresholds. It reuses the same eligible metric selections and reports whether the outcome changes. Missing, conflicted, stale, future-dated or unverified evidence cannot be made eligible by selecting a more permissive scenario.

## Interview claim gate

Structured synthetic statements are classified as observations, opinions or requests. Normalization creates review candidates only. An attributable human decision may promote an observation into the register as `indicative`; opinions and requests cannot be promoted by this workflow. Approved interview metrics then pass through the normal freshness and contradiction controls.

## Freshness gate

The engagement supplies an explicit `analysis_date`. Current prototype windows are 60 days for internal records, 90 for interviews, 365 for policies and 180 for external benchmarks. Future-dated and stale items remain visible in the evidence register but cannot support a decision.

## Contradiction gate

Current eligible items for the same metric conflict when their units differ or their numeric spread exceeds 10 percent of the largest absolute value. A material conflict produces `evidence_conflict` and no recommendation. Values inside tolerance are resolved deterministically by reliability, collection date and evidence ID.

## Citation control

Findings, options, recommendations and risks are stored as claim objects with evidence IDs. Citation coverage measures whether a claim has an ID, not whether the underlying evidence is true. Tests additionally confirm that cited IDs exist in the register.
