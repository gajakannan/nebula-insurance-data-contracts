# Submission Modeling

## Decision

Model submission as a first-class area rather than treating it as an incomplete policy.

## Rationale

Many submissions never become policies. Submission data also contains distinct producer, applicant, intake, risk, document, and underwriting context that should not be lost or forced into issued-policy contracts.

## Consequences

Use submission contracts for intake and underwriting context:

```text
Submission
SubmissionPartyRole
SubmissionRisk
SubmissionAssessment
SubmissionDocument
SubmissionLifecycleEvent
```

Link submissions to policies when a submission becomes bound or issued, but do not require every submission to produce a policy.

See `references/patterns/pc/submission-lifecycle-pattern.md`.
