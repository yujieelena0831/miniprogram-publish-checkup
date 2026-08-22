# Backend Selection And CloudBase

CloudBase is an optional Serverless backend platform, not a requirement for every Mini Program with backend needs.

## Select The Backend Mode

- Use CloudBase when the project chooses managed cloud functions, database, storage, identity, hosting, or related `wx.cloud` capabilities.
- Keep an existing custom backend when the product already depends on owned Node, Java, Python, PHP, Go, or third-party HTTPS services.
- Support hybrid systems when CloudBase and custom APIs serve different responsibilities.
- Do not migrate backend architecture merely to satisfy this skill.

## CloudBase Preflight

- Confirm the environment ID and separate development, test, and production resources.
- Initialize `wx.cloud` once at application startup when the project requires it.
- Verify cloud-function roots, deployed versions, runtime, dependencies, timeouts, logs, and permissions.
- Verify database security rules before allowing client reads or writes.
- Put privileged writes, cross-user access, secret-bearing integrations, and trusted validation in cloud functions or another trusted backend.
- Verify storage paths, ownership, access rules, upload limits, cleanup, and content-safety requirements.
- Use `cloud.getWXContext()` in trusted cloud code when WeChat identity is required.
- Treat OPENID as platform identity, not proof that the product never needs account linking, phone verification, membership, or another business login.
- Never hard-code SecretId, SecretKey, upload keys, or third-party API secrets in Mini Program code.

## Custom Backend Preflight

- Use HTTPS production endpoints and valid certificates.
- Confirm request, upload, download, and socket domains in the WeChat console as applicable.
- Keep authentication tokens scoped and revocable; never embed server secrets in the client.
- Verify production health, timeout/retry behavior, error responses, rate limits, logging, data migration, and rollback.

## Deployment Safety

- Inspect current resource state before changing CloudBase configuration.
- Obtain explicit authorization before creating environments, changing security rules, deploying functions, modifying production data, or enabling billing.
- Verify changes through logs, test calls, and an experience build.
- Consult current Tencent CloudBase documentation for supported runtimes, quotas, pricing, and deployment commands because these change over time.
