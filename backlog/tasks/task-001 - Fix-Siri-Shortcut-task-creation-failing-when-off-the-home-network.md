---
id: TASK-001
title: Fix Siri Shortcut task creation failing when off the home network
status: To Do
assignee:
  - James
created_date: '2026-09-22 22:39'
updated_date: '2026-09-22 22:41'
labels:
  - shortcuts
  - networking
  - tailscale
dependencies: []
references:
  - k8s/api/ingress.yaml
  - k8s/ingress.yaml
  - k8s/api/middleware.yaml
  - api/app/routers/next_actions.py
priority: high
type: bug
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Sending a new next action from the iOS Siri Shortcut to the GSD API succeeds on the home wifi and fails when away from it. The Shortcut is the primary capture path when away from a desk, so silent failure off-network means captured items are lost at exactly the moment the system is most useful.

Relevant setup: the Traefik ingress serves the API at host `gsd.home.lab` on the `web` (plain HTTP, port 80) entrypoint, stripping the `/api` prefix before the FastAPI service on port 8000 (`k8s/api/ingress.yaml`, `k8s/api/middleware.yaml`). `gsd.home.lab` is a Pi-hole A record pointing at the MetalLB/Traefik LAN IP 192.168.50.240 (`k8s/ingress.yaml`) — a private RFC1918 address served by a LAN-only resolver. Off the home LAN, reaching it depends on the Tailscale tunnel: Pi-hole must be configured as a Tailscale split-DNS nameserver for `home.lab`, and 192.168.50.240 must be reachable via an advertised-and-accepted subnet route (or the service reachable by its MagicDNS `*.ts.net` name instead). Either piece being absent produces exactly this symptom, and so do several unrelated causes, so the failing layer needs to be identified before a fix is chosen.

Note the suspected layers are not mutually exclusive, and iOS adds its own: Shortcuts can run with the Tailscale VPN profile inactive, and iOS may fall back to cellular DNS for a `.lab` suffix. Diagnosis must record the observed failure (HTTP status, timeout, or DNS error) rather than only whether it worked.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A documented off-network reproduction exists: running the Shortcut away from the home LAN is captured with the exact failure surfaced (error text, HTTP status code, or timeout duration) and the elapsed time before failure
- [ ] #2 The Tailscale tunnel layer is isolated: with the device off the home LAN and Tailscale connected, `ping`/`tailscale status` from the iOS device (or an equivalent off-network client) confirms whether the homelab node is reachable, and whether 192.168.50.240 is reachable by raw IP with DNS bypassed
- [ ] #3 The DNS resolution layer is isolated: off-network resolution of `gsd.home.lab` is tested and recorded — whether it resolves at all, and whether it resolves to 192.168.50.240 or to a public/NXDOMAIN answer — confirming or ruling out Tailscale split-DNS/MagicDNS as the failing layer
- [ ] #4 The GSD endpoint layer is isolated: `POST /api/next-actions` and `GET /api/health` are exercised against `gsd.home.lab` from an on-LAN client and from an off-network client reaching the same IP over Tailscale, showing whether the API itself responds identically in both cases
- [ ] #5 The Shortcut request layer is isolated: the exact URL, HTTP method, headers, and JSON body the Shortcut sends are captured and replayed verbatim with curl from an off-network client, showing whether the failure follows the request or the client
- [ ] #6 The failing layer is named explicitly in the task notes, with the evidence that rules out the other three
- [ ] #7 The Shortcut creates a next action successfully from off the home network, verified end to end by the new action appearing via `GET /api/next-actions`
- [ ] #8 The fix still works on the home wifi — no on-LAN regression — and both paths are verified after the change
- [ ] #9 The resulting network path (DNS names, routes, and any Tailscale split-DNS or subnet-route configuration) is documented in the repo so it can be rebuilt without rediscovery
<!-- AC:END -->
