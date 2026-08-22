# Package-Only Decision Model

Use this reference whenever the user supplies a project directory or ZIP and expects a release decision without completing a questionnaire.

## First Principle

A release is safe only when identity and scope, artifact integrity, runtime correctness, external dependencies, platform and legal eligibility, reviewer reproducibility, controlled release, and post-release recovery are all supported by evidence. A package can prove some of these facts and reveal risks in others; it cannot prove private console state or future platform approval.

Never convert absence of evidence into success. Infer applicable checks from the package, minimize user effort, and report the smallest external evidence needed to remove each uncertainty.

## Complete Inspection Surface

Inspect every applicable category:

1. **Identity and scope**: AppID, project root, framework, source versus generated output, version clues, build mode, target environment, and accidental test identity.
2. **Archive and artifact integrity**: readable archive, safe paths, symlinks, duplicate or nested roots, macOS junk, required configuration, lockfiles, build scripts, generated output, ignored and included files, sensitive files, server-only files, and reproducibility clues.
3. **Runtime graph**: app entry, pages, subpackages, components, plugins, workers, sitemap, themes, assets, exact path case, npm output, and framework aliases.
4. **Navigation and UI shell**: initial route, all navigation targets, tabBar, custom tab bar, icons, direct entry, share and scan entry, safe area, and failure-state escape paths.
5. **Package boundaries**: main package, every subpackage, aggregate size, largest files, duplicate or unused assets where detectable, misplaced backend data, and current official upload limits.
6. **Build and compatibility**: clean build instructions, dependency lock, Developer Tools compile evidence, base library, deprecated or unsupported APIs, npm build, platform differences, startup, memory, and performance budgets.
7. **Backend and external services**: local-only, CloudBase, custom HTTPS, or hybrid; production environment; domains and certificates; authentication and authorization; secrets; database and storage rules; health, timeout, retry, rate limits, quotas, payment or third-party services, migrations, backup, and degradation.
8. **Privacy and data**: direct and wrapped APIs, components, SDKs, forms, permissions, backend fields, logs, consent timing, denial path, minimization, retention, deletion, account cancellation, sharing, minors, and agreement with the platform privacy guide.
9. **Subject and regulatory eligibility**: subject, administrator, Mini Program or APP filing, filing display, domain ICP relationship, service categories, industry qualifications, names and descriptions, validity and expiry. These usually require external evidence.
10. **Content and operations**: completeness, prohibited or misleading content, copyright, UGC moderation and reporting, customer service, payments and refunds, advertising, induced sharing, remote behavior changes, and scenario-specific rules for healthcare, education, finance, news, live streaming, minors, AI, location, camera, or microphone.
11. **Reviewer reproducibility**: working account and verification path, reviewer instructions, stable data, hidden entry points, permissions, and consistency between submitted features, description, screenshots, categories, and qualifications.
12. **Release control and survival**: version-to-commit and artifact identity, approval, staged release, rollback trigger and target, data rollback, monitoring, alert owner, observation window, backup and restore evidence, incident response, and user-support ownership.

Load current official rules for categories detected from code or configuration. Do not load every industry module indiscriminately.

## Evidence Classes

- `PACKAGE`: directly observed in supplied files.
- `DERIVED`: reproducible result of a local script or build.
- `RUNTIME`: Developer Tools, experience build, device, or backend test result.
- `PLATFORM`: current WeChat Public Platform or CloudBase console evidence.
- `LEGAL_OR_OPERATIONAL`: qualification, licensing, ownership, moderation, support, or release-owner evidence.

For volatile platform facts, record the official source and verification date. For screenshots or user statements, say exactly what was and was not independently verified.

## Status And Decision Rules

- `PASS`: positive evidence satisfies a defined pass condition.
- `BLOCKER`: evidence proves a submission or release condition fails.
- `WARNING`: not an immediate blocker, but a concrete quality, security, or operational risk exists.
- `UNKNOWN`: required evidence is unavailable or the check cannot be completed from the package.
- `NOT_APPLICABLE`: inspected context proves the check does not apply; never use this merely because evidence is missing.

Decision precedence:

1. Any `BLOCKER` => `BLOCKED`.
2. No blocker but one or more required `UNKNOWN` => `PACKAGE_CHECK_PASSED_EXTERNAL_CONFIRMATION_REQUIRED`.
3. Only verified required checks may produce `READY_FOR_SUBMISSION_OR_RELEASE`.

Static inspection alone can never produce the third decision because compile, real-device, platform, and operational evidence exist outside the package.

## Finding Contract

Every non-pass finding must contain:

- unique code and category;
- status and affected release stage;
- observed evidence and location;
- why it blocks or creates risk;
- exact remediation, avoiding vague phrases such as “check configuration”;
- retest method and pass condition;
- evidence class;
- owner if it can be inferred;
- verification time or expiry when volatile.

Do not overwhelm the user with the full checklist. Lead with the decision, then blockers ordered by release impact, warnings, unknown external facts, and the shortest route to the next gate.

## Report Contract

Return:

1. **Decision**: one of the three top-level decisions, in plain language.
2. **Scope**: package path/name, detected root, framework, AppID presence, backend mode, routes, and package totals.
3. **Blockers**: reason, evidence, location, exact fix, and retest.
4. **Warnings**: concrete risk and recommended fix.
5. **External confirmations**: only facts that cannot be proven from the package, each with the exact console page or evidence requested when known.
6. **Passed evidence**: concise list of important verified checks.
7. **Next gate**: the smallest next action, such as fix package blockers, compile an experience build, or supply platform screenshots.

Never say “can publish” when the actual conclusion is only “no static package blocker found.”
