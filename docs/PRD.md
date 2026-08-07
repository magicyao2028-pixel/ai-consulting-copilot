# Product Requirements Document

## Product and user

AI Consulting Copilot v0.1 supports an operations or transformation lead in a small or medium-sized business. It prepares a reviewable decision memo; it does not make or execute the decision.

## Problem

AI pilot discussions often mix internal facts, assumptions and vendor claims. Decision owners need to know which evidence supports each conclusion, what is missing and where a human must approve.

## In scope

1. Validate one structured engagement and evidence register.
2. Require support volume, repetitive-intent share and response-time baselines.
3. Exclude evidence labelled unverified from recommendation logic.
4. Produce cited findings, options, risks and recommendations.
5. Produce a 30-day pilot plan and explicit governance gates.
6. Abstain when a required metric is missing.

## Out of scope

- autonomous research, interviews or web browsing;
- real company data, financial approval or ROI guarantees;
- automatic procurement, customer communication or workflow execution;
- independent verification of input reliability labels.

## Release gate

The sample must pass all tests, use synthetic data, cite every generated claim, exclude `unverified` evidence from decision logic and issue no recommendation when a required metric is absent.
