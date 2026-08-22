# Release Compliance And Filing

Use this as a release gate, not as a substitute for legal advice, WeChat review, or regulatory approval. Verify current requirements through official consoles and primary sources each time.

## Subject, Category, And Qualifications

- Confirm the registered subject and administrator information are valid.
- Match the Mini Program name, icon, description, service categories, review pages, and actual functionality.
- Identify functions that require special categories, licenses, or prior approvals. Do not guess qualification eligibility.
- Remove hidden, unfinished, test-only, or out-of-category functionality from the submitted build.

## Filing

- Confirm whether Mini Program/APP filing is required and completed for the intended mainland China service.
- Distinguish Mini Program/APP filing from website or backend-domain ICP filing and from industry-specific licenses.
- Match the filing subject, service name, domain/network resources, and actual operation.
- Confirm the filing number is displayed and linked as currently required.
- Treat filing status, changes, cancellation, and special-industry approvals as manual official-console checks.

Primary filing basis: [MIIT notice on mobile internet application filing](https://www.gov.cn/zhengce/zhengceku/202308/content_6897341.htm?type=mobile-internet).

## Privacy And Personal Information

- Inventory actual APIs, components, forms, SDKs, logs, and backend fields that collect or process personal information.
- Make the platform privacy-protection guide match the actual information types and purposes.
- Obtain consent before calling capabilities that require it; provide a usable denial path for nonessential information.
- Check minimization, retention, deletion, account cancellation, third-party sharing, cross-device identity, and minor-related requirements where applicable.
- Test privacy behavior in the experience build and formal build; static detection may miss indirect component or SDK usage.

Current Tencent guidance summarizing WeChat privacy adaptation: [Mini Program privacy-protection guide adaptation](https://cloud.tencent.cn/document/product/1301/97930).

## Content And Operations

- Confirm the submitted application is complete, stable, and consistent with its description.
- Check illegal content, infringement, misleading claims, forced or induced sharing, abusive redirects, and unavailable services.
- For user-generated content, payments, healthcare, education, finance, news, live streaming, minors, AI, location, camera, microphone, or similar sensitive capabilities, load the current applicable platform and legal rules.
- Provide reporting, moderation, refund, customer-service, or account-management paths when the business requires them.

## Security And Production Configuration

- Remove private keys, API secrets, upload credentials, debug endpoints, local addresses, and privileged admin tools from the client package.
- Confirm production domains, certificates, backend authentication, authorization, database rules, storage rules, logging, monitoring, backups, and rollback.
- Verify that reviewer access does not expose real user data or production administration.

## Manual Evidence Required

Record screenshots or status from the WeChat Public Platform and relevant official consoles for filing, service categories, qualifications, privacy declarations, configured domains, submitted version, and review status. Mark missing evidence as `UNKNOWN`, not `PASS`.
