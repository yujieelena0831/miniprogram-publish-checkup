# Debug, Preview, Upload, And Release

## Local And Simulator Gate

1. Open the directory containing `project.config.json` in WeChat Developer Tools.
2. Confirm AppID, source root, base library, npm build state, plugins, and environment configuration.
3. Compile from a clean start and inspect console, network, storage, performance, and dependency-analysis panels.
4. Exercise ready, loading, empty, error, permission-denied, session-expired, and retry states.

## Experience Build And Real Devices

- Create an experience build before review.
- Test the first launch, cold start, foreground return, weak network, offline recovery, and denied permissions.
- Cover iOS and Android plus representative screen sizes.
- Test direct entry paths, sharing, scans, uploads, downloads, sockets, payments, and background behavior when present.
- Verify that development-only domains, bypass flags, test accounts, mock data, and local addresses are absent from production configuration.

## miniprogram-ci

- Use `miniprogram-ci` when automated preview, upload, npm build, or cloud-function upload is required.
- Confirm AppID, project path, upload key, robot number, IP allowlist, version, and description.
- Store upload keys in a secret manager or protected CI secret. Never commit them or place them in the Mini Program package.
- Pin and review the dependency version used by CI; do not silently introduce an unreviewed latest version into an existing release pipeline.
- Treat preview/upload as an external state change. Obtain explicit authorization before running it.

## Review Preparation

- Confirm the submitted build is functionally complete rather than a demo or placeholder.
- Match review pages and service categories to the actual functionality.
- Provide concise reviewer instructions, entry path, required permissions, and a working test account when login blocks access.
- Ensure required backend data exists and does not depend on developer assistance.
- Re-run core journeys after upload and again after formal release.

## Evidence

Record the tool/version, build version, environment, devices tested, package result, test paths, unresolved manual items, and review/release status. Do not claim review approval before the platform grants it.
