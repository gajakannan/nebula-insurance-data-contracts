# Submission Lifecycle Pattern

Use the submission lifecycle pattern to model the business journey from intake through underwriting review, quote or indication, bind, decline, or withdrawal.

## Intent

Submissions are first-class because many submissions never become policies. The submission contract set should preserve intake context, applicant and producer participation, risk information, assessments, documents, and lifecycle events.

## Recommended Contracts

```text
Submission
SubmissionPartyRole
SubmissionRisk
SubmissionAssessment
SubmissionDocument
SubmissionLifecycleEvent
```

## Modeling Guidance

Keep the current submission status on `Submission` when it helps current-state access.

Capture meaningful changes as `SubmissionLifecycleEvent` records with event type, event date or datetime, effective date where applicable, reason code, actor or channel where known, and source-neutral narrative fields.

Use `SubmissionAssessment` for underwriting, triage, clearance, referral, declination, and other review outcomes that need their own result and rationale.
