---
id: TASK-023
title: Cut down repeated Cloudflare Access logins on the GSD UI
status: Done
assignee:
  - '@claude'
created_date: '2026-11-17 15:52'
updated_date: '2026-11-17 16:59'
labels:
  - cloudflare
  - security
  - ux
dependencies:
  - TASK-004
references:
  - README.md
  - k8s/cloudflared/configmap.yaml
modified_files:
  - README.md
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
- [x] #2 Access still restricts the UI to the intended account(s), and a logged-out or unauthorised visitor is still stopped at the Cloudflare edge
- [x] #3 capture.medaughsolutions.com/webhook/capture is still not behind Access and a Shortcut capture still succeeds
- [x] #4 The README Remote Access section records the identity provider, session duration and policy now applied to gsd.medaughsolutions.com, and why
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-17: Google login method added in Zero Trust. First Test returned "unable to find the requested identity provider", which is Cloudflare failing to find an IdP id that did not exist yet, not a Google error. Testing from the saved Login methods list passed and returned the user name and email. If this reappears: save first, then test from the list.

2026-11-17: User set Google + One-time PIN on the GSD Access app, policy Emails = james.medaugh@gmail.com, application session and global session timeout 1 month. Phone (Chrome on iOS, cellular not specified) now goes to Google account selection instead of the Cloudflare PIN page and lands in the GSD UI.

External checks after the change: / and /api/next-actions on gsd.medaughsolutions.com both 302 to proud-wind-167f.cloudflareaccess.com; POST capture.medaughsolutions.com/webhook/capture with no token 403 (n8n header auth, no Access redirect); capture /rest/login 404.

README: added "Access login and session length" under Remote Access.

2026-11-17 user verification: a Shortcut capture after the change arrived in the inbox (user then deleted it), so the capture hostname is still outside Access. Signing in with a different Google account (medaughsolutions@gmail.com) was refused with "That account does not have access", so the policy restricts entry, not the login method.

AC #1 not yet proven: the 1-month application and global sessions are set, but staying signed in for that long can only be observed over time.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Replaced the one-time-PIN login with Google on the gsd.medaughsolutions.com Access application, keeping PIN as a fallback, and raised both the application session and the Zero Trust global session to 1 month. The user had reported "a lot of Cloudflare login pages"; the phone now goes to Google account selection and into the UI in one step. The settings live in the Cloudflare dashboard, so the README Remote Access section now records the login methods, policy (Emails = james.medaugh@gmail.com), session lengths, the Google OAuth redirect URI, and why.

Verified: unauthenticated / and /api/next-actions on the UI host 302 to Access; a different Google account (medaughsolutions@gmail.com) is refused with "That account does not have access"; capture.medaughsolutions.com/webhook/capture still returns 403 from n8n without a token, with no Access redirect, and a real Shortcut capture arrived in the inbox; /rest/login on the capture host is still 404.

AC #1 is left unchecked on purpose: the 1-month session is configured but can only be confirmed by going that long without a prompt. If Access prompts again sooner, check both session settings first.
<!-- SECTION:FINAL_SUMMARY:END -->
