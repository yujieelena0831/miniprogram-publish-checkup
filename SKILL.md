---
name: miniprogram-publish-checkup
description: Determine whether a WeChat Mini Program project folder or ZIP is ready for submission or release, explain every blocking or uncertain reason, and give exact remediation. Use when a user provides only a Mini Program package and asks whether it can launch, pass review, comply, preview, upload, or publish; also use for project completeness, pages, components, routing, tabBar, package size, secrets, privacy, backend or CloudBase, filing, service categories, qualifications, real-device readiness, and release checkups.
---

# Mini Program Publish Checkup

## Default User Experience

Accept one project directory or ZIP as sufficient input. Do not start with a questionnaire. Inspect the package first, infer the framework, capabilities, backend, privacy surface, and applicable risk modules, then ask only for evidence that cannot exist in the package if the user wants the final uncertainty removed.

Answer these questions directly:

1. Can this package proceed to submission or release now?
2. If not, what exact evidence caused the decision?
3. What must change, where should it change, and how is the fix rechecked?

Read `references/package-only-decision.md` for the decision model, complete inspection surface, evidence rules, and report contract.

## Operating Contract

- Treat the project as backend-neutral. Detect local-only, CloudBase, custom HTTPS backend, or hybrid architecture before applying backend rules.
- Separate automated evidence from external evidence. Treat missing evidence as `UNKNOWN`, never as `PASS`. Do not claim that a Mini Program is compliant or guaranteed to pass review when required WeChat console, qualification, filing, privacy, backend availability, compiled-build, or real-device evidence is unavailable.
- Verify volatile platform limits and submission rules against current official sources at execution time. Treat script size limits as configurable safety targets, not permanent platform truth.
- Do not upload, submit for review, publish, change CloudBase resources, or modify production configuration without explicit user authorization.
- Preserve existing project conventions while remediating blockers. Do not impose CloudBase, a custom tab bar, or a specific visual style on every project.

## Checkup Workflow

1. Accept the supplied directory or ZIP. Run `scripts/inspect_package.py` first; it safely validates ZIP topology, finds the project root, runs structural and package checks, and produces the initial decision report.
2. Identify the project type, source root, build output, AppID, framework, backend mode, release target, and whether the input is source or generated output. Inspect `project.config.json`, `app.json`, pages, subpackages, components, tabBar, assets, private files, and environment configuration. Read `references/project-structure.md`.
3. For navigation or tabBar findings, read `references/navigation-and-tabbar.md`; validate routes, icons, custom component state, safe areas, and real-device behavior.
4. Classify the backend. For CloudBase or `wx.cloud`, read `references/backend-cloudbase.md`. For a custom backend, validate HTTPS endpoints, authentication, secrets, production availability, and configured request/upload/download/socket domains.
5. Run `scripts/estimate_package_size.py`. Inspect the main package boundary, subpackages, largest files, `packOptions.ignore`, generated output, server code, secrets, logs, documentation, and unused assets.
6. Read `references/release-compliance.md`. Inventory privacy-related capabilities, filing, subject, service categories, qualifications, content/operation risks, reviewer access, and required manual console evidence.
7. Read `references/debug-preview-upload.md`. Compile, preview, test on real devices, verify production dependencies, and prepare upload or review only to the level authorized by the user.
8. Return a release-gate report using `PASS`, `BLOCKER`, `WARNING`, `UNKNOWN`, and `NOT_APPLICABLE`. For every non-pass item include evidence, impact, exact remediation, owner when knowable, and a retest method.

## Route By Scenario

- Project completeness, broken routes, missing files, or handoff archive: read `references/project-structure.md` and run `scripts/audit_miniprogram.py`.
- TabBar, custom navigation, icon, or page-switching issue: read `references/navigation-and-tabbar.md`.
- Package too large or unexpected upload files: run `scripts/estimate_package_size.py` and inspect package boundaries.
- CloudBase, `wx.cloud`, cloud functions, cloud database, cloud storage, or OPENID: read `references/backend-cloudbase.md`.
- Custom Node, Java, Python, PHP, Go, or third-party backend: keep CloudBase rules inactive and validate the HTTPS API path instead.
- Privacy, filing, category, qualification, review, or compliance request: read `references/release-compliance.md` and verify current official requirements.
- Preview, experience build, CI, upload, or release: read `references/debug-preview-upload.md`.
- Compatibility or difficult runtime issue: read `references/common-pitfalls.md` only for the technologies actually present.

## Automation

Run the package-first inspection for either a ZIP or directory:

```bash
python3 ~/.codex/skills/miniprogram-publish-checkup/scripts/inspect_package.py /path/to/project-or.zip
```

Run the structural preflight:

```bash
python3 ~/.codex/skills/miniprogram-publish-checkup/scripts/audit_miniprogram.py /path/to/project
```

Run the package estimate:

```bash
python3 ~/.codex/skills/miniprogram-publish-checkup/scripts/estimate_package_size.py /path/to/project
```

Treat script outputs as package evidence, not proof of platform approval. WeChat Developer Tools remains authoritative for the compiled upload result, dependency analysis, preview, and real-device behavior.

## Release Gate

Use three top-level decisions:

- `BLOCKED`: package evidence proves that submission or release should stop.
- `PACKAGE_CHECK_PASSED_EXTERNAL_CONFIRMATION_REQUIRED`: no package blocker was found, but facts outside the package remain unknown.
- `READY_FOR_SUBMISSION_OR_RELEASE`: no blocker remains and all required external, compiled-build, backend, real-device, and platform evidence has been supplied and verified.

Do not describe the project as ready to publish until:

- No automated `BLOCKER` remains.
- The project compiles from the correct source/build root.
- Core user journeys pass on an experience build and real devices.
- Production backend or CloudBase dependencies are reachable and correctly separated from development resources.
- Package boundaries and current platform limits are confirmed.
- Privacy declarations match actual APIs and collected data.
- Filing, subject, service category, and required qualifications are confirmed with current evidence from the relevant official console.
- Reviewer instructions and any required test account work without developer assistance.

## Handoff

Report:

- Overall gate: ready for preview, ready for review, ready for release, or blocked.
- Findings grouped by `BLOCKER`, `WARNING`, and `UNKNOWN`.
- Checks executed and evidence obtained.
- Items that require WeChat Developer Tools, WeChat Public Platform, CloudBase console, or real-device confirmation.
- For every non-pass item: why it matters, evidence, affected location, exact fix, and retest.
- The smallest next user action. Never imply that automated inspection replaces platform review or regulatory approval.
