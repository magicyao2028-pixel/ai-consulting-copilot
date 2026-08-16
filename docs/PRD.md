# Product Requirements Document

## Product and user

AI Consulting Copilot v0.4 supports an operations or transformation lead in a small or medium-sized business. It prepares a reviewable decision memo and compares declared policy scenarios; it does not make or execute the decision.

## Problem

AI pilot discussions often mix internal facts, assumptions and vendor claims. Decision owners need to know which evidence supports each conclusion, what is missing and where a human must approve.

## In scope

1. Validate one structured engagement and evidence register.
2. Require support volume, repetitive-intent share and response-time baselines.
3. Exclude evidence labelled unverified from recommendation logic.
4. Produce cited findings, options, risks and recommendations.
5. Produce a 30-day pilot plan and explicit governance gates.
6. Abstain when a required metric is missing.
7. Exclude stale and future-dated evidence using explicit source-specific windows.
8. Stop recommendation when current evidence for one metric materially conflicts.
9. Normalize consented synthetic interview statements into pending candidate claims.
10. Require a named reviewer, decision date and rationale before an observation enters the evidence register.
11. Prevent opinions and requests from being promoted as evidence.
12. Validate configurable decision thresholds and compare at least two declared scenarios against the same evidence register.
13. Show whether the recommendation changes across scenarios without allowing thresholds to bypass evidence-quality gates.

## Out of scope

- interview recording, transcription, autonomous research or web browsing;
- real company data, financial approval or ROI guarantees;
- automatic procurement, customer communication or workflow execution;
- independent verification of input reliability labels.

## Release gate

The sample must pass all tests, use synthetic data, cite every generated claim, keep normalized candidates outside the evidence register until human approval, exclude unverified/stale/future evidence from decision logic and issue no recommendation when a required metric is absent or current evidence conflicts. Scenario comparison must reuse the same evidence register, expose its thresholds and remain blocked by those same evidence gates.
