---
id: TASK-004
title: Expose GSD publicly via Cloudflare Tunnel with Access in front of the UI
status: Done
assignee:
  - '@James'
created_date: '2026-09-25 18:10'
updated_date: '2026-09-26 06:11'
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
Makes GSD reachable from anywhere without opening a router port. A `cloudflared` daemon dials outbound to Cloudflare and holds the connection open; public requests arrive at Cloudflare and ride back down that established connection. Nothing is exposed on the router, and because clients speak ordinary HTTPS, no software or VPN profile is needed on any device. That last property is what makes Apple Watch capture possible: there is no VPN client for watchOS, so any solution requiring client software cannot serve the Watch, which is the most-used capture surface.

Cloudflare Access sits at the edge in front of the UI and provides the interactive login a browser needs, free for up to 50 users. The capture webhook cannot sit behind an SSO prompt because iOS Shortcuts cannot complete an interactive login, so it is authenticated by its own shared-secret header instead.

Topology, confirmed on the cluster rather than assumed (see implementation notes):

- The live n8n runs inside k3s in the `n8n` namespace, on `service/n8n` (ClusterIP :80 -> container :5678), reached on the LAN through a Traefik ingress at n8n.home.lab. The address the Shortcut currently uses, 192.168.50.122:5678, is a dead host.
- The GSD UI is `service/ui` in the `gsd` namespace, ClusterIP :3000.

**The tunnel must point at the ui service, never at the api service directly.** TASK-003 established that the API requires a token which the browser cannot hold, so the UI nginx attaches it server-side on the way through. A Traefik ingress that routed /api straight to the API bypassed that injection and had to be deleted; a tunnel aimed at the API would reproduce exactly that failure.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Which n8n instance serves `192.168.50.122:5678/webhook/capture` is confirmed and documented, along with how it is exposed and whether it runs inside or outside the k3s cluster
- [x] #2 The n8n-to-API hop is verified working from wherever that n8n actually runs, with the effective URL recorded (replacing `api.gsd.svc.cluster.local` if that name does not resolve there)
- [x] #3 `cloudflared` runs as a persistent service on the homelab, starts automatically on boot, and reconnects on its own after a network interruption
- [x] #4 The GSD UI is served over HTTPS at gsd.medaughsolutions.com with a valid certificate, reachable from outside the home network
- [x] #5 Cloudflare Access protects the UI with SSO, and an unauthenticated visitor is stopped at the Cloudflare edge without reaching the homelab
- [x] #6 The capture webhook path is publicly reachable over HTTPS and excluded from the interactive Access policy, authenticated instead by the TASK-003 shared secret
- [x] #7 No inbound port is opened on the router, verified by confirming the tunnel works with no port-forwarding rules present
- [x] #8 Remote access is verified from a device on cellular with wifi disabled, not merely from a different wifi network
- [x] #9 On-LAN access continues to work after the change, whether via the existing gsd.home.lab route or the new public hostname
- [x] #10 The tunnel and Access configuration, including hostname-to-service mappings and the policy applied to each path, is documented in the repository
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Approach

