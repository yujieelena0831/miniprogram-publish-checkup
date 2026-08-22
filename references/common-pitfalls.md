# Common Pitfalls

Apply only the checks relevant to the detected stack.

## Compiler And Base Library

- Verify modern JavaScript/TypeScript syntax against the project's compiler, Developer Tools settings, and target base library instead of applying blanket syntax bans.
- Test APIs and components against the declared minimum base library and provide fallbacks when required.

## Paths And Generated Output

- Check path case, extension resolution, framework aliases, npm output, subpackage boundaries, and ignored files.
- Do not inspect only framework source when WeChat uploads generated output; verify both build reproducibility and compiled artifacts.

## Components And Styling

- Prefer documented component variables and APIs before deep selector overrides.
- Test third-party components, pseudo-elements, safe areas, fonts, Canvas, and native components on real devices.
- Do not introduce TDesign-specific rules when the project does not use TDesign.

## Environment Drift

- Compare AppID, source root, backend URL, CloudBase environment, build mode, and version across local, experience, review, and production builds.
- Restart or clean Developer Tools caches when configuration changes are not reflected, then verify the actual compiled output.

## Identity And Permissions

- Distinguish WeChat identity, product accounts, phone verification, and business authorization.
- Test first authorization, denial, later authorization, revoked permission, expired session, and account deletion paths.

## CI And Secrets

- Keep upload keys and backend secrets out of source control and packages.
- Confirm CI IP rules, dependency versions, build commands, project path, robot number, and artifact retention.
- Require explicit authorization before previewing, uploading, deploying, submitting, or publishing.
