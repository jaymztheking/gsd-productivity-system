---
id: TASK-004
title: Expose GSD publicly via Cloudflare Tunnel with Access in front of the UI
status: To Do
assignee: []
created_date: '2026-09-25 18:10'
labels:
  - networking
  - cloudflare
  - security
dependencies:
  - TASK-002
  - TASK-003
references:
  - k8s/ingress.yaml
  - k8s/n8n/service.yaml
  - n8n/workflows/inbox-capture.json
priority: high
type: feature
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Makes GSD reachable from anywhere without opening a router port. A `cloudflared` daemon on the homelab dials outbound to Cloudflare and holds the connection open; public requests arrive at Cloudflare and ride back down that established connection. Because the connection originates from inside the network, nothing needs to be exposed on the router, and because clients speak plain HTTPS, no software or VPN profile is needed on any device. That last property is what makes Apple Watch capture possible: there is no Tailscale or VPN client for watchOS, so any solution requiring client software cannot serve the Watch.

Cloudflare Access sits at the edge in front of the UI and provides the interactive login that a browser needs, free for up to 50 users. The capture webhook cannot sit behind an SSO prompt because iOS Shortcuts cannot complete an interactive login, so that path is authenticated by the shared-secret header from TASK-003 instead.

An unresolved question must be settled as part of this work: which n8n instance actually serves the capture webhook. The Shortcut currently posts to `192.168.50.122:5678/webhook/capture`, but every Service in `k8s/` is ClusterIP with no NodePort, so the in-cluster n8n is not reachable at that address. The comment in `k8s/ingress.yaml` ("n8n is shared — use the existing instance at n8n.home.lab") suggests .122 is a separate instance running outside the cluster, distinct from the Traefik/MetalLB address 192.168.50.240. If the external instance is the live one, its workflow targets `http://api.gsd.svc.cluster.local:8000/next-actions`, a cluster-internal name that only resolves from inside k3s, which would be a second latent failure independent of remote access.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Which n8n instance serves `192.168.50.122:5678/webhook/capture` is confirmed and documented, along with how it is exposed and whether it runs inside or outside the k3s cluster
- [ ] #2 The n8n-to-API hop is verified working from wherever that n8n actually runs, with the effective URL recorded (replacing `api.gsd.svc.cluster.local` if that name does not resolve there)
- [ ] #3 `cloudflared` runs as a persistent service on the homelab, starts automatically on boot, and reconnects on its own after a network interruption
- [ ] #4 The GSD UI is served over HTTPS at gsd.medaughsolutions.com with a valid certificate, reachable from outside the home network
- [ ] #5 Cloudflare Access protects the UI with SSO, and an unauthenticated visitor is stopped at the Cloudflare edge without reaching the homelab
- [ ] #6 The capture webhook path is publicly reachable over HTTPS and excluded from the interactive Access policy, authenticated instead by the TASK-003 shared secret
- [ ] #7 No inbound port is opened on the router, verified by confirming the tunnel works with no port-forwarding rules present
- [ ] #8 Remote access is verified from a device on cellular with wifi disabled, not merely from a different wifi network
- [ ] #9 On-LAN access continues to work after the change, whether via the existing gsd.home.lab route or the new public hostname
- [ ] #10 The tunnel and Access configuration, including hostname-to-service mappings and the policy applied to each path, is documented in the repository
<!-- AC:END -->
