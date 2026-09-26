---
id: TASK-005
title: Rework the Siri Shortcut to capture over public HTTPS from any network
status: Done
assignee:
  - '@James'
created_date: '2026-09-25 18:10'
updated_date: '2026-09-26 07:06'
labels:
  - shortcuts
  - ios
  - capture
dependencies:
  - TASK-004
references:
  - README.md
  - DECISIONS.md
priority: high
type: feature
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Completes the capture-from-anywhere goal. The Shortcut currently posts to `http://192.168.50.122:5678/webhook/capture`, a hard-coded private LAN address that is only meaningful inside the home network, so away from home it fails with a server error message and the dictated item is lost. Watch-based capture is the most frequently used entry point into the system, so this is the failure that matters most.

Once TASK-004 is live the Shortcut can target the public HTTPS hostname instead, presenting the TASK-003 shared secret as a request header. No VPN profile and no app install are involved on any device, which is what allows the Apple Watch to work: watchOS has no VPN client available, and a Shortcut running there makes an ordinary HTTPS request over the Watch cellular or wifi connection.

All three invocation surfaces need verification because they do not share a network path. The Watch may route through the paired iPhone over Bluetooth when nearby, or use its own cellular or wifi radio when not, and CarPlay runs the Shortcut on the phone. The important test is the Watch acting independently, away from both the home network and the phone.

Per DECISIONS.md the Shortcut has no offline queue and fails silently when the server is unreachable. That limitation is not solved here and remains deferred to the planned native iOS app, but the failure should at least be visible rather than silent.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The Shortcut posts to the public HTTPS hostname from TASK-004 rather than to a private LAN IP address
- [x] #2 The Shortcut presents the TASK-003 secret as a request header, and the secret is not committed to the repository
- [x] #3 Dictated capture succeeds from the Apple Watch while away from the home network, verified with the Watch on cellular or non-home wifi rather than relaying through a nearby paired iPhone
- [x] #4 Dictated capture succeeds from the iPhone on cellular with wifi disabled
- [ ] #5 Dictated capture succeeds from CarPlay
- [x] #6 Each captured item appears in the inbox with the dictated text intact, confirmed via the UI or `GET /next-actions`
- [x] #7 Capture still succeeds while on the home network, confirming no regression for the existing working path
- [x] #8 A failed capture surfaces a visible error on the device rather than appearing to succeed
- [x] #9 The iOS Shortcut Setup section of the README is updated with the new URL, the required header, and how to supply the secret without storing it in the repository
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## What the Shortcut needs

Target `https://capture.medaughsolutions.com/webhook/capture` (published in TASK-004) instead of the dead `192.168.50.122:5678`, with the `X-Webhook-Token` header carrying the n8n webhook secret. Plain HTTPS with a header, so nothing is installed on any device and watchOS -- which has no VPN client -- can use it.

## AC #8 needs an n8n change, not a Shortcut change

The webhook is set to `responseMode: onReceived`, so it returns 200 the moment the request arrives, before the API call runs. A capture that fails downstream therefore reports success to the Shortcut. This is not hypothetical: earlier today a capture returned 200 and created nothing, because the expression error happened after the acknowledgement.

Changing the webhook to `responseMode: lastNode` makes it wait for the chain and return the real result, so a downstream 401 or error becomes a non-200 that Shortcuts surfaces as a visible failure. Capture becomes marginally slower, by the duration of one API call, which is irrelevant for dictation and well worth honest reporting.

**Change this in the n8n UI rather than by re-importing the workflow.** It is a single dropdown. Re-importing has twice now reset the Webhook node authentication and unlinked its credential, which cost significant debugging time; the repo JSON is updated to match so the two stay in sync without an import.

## Steps

1. Update `n8n/workflows/inbox-capture.json` to `responseMode: lastNode` so the committed definition matches what the live instance will do.

2. James changes Response Mode on the Webhook node to "When Last Node Finishes" in the n8n UI, and confirms Authentication is still Header Auth with the `GSD Capture Webhook Token` credential attached.

3. Verify from the command line first, before touching the Shortcut, so a failure can be attributed to one change at a time: a correct token creates an item and now returns the created row rather than a generic acknowledgement, and a wrong token returns 403.

4. James updates the Shortcut: URL to the public hostname, and adds the `X-Webhook-Token` header alongside the existing `Content-Type`. The secret lives in the Shortcut definition, which syncs through the iCloud keychain to Watch and CarPlay, and is never committed.

