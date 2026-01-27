# Change Management Policy

## Purpose
To ensure controlled, traceable, and compliant changes to Neurova Clinical Engine.

## Change Categories

### Minor Changes
- UI text changes
- Non-clinical copy updates
- Bug fixes without impact on scoring or data flow

**Action**:
- Internal documentation
- Version bump (patch)

### Major Changes
- Scoring logic changes
- Test instrument changes
- Consent text changes
- Report wording affecting clinical interpretation

**Action**:
- Formal review
- Re-validation
- Regulatory assessment prior to release

## Versioning
- All releases are versioned
- Scoring logic is immutable per version

## Prohibited Changes
- Silent modification of scoring rules
- Modification of historical reports