Run cloudflared as a Deployment inside k3s rather than as a systemd service on a Pi. It then inherits the restart, reconnect and boot behaviour Kubernetes already provides (AC #3), needs no host-level configuration on any node, reaches the target services over cluster DNS without leaving the cluster, and its manifests live in this repo alongside everything else. Two replicas so a node reboot does not drop the tunnel; cloudflared supports multiple connectors on one tunnel.

## Hostname split, and why

Two public hostnames rather than one with path-based Access bypass rules:

- `gsd.medaughsolutions.com` -> `http://ui.gsd.svc.cluster.local:3000`, protected by Cloudflare Access SSO.
- `capture.medaughsolutions.com` -> `http://n8n.n8n.svc.cluster.local:80`, NOT behind Access, restricted to the single path `/webhook/capture`, authenticated by the header secret from TASK-003.

Access policies attach per hostname, so separating the two means the interactive policy cannot accidentally sit in front of the Shortcut, which is unable to complete an SSO challenge. A path-bypass rule on one shared hostname would work, but it is one edit away from locking out capture, and that failure would be silent: the Shortcut would report a generic server error.

The n8n hostname is path-restricted so only the capture webhook is reachable. Without that, every other webhook and the n8n editor itself would be publicly exposed on that hostname. Anything else on it answers 404 from cloudflared, which never reaches the cluster.

## Steps

1. Create the tunnel in the Cloudflare Zero Trust dashboard (Networks -> Tunnels -> Create, connector type Cloudflared). This yields a connector token. Dashboard creation is preferred over `cloudflared tunnel login` because the latter needs an interactive browser session on the host, and the dashboard also manages the DNS records for us.

2. Store the connector token as a Kubernetes Secret in a new `cloudflared` namespace. James runs the `kubectl create secret` command in his own terminal so the token does not pass through the agent transcript. The manifest references the Secret by name and never contains the value; `k8s/cloudflared/secret.yaml.example` documents the shape, matching the existing `k8s/secrets.yaml.example` convention.

3. Add `k8s/cloudflared/` manifests: namespace, ConfigMap holding the ingress rules, and Deployment. The ingress rules encode the hostname split above plus a catch-all 404, and `originRequest.noTLSVerify` is unnecessary because both origins are plain HTTP inside the cluster.

4. Apply and confirm both connectors register and report healthy in the dashboard, and that the pods stay Ready.

5. In the Cloudflare dashboard, publish the two public hostnames against the tunnel. This creates proxied CNAME records automatically. Verify neither disturbs the MX, SPF, DKIM or autodiscover records migrated in TASK-002 — that zone now carries live mail and the records are recorded in doc-001.

6. Apply a Cloudflare Access application to `gsd.medaughsolutions.com` with a one-time-PIN or Google policy limited to James. Confirm an unauthenticated request is stopped at the edge and never reaches the cluster, checked by watching the ui pod log while requesting the hostname (AC #5).

7. Verify the capture path publicly: `POST https://capture.medaughsolutions.com/webhook/capture` refuses without the header secret and creates an inbox item with it, and confirm any other path on that hostname returns 404 without touching n8n (AC #6).

8. Verify no router port-forwarding exists, which the tunnel architecture does not need (AC #7). The check is that the tunnel works while no inbound rule is present, not that a rule was removed.

9. Verify from a device on cellular with wifi disabled, not merely a different wifi network, since another wifi could still route to the LAN and give a false pass (AC #8).

10. Confirm on-LAN access still works via gsd.home.lab, which is unchanged: Pi-hole still resolves it to the Traefik VIP and the existing ingress still serves the UI (AC #9).

11. Document the topology, the hostname split and its reasoning, the Access policy per hostname, and the token rotation path in the README (AC #10).

## Deliberately out of scope

The Shortcut itself is TASK-005. This task proves the capture path works with curl; repointing the Shortcut and verifying Watch, phone and CarPlay belongs there. The MCP server at mcp.gsd.home.lab is not published through the tunnel: it is broken pending TASK-007, and exposing it publicly before it authenticates would be actively harmful.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
AC #1 and #2 RESOLVED 2026-09-26 during TASK-003 deployment, before this task began. The speculation in the original description is superseded.

AC #1: the live n8n runs INSIDE the k3s cluster, in the n8n namespace on node cherrypi (pod n8n-6b8dbb759c-dblxs). It is exposed on service/n8n, a ClusterIP on port 80 targeting container port 5678, and reached externally through a Traefik ingress at n8n.home.lab which resolves to 192.168.50.240. It is NOT the instance at 192.168.50.122:5678 — that host is entirely down, both :5678 and :80 closed with ICMP reporting host down. So the Siri Shortcut has been pointing at a dead address, meaning capture was broken on the home network too, not only away from it.

AC #2: the n8n-to-API hop works. api.gsd.svc.cluster.local:8000 resolves from that n8n, so no URL replacement is needed. Verified against the auth-enforcing API after the TASK-003 deployment: a capture POST returned 201 Created and all four weekly-digest fetches returned 200, all from 10.42.2.175 (the n8n pod), with zero 401s. The same endpoints return 401 without a token, so those successes are evidence the credential authenticated.

Tunnel targets confirmed reachable from inside the cluster: ui.gsd.svc.cluster.local:3000 and n8n.n8n.svc.cluster.local:80, the latter returning 403 on POST /webhook/capture, which is the header-auth layer refusing an unauthenticated probe. Both gsd.medaughsolutions.com and capture.medaughsolutions.com are currently unused in DNS.

TUNNEL LIVE AND VERIFIED 2026-09-26. Tunnel id 12477315-47dd-4346-903c-c4f12e84a5dc, 2 connector replicas on separate nodes (derbypi, fruitpi), 8 registered connections.

Local ingress rules ARE honoured by a connector-token tunnel, which was not a given: token-based tunnels can take configuration from Cloudflare instead and ignore the local file. Proved by behaviour rather than by logs: capture.medaughsolutions.com/ returns 404 from the catch-all rule in the ConfigMap while /webhook/capture reaches n8n. This only holds because the public hostnames were added as plain proxied CNAME records in the DNS tab; adding them through the tunnel Public Hostname tab writes routing into Cloudflare and overrides the local config, which would silently move the routing out of version control.

AC #5 evidence, edge blocking with a control: requested a uniquely-named path through the public hostname and found 0 occurrences in the ui pod log, then requested the same path via the LAN ingress and found 1. The control matters, since a zero count alone could just mean the log check was broken.

AC #6 evidence: POST https://capture.medaughsolutions.com/webhook/capture with the header secret returned 200 and created inbox item 20da46c0, with POST /next-actions 201 Created logged from 10.42.2.175. A wrong token and a missing token both return 403. Other paths on that hostname return 404 from cloudflared without reaching the cluster, including /rest/login, so the n8n editor is not exposed.

AC #3 evidence: deleted one connector pod and polled the public capture hostname every 2s for 16s with no failed request; Kubernetes scheduled a replacement on another node automatically.

Debugging note: several rounds of 403 on the capture webhook were caused by the stored credential value being unknown and unreadable rather than by any misconfiguration. n8n masks credential values, and the secret had been regenerated twice, so every test used a stale value. The 403 response also carries www-authenticate: Basic realm="Webhook" even when the node uses Header Auth, which led me to wrongly diagnose the auth type; that header is part of n8n generic 403 and is not evidence of the configured type. What resolved it was generating a token, recording it in a password manager first, and then setting it in n8n -- so the value was readable at test time. Do that from the start with any masked credential.

TASK-002 regression check passed after adding the CNAMEs: MX, SPF and autodiscover unchanged, and the DKIM hash still matches doc-001.

AC #7 and #8 VERIFIED 2026-09-26. Router (ASUS RT-AX82U) Virtual Server / Port Forwarding list is empty -- "No data in table" -- so the tunnel works with no inbound rule present at all, which is the stronger form of the claim than removing one. Remote access confirmed by the user from a phone on cellular with wifi disabled: Cloudflare Access challenged, then the UI loaded.

UX issue observed and not yet addressed: the user reported "a lot of Cloudflare login pages". That is the one-time-PIN flow combined with a short default Access session duration. Raising Session Duration on the GSD application, or switching the identity provider from Cloudflare OTP to Google, would remove most of the friction. Worth doing before daily reliance, since a capture tool that demands repeated re-authentication is one people stop opening. Not tracked as a task yet.

FINAL SWEEP 2026-09-26 06:11 UTC: public UI host 302 to Access both at / and /api/next-actions; capture path 403 without a token; capture host 404 on /rest/login; LAN UI and LAN data both 200; TLS verify result 0; both connectors Running on separate nodes; DKIM hash still matching doc-001.

Test data left in the live inbox by this work: e2e-test (c91e49c6) and public capture test (20da46c0). Both are real rows in the production database and should be deleted during triage.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
GSD is now reachable from anywhere over HTTPS with no port open on the router, completing the remote-access half of the original goal. cloudflared runs in-cluster as a two-replica Deployment spread across nodes, so it inherits Kubernetes restart and reschedule behaviour; verified by deleting a connector pod and observing no dropped requests while a replacement was scheduled elsewhere.

Two public hostnames rather than one. gsd.medaughsolutions.com serves the UI behind Cloudflare Access SSO. capture.medaughsolutions.com serves only the n8n capture webhook, restricted to ^/webhook/capture/?$ and authenticated by its own header secret, because iOS Shortcuts cannot complete an interactive SSO challenge. Access policies attach per hostname, so separating them keeps the SSO policy from ever landing in front of the Shortcut, which would fail with a generic server error and be hard to attribute. Every other path on the capture hostname, including the n8n editor at /rest/login, is answered 404 by cloudflared without reaching the cluster.

The tunnel points at the ui service rather than api, because the API requires a token the browser cannot hold and the UI nginx attaches it in transit. Routing lives in k8s/cloudflared/configmap.yaml, and the hostnames are plain proxied CNAMEs rather than tunnel Public Hostname entries, since those write routing into Cloudflare and would override the version-controlled config.

Verified: unauthenticated requests to the UI host return 302 to Access and never reach the cluster, proved with a uniquely-named path that appeared 0 times in the ui pod log and 1 time when requested via the LAN ingress as a control; a public HTTPS capture with the header secret created inbox item 20da46c0 with POST /next-actions 201 Created logged from the n8n pod, while a wrong or missing token returns 403; TLS is valid Let us Encrypt over HTTP/2; the router port-forwarding table is empty so no inbound rule exists; remote access confirmed from a phone on cellular with wifi disabled; gsd.home.lab still works on the LAN; and the TASK-002 mail records survived the new DNS entries with the DKIM hash still matching doc-001.

Two questions this task carried from creation were answered during TASK-003 and are recorded in the notes: the live n8n runs inside the cluster in the n8n namespace, and its cluster-internal API hostname resolves correctly. The address the Shortcut still points at, 192.168.50.122:5678, is a dead host, which means capture has been broken on the home network too rather than only remotely -- TASK-005 now has a working public endpoint to repoint it at.

Two follow-ups are noted rather than done: the Access session duration should be raised or the identity provider switched to Google, because the one-time-PIN flow currently prompts often enough to be a deterrent; and two test rows were left in the production inbox.
<!-- SECTION:FINAL_SUMMARY:END -->
