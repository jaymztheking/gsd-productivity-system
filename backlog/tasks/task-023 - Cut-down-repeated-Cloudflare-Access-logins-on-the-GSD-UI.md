---
id: TASK-023
title: Cut down repeated Cloudflare Access logins on the GSD UI
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-17 15:52'
updated_date: '2026-11-17 16:02'
labels:
  - cloudflare
  - security
  - ux
dependencies:
  - TASK-004
references:
  - README.md
  - k8s/cloudflared/configmap.yaml
priority: medium
type: chore
ordinal: 18000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-004 put gsd.medaughsolutions.com behind Cloudflare Access, using the Cloudflare one-time-PIN identity provider and the default Access session duration. Using it from a phone on cellular, the user reported "a lot of Cloudflare login pages": the PIN flow plus a short session means re-entering an emailed code often. A capture and review tool that keeps asking for a login is one people stop opening, so this should be fixed before relying on GSD remotely every day. Two levers exist, raising the Session Duration on the GSD Access application and switching the identity provider from one-time PIN to Google, and they can be combined. Access settings live in the Cloudflare Zero Trust dashboard, not in this repo, so whatever is chosen has to be written down in the README Remote Access section to stay discoverable. Only gsd.medaughsolutions.com is in scope. capture.medaughsolutions.com is deliberately not behind Access (iOS Shortcuts cannot complete SSO) and must stay that way.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 After a successful login, the GSD UI on a phone stays signed in for the chosen session length without another Access prompt
- [ ] #2 Access still restricts the UI to the intended account(s), and a logged-out or unauthorised visitor is still stopped at the Cloudflare edge
- [ ] #3 capture.medaughsolutions.com/webhook/capture is still not behind Access and a Shortcut capture still succeeds
- [ ] #4 The README Remote Access section records the identity provider, session duration and policy now applied to gsd.medaughsolutions.com, and why
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Decisions (user, 2026-11-17): add Google as a login method, set sessions to 1 month. User opens GSD in Chrome on iOS (a normal browser tab, so the iOS home-screen web app cookie isolation does not apply).

The user does steps 1-3 because the secrets and dashboards are theirs. The Google client secret goes straight into the Cloudflare dashboard and never through the agent transcript.

1. Google Cloud Console: OAuth consent screen (External, add james.medaugh@gmail.com as a test user), then an OAuth client ID of type Web application with origin https://proud-wind-167f.cloudflareaccess.com and redirect URI https://proud-wind-167f.cloudflareaccess.com/cdn-cgi/access/callback
2. Zero Trust > Settings > Authentication: add Google as a login method, paste the client ID and secret, run Test. Set Global session timeout to 1 month.
3. Access application for gsd.medaughsolutions.com: enable Google, keep One-time PIN as a fallback, confirm the Allow policy matches the Google account email, set Session Duration to 1 month.
4. Verify from outside: an unauthenticated request to the UI host still gets 302 to Access; capture.medaughsolutions.com/webhook/capture still reaches n8n (403 without a token rather than an Access redirect); user confirms a Google login on the phone and a Shortcut capture.
5. Document the login methods, session lengths, policy and reasoning in the README Remote Access section.
<!-- SECTION:PLAN:END -->
