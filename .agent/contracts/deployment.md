# Release, deploy, and publish

## Actual repository capability

This is a local CLI. No hosted deployment target or deployment workflow is
configured. Installing dependencies or building a private workbook is not a
live deployment. `deploy` and `publish` must report this missing prerequisite
without inventing hosting, uploading finance data, or changing repository
settings. Adding deployment is separate implementation scope.

Source milestones use [release notes](../../docs/releases/) and Git tags; read
current history and live releases before choosing a version. Do not equate a
document named after a version with an existing tag or release. No package
publication pipeline is configured. Never attach private generated workbooks.

## Distinct meanings

**Release** manages version/notes/tag/artifact/release records applicable to an
explicitly requested source milestone. It does not inherently make it live.

**Deploy** follows the configured normal deployment process when one exists.
It requires scope, intended revision, target, normal checks, applicable
migration/health requirements, and rollback evidence. Respect provider and
external controls. Never silently switch to force publication.

**Publish** is explicit force publication. It is not a synonym for ordinary
Git push or source release. When a real target and authority exist:

1. Identify the normal deployment blocker and the owner of its control.
2. Classify the blocker as repository/process-controlled or externally enforced.
3. Bypass only eligible repository/deployment-process gates covered by the
   requested force-publication scope, using the minimum necessary force path.
4. Retain truthful failed/skipped verification statuses and record each bypass.
5. Verify the resulting revision and observed live state; distinguish failed
   deployment, rollback, and unverified acceptance.

Never bypass GitHub branch protection, Rulesets, externally required checks or
reviews, protected environment approvals, organization governance, hosting
protections, IAM, cloud policy, or equivalent external controls. Administrator
credentials do not change that boundary. Privacy and authorization requirements
are not eligible gates to bypass. Consult [authorization](authorization.md).
