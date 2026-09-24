---
id: TASK-001
title: Fix Siri Shortcut capture failing when off the home network
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
  - n8n/workflows/inbox-capture.json
  - README.md
  - k8s/ingress.yaml
  - k8s/n8n/service.yaml
priority: high
type: bug
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Saying "Hey Siri, Capture" sends a task to the inbox fine on home wifi and fails when away from it. Capture-from-anywhere is the whole point of the Shortcut, so failing off-network loses items exactly when the system matters most.

The actual path (confirmed against the repo, not assumed):

1. iOS Shortcut dictates text and POSTs JSON `{"title": "..."}` to `http://192.168.50.122:5678/webhook/capture` — plain HTTP, no hostname, a hard-coded private LAN IP.
2. Port 5678 is n8n. The `capture` webhook path is defined in `n8n/workflows/inbox-capture.json`.
3. That workflow POSTs to `http://api.gsd.svc.cluster.local:8000/next-actions` with `status: "inbox"`, which writes to Postgres.

The key fact for diagnosis: the Shortcut targets a bare IP, so **no DNS lookup happens on that hop at all**. Pi-hole and Tailscale MagicDNS resolve names, and there is no name here to resolve — they cannot be the cause of this specific failure, and time spent on split-DNS is wasted until step 1 is proven to connect. The real question is whether 192.168.50.122 is *routable* from the phone when it is off the LAN. 192.168.50.x is a private address range, meaningful only inside the home network; from outside it reaches nothing unless a Tailscale node at home advertises the 192.168.50.0/24 subnet route AND the phone has accepted that route AND the Tailscale VPN is actually active at the moment Siri fires the Shortcut.

Open question to resolve first: which n8n actually serves this webhook. Every Service in `k8s/` is ClusterIP with no NodePort, so the in-cluster n8n is not reachable at `192.168.50.122:5678`. The comment in `k8s/ingress.yaml` ("n8n is shared — use the existing instance at n8n.home.lab") suggests .122 is a separate pre-existing n8n running outside the cluster, distinct from the Traefik/MetalLB IP 192.168.50.240. If that external n8n is the live one, confirm it can still reach the API — `api.gsd.svc.cluster.local` is a cluster-internal name that only resolves from inside the k3s cluster, which would be a second latent bug independent of the network issue.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Confirmed and recorded which n8n instance actually serves `192.168.50.122:5678/webhook/capture`: the in-cluster deployment or a separate host-level instance, and how it is exposed
- [ ] #2 Off-network reproduction captured with the exact failure surfaced — error text, HTTP status, or timeout duration and how long it hung before failing — not just "it did not work"
- [ ] #3 Tailscale VPN state is confirmed at the moment the Shortcut runs: whether the tunnel is actually active when Siri fires it from phone, Watch, and CarPlay, since a Shortcut can run with the VPN profile inactive
- [ ] #4 Routability of 192.168.50.122 from off-network is tested directly with the VPN up — the raw IP reached by curl or ping from the phone or an equivalent off-LAN client — confirming whether a subnet route for 192.168.50.0/24 is advertised by a home Tailscale node and accepted by the client
- [ ] #5 The n8n webhook layer is isolated: `POST /webhook/capture` with the same JSON body succeeds against 192.168.50.122:5678 from an on-LAN client, establishing that the endpoint works and the failure is the network path
- [ ] #6 The n8n-to-API hop is verified: a capture that reaches n8n results in an inbox item, confirming the workflow can resolve and reach the API from wherever that n8n actually runs
- [ ] #7 A capture succeeds end to end from off the home network, verified by the dictated item appearing in the inbox via `GET /next-actions`
- [ ] #8 Capture still works on home wifi after the change — both paths verified, no on-LAN regression
- [ ] #9 The Shortcut target address is documented, and if it changes (for example to a Tailscale MagicDNS `*.ts.net` name that works identically on and off the LAN) the README iOS Shortcut Setup section is updated to match
<!-- AC:END -->
