---
id: TASK-005
title: Rework the Siri Shortcut to capture over public HTTPS from any network
status: To Do
assignee: []
created_date: '2026-09-25 18:10'
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
- [ ] #1 The Shortcut posts to the public HTTPS hostname from TASK-004 rather than to a private LAN IP address
- [ ] #2 The Shortcut presents the TASK-003 secret as a request header, and the secret is not committed to the repository
- [ ] #3 Dictated capture succeeds from the Apple Watch while away from the home network, verified with the Watch on cellular or non-home wifi rather than relaying through a nearby paired iPhone
- [ ] #4 Dictated capture succeeds from the iPhone on cellular with wifi disabled
- [ ] #5 Dictated capture succeeds from CarPlay
- [ ] #6 Each captured item appears in the inbox with the dictated text intact, confirmed via the UI or `GET /next-actions`
- [ ] #7 Capture still succeeds while on the home network, confirming no regression for the existing working path
- [ ] #8 A failed capture surfaces a visible error on the device rather than appearing to succeed
- [ ] #9 The iOS Shortcut Setup section of the README is updated with the new URL, the required header, and how to supply the secret without storing it in the repository
<!-- AC:END -->
