# Failure Mode Analysis

| Scenario | System Behavior | Risk Level | Mitigation |
|--------|----------------|-----------|------------|
| Network loss mid-test | Session resumable | Low | Auto-save |
| Invalid input values | Rejected | High | Range validation |
| Double submission | Deduplicated | Medium | Idempotency keys |
| PDF generation failure | Error logged | Low | Retry |
| Red flag ignored | Block finalization | High | Mandatory review |
