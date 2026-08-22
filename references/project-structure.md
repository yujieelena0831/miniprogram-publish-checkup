# Project Structure And Completeness

Use this reference for native Mini Programs and adapt paths for Taro, uni-app, or other generated projects.

## Identify The Correct Root

- Locate `project.config.json` before auditing files.
- Resolve `miniprogramRoot`; do not confuse framework source with generated Mini Program output.
- Confirm `compileType`, AppID, build commands, npm output, subpackages, plugins, and cloud-function roots.
- For an archive, verify that extraction produces the expected project root without an accidental extra directory layer.

## Required Runtime Graph

- Parse `app.json` and verify every declared page and subpackage page exists.
- For native pages, require `.json`, `.wxml`, `.wxss`, and one script entry such as `.js` or `.ts` unless the framework build output has a documented alternative.
- Parse global and page-level `usingComponents`; verify local component paths and companion files.
- Verify tabBar routes, custom-tab-bar files, plugin declarations, workers, sitemap, theme, and referenced local assets when present.
- Check path case exactly. Case-insensitive local development can hide production failures.

## Source Package Versus Upload Package

- A handoff source package must contain source, necessary configuration, lockfiles, reproducible build instructions, and non-secret environment examples when the project requires a build.
- A WeChat upload package is produced by WeChat Developer Tools or `miniprogram-ci`; do not treat an arbitrary ZIP as the authoritative compiled upload result.
- Exclude private keys, upload credentials, `.env` files, logs, server-only code, editor caches, temporary output, unrelated documentation, and unused assets.
- Do not exclude files imported by the Mini Program runtime merely to reduce the estimate.

## Backend Classification

Classify before applying backend checks:

- Local-only: no remote persistence or trusted server logic.
- CloudBase: `wx.cloud`, cloud functions, cloud database, cloud storage, or CloudBase environment configuration.
- Custom backend: `wx.request`, uploads, downloads, or sockets targeting owned/third-party HTTPS services.
- Hybrid: both CloudBase and custom services.

Confirm that secrets and privileged operations stay off the Mini Program client for every backend mode.
