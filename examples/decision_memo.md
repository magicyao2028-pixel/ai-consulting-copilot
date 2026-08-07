# Evidence-Backed Decision Memo

**Question:** Should a regional retailer run an AI-assisted customer-service pilot?
**Status:** recommendation_ready
**Confidence:** medium

## Executive decision

Run a 30-day assistive customer-service pilot with human approval gates.

## Findings

- The synthetic support operation handles 4200 contacts per month. [E-01]
- Repetitive intents represent 61% of contacts, creating a bounded assistive use case. [E-02]
- First response currently takes 11.8 hours, above the eight-hour pilot threshold. [E-03]

## Options

- Keep the current manual workflow and continue measuring the baseline. [E-01] [E-02] [E-03]
- Run a narrow assistive pilot for repetitive intents; recommended. [E-01] [E-02] [E-03]
- Fully automate replies; rejected because current evidence does not support that risk. [E-01] [E-02] [E-03] [E-04]

## Recommendations

- Run a 30-day assistive customer-service pilot with human approval gates. [E-01] [E-02] [E-03]
- Keep sensitive-data filtering and human approval as release gates. [E-04]

## Risks

- Customer messages may contain sensitive data, so raw text must not enter an uncontrolled model path. [E-04]

## 30-day pilot plan

- **Days 1-5:** Confirm baseline definitions, approved intents and privacy gate.
- **Days 6-15:** Run shadow-mode suggestions against synthetic or approved test cases.
- **Days 16-25:** Review exceptions, false routing and reviewer overrides.
- **Days 26-30:** Compare against the baseline and make a human go/no-go decision.

## Evidence controls

- Citation coverage: 9/9 (100.0%)
- Ignored unverified evidence: E-05
- Human approval required: yes

## Evidence register

- **[E-01] Synthetic monthly support register** — The demonstration operation receives 4,200 support contacts per month. (internal_record, verified, 2026-07-31)
- **[E-02] Synthetic intent review** — The three most repetitive intents represent 61 percent of contacts. (internal_record, verified, 2026-07-31)
- **[E-03] Synthetic service baseline** — Median first response is 11.8 hours for the scoped channels. (internal_record, verified, 2026-07-31)
- **[E-04] Synthetic privacy review** — Customer messages can contain payment-card fragments, email addresses and passwords. (policy, verified, 2026-07-29)
- **[E-05] Unverified vendor marketing claim** — A vendor claims a 40 percent cost reduction without a reproducible method. (external_benchmark, unverified, 2026-07-20)

_Public demonstration data is synthetic. This memo is not a production outcome claim._