5. Verify each invocation surface separately, since they do not share a network path (AC #3, #4, #5). The Watch must be tested acting independently on its own cellular or wifi, not relaying through a nearby paired iPhone over Bluetooth, since relaying would mask exactly the failure being fixed. CarPlay runs the Shortcut on the phone.

6. Confirm each dictated item appears in the inbox with its text intact (AC #6), and that capture still works on the home network (AC #7).

7. Verify failure is visible (AC #8) by temporarily sending a wrong token and confirming the device reports an error rather than appearing to succeed.

8. Rewrite the README iOS Shortcut Setup section: new URL, the header, where the secret lives, and the note that the old LAN address is dead (AC #9).

## Out of scope

No offline queue. DECISIONS.md records that the Shortcut fails rather than queuing when the server is unreachable, deferred to the planned native iOS app. This task makes the failure visible; it does not make it recoverable.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
SHORTCUT REPOINTED AND WORKING 2026-09-26. Now posts to https://capture.medaughsolutions.com/webhook/capture with the X-Webhook-Token header. Verified from iPhone on home wifi, iPhone on cellular with wifi off, and Apple Watch. Successful writes visible as POST /next-actions 201 Created from 10.42.2.175 in the api log.

THREE DISTINCT FAULTS were hit getting here, worth recording because none was in the infrastructure and each looked like a network problem:

1. JSON body key entered as "title" with literal double quotes rather than title, so the API received only {"status":"inbox"} and returned 422 with loc ["body","title"] Field required. The n8n error surfaced this precisely once we read the Create Inbox Item node output rather than the status code.

2. The Provided Input variable from Ask for Input inserted directly into the JSON value field serialised as a typed object rather than a plain string, producing a malformed body. Hardcoding a literal value worked while the variable did not, which is what isolated it. Fixed by coercing through an intermediate Text action containing only the variable.

3. The Apple Watch was running a stale copy of the Shortcut. iCloud sync had not propagated the fixes, so every Watch test exercised the old broken version and its requests never reached the server at all. Resolved by toggling Show on Apple Watch off and on to force a re-push. This is why Watch behaviour diverged from the phone and why the failures looked like watchOS or connectivity problems. Check Shortcut freshness on the Watch before diagnosing anything Watch-specific.

AC #8 is satisfied by direct observation rather than a contrived test: after the responseMode change to lastNode, real failures surfaced on the device as visible errors ("error in workflow", then "400 Bad Request") instead of silently reporting success. Under the previous onReceived setting these same failures would have returned 200 and the captures would have vanished without any indication.

Latency measured at 0.8 to 1.0s for the full public round trip including the API write, so the extra wait introduced by lastNode is not a practical cost.

Test rows created during verification were deleted as they went; the inbox is clean.

AC #3 VERIFIED 2026-09-26. Capture from the Apple Watch succeeded with both the Watch and the paired iPhone off wifi, so the request travelled over cellular rather than the home network. Three POST /next-actions 201 Created appeared in the api log during the test window with no n8n errors.

Evidence limitation worth stating: the api log records the request as coming from 10.42.2.175, the n8n pod, because that is the hop that writes to the API. Server-side logs therefore confirm the capture completed but cannot show which network the originating device used. That half rests on direct observation by the user, which is the only place it can come from short of inspecting Cloudflare request logs.

This closes the original goal that started this work: dictated capture into the GSD inbox from the Apple Watch, away from the home network, with no VPN and nothing installed on the device.

AC #6 VERIFIED 2026-09-26. Captured items appear in the inbox with the dictated text intact. The user reports occasional minor dictation errors, which are Siri speech-recognition inaccuracies rather than transport or encoding problems: the text arrives as transcribed, and nothing is truncated or mangled in the JSON body, n8n, or the API. The earlier malformed-body faults produced hard 422 and 400 failures rather than corrupted text, so a garbled title would be a distinct symptom from anything seen here.

AC #5 (CarPlay) NOT VERIFIED and closed as pending real-world confirmation, at the user direction. CarPlay runs the Shortcut on the iPhone, whose network paths are already verified on both home wifi and cellular, so CarPlay changes the invocation surface rather than the request or the transport. The residual risk is Siri recognition of the shortcut name in the car rather than anything in this pipeline. If it misbehaves, it warrants a small follow-up rather than reopening this task.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The Siri Shortcut now captures into the GSD inbox from any network. It posts to https://capture.medaughsolutions.com/webhook/capture with the webhook secret in an X-Webhook-Token header, replacing http://192.168.50.122:5678/webhook/capture -- a private LAN address on a host that turned out to be down entirely, so capture had been failing on the home network as well as away from it.

Verified working from the iPhone on home wifi, the iPhone on cellular with wifi disabled, and the Apple Watch with both the Watch and the paired phone off wifi, each producing POST /next-actions 201 Created from the n8n pod. Dictated text arrives intact; the occasional inaccuracy is Siri transcription rather than transport. CarPlay is unverified and closed as pending, since it runs the Shortcut on the already-verified iPhone.

Also switched the n8n webhook from responseMode onReceived to lastNode, so it waits for the API write and returns the real result. Under onReceived the webhook acknowledged the request before the API call ran, meaning a failed capture reported success and vanished -- observed for real earlier in this work. That change is what made the three faults below visible on the device instead of silent, and it satisfies the requirement that failures surface. The cost is about one second of round trip, measured end to end.

Three faults were found and fixed, none of them in the infrastructure, all of which initially looked like network problems: the JSON body key was entered as "title" with literal quotes so the API received no title and returned 422; the Provided Input variable inserted directly into a JSON value serialised as a typed object rather than a string, fixed by coercing through an intermediate Text action; and the Apple Watch was running a stale iCloud-synced copy of the Shortcut, so every Watch test exercised the old broken version and never reached the server, fixed by toggling Show on Apple Watch to force a re-push. That last one is the reason Watch behaviour diverged from the phone and looked like a watchOS or connectivity limitation.

The README iOS Shortcut Setup section is rewritten with the new URL, the header, where the secret lives, why the old LAN address must not be used, and the note that failures are now visible but captures still are not queued offline.
<!-- SECTION:FINAL_SUMMARY:END -->
