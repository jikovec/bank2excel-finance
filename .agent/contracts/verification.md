# Verification contract

Classify every relevant check exactly once:

| Status | Meaning |
| --- | --- |
| passed | Executed against the relevant state and met its criteria. |
| failed | Executed and contradicted a criterion. |
| blocked/unavailable | Could not execute or complete, including missing dependencies. |
| intentionally bypassed | An applicable check was deliberately skipped under valid scope/authority. |
| not required | Does not apply to this task or repository capability. |

An unexecuted check is never passed. Include exact command/target, relevant
revision, outcome, and limitations. A command failing to import a missing
package is unavailable execution, not passing application validation.

Choose the strongest proportionate native evidence. For documentation and
agent infrastructure use [private-safe validation](../workflows/private-safe-validation.md).
For behavior changes use focused, input-independent synthetic regressions where
possible. Do not create a test that merely restates implementation or weaken a
criterion to pass. Rerun affected checks after repairs; expand only for a new
change, failure, or unresolved concern.

Separate structural metadata/link checks from semantic routing review and real
provider discovery. No CI configuration means no hosted CI result, not a green
pipeline. Local tests, remote checks, merge, release artifacts, deployment
identity, and live acceptance are different evidence. Check current remote
state before claiming completion of a remote operation.
