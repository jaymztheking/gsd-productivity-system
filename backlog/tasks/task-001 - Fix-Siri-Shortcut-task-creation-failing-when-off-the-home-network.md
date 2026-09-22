---
id: TASK-001
title: Fix Siri Shortcut task creation failing when off the home network
status: To Do
assignee:
  - James
created_date: '2026-09-22 22:39'
updated_date: '2026-09-22 22:52'
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
