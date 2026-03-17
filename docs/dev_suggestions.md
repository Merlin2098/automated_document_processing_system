# Legacy Maintenance Notes

## Operating Context

This repository currently runs in a **legacy** mode. The architecture has been stabilized, and large structural changes may reduce performance or introduce regressions in processing behavior.

## Document Format Changes

If you need to adjust how PDF data is read or extracted after upstream format changes:

- Edit the extractors in `extractores/` directly.
- Avoid moving or renaming modules in that folder unless there is a critical reason to do so.

## Performance Warning

Historically, aggressive refactors have caused performance regressions that were difficult to recover from.

- **Principle:** if the current implementation is stable and fast, do not refactor it without evidence.
- Any restructuring should be justified with metrics and before-versus-after comparisons.

## Practical Rule

> If it is not broken, do not redesign it.

Before changing the architecture:

1. Measure the current baseline.
2. Make the smallest possible change.
3. Measure again and compare results.
