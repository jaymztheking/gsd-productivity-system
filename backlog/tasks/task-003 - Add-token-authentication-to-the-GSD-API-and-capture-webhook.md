---
id: TASK-003
title: Add token authentication to the GSD API and capture webhook
status: Done
assignee:
  - '@James'
created_date: '2026-09-25 18:09'
updated_date: '2026-09-26 05:28'
labels:
  - security
  - api
  - auth
dependencies: []
references:
  - api/app/main.py
  - n8n/workflows/inbox-capture.json
  - docker-compose.yml
priority: high
type: feature
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The API has no authentication of any kind today: no tokens, no login, no API keys, and `allow_origins=["*"]` in `api/app/main.py`. Every endpoint is open to anyone who can reach it. This was acceptable while the service was LAN-only, but it is a hard blocker for exposing GSD to the internet: without it, anyone who discovers the hostname can read, modify, and delete the entire task list.

This task must land before the Cloudflare Tunnel goes live. It covers the machine-to-machine half of authentication, which is the half that has to work without a human present.

The constraint that shapes the design: capture must keep working from Apple Watch, CarPlay, and iPhone through iOS Shortcuts, with no interactive login and no app install. Shortcuts can set custom HTTP headers on a request, so a long random shared secret presented in a header satisfies both requirements. The secret lives in the Shortcut, which is stored in the iCloud keychain.

Browser access to the UI needs the interactive cookie-based kind of auth instead, which Cloudflare Access provides at the edge; that is handled in the tunnel task and is deliberately out of scope here. Note that a token check at the edge alone is not sufficient: the API and the capture webhook must reject unauthenticated requests on their own, so that anything reaching them from inside the network or via a misconfigured route is still refused.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 All API endpoints that read or modify data require a valid secret token and return 401 with no data when it is missing or wrong
- [x] #2 The token is presented in an HTTP header that iOS Shortcuts can set, and is verified with a constant-time comparison
- [x] #3 The token is supplied via environment variable or Kubernetes Secret, is absent from the repository and from committed manifests, and `.env.example` documents it without a real value
- [x] #4 BOTH n8n workflows present the token on their calls to the API: inbox-capture.json on its create call, and weekly-digest.json on all four of its fetch calls, so neither workflow is left broken by the new auth requirement
- [x] #5 The capture webhook itself validates a shared secret, so that public exposure does not permit anonymous writes even if the API is reachable only through it
- [x] #6 CORS `allow_origins` is narrowed from `["*"]` to the known UI origin(s)
- [x] #7 The `/health` endpoint remains unauthenticated for Kubernetes probes and exposes no task data
- [x] #8 Tests cover both the authorized and unauthorized paths for a representative read endpoint and a representative write endpoint
- [x] #9 Local development via docker compose still works, with the required setup documented in the README
- [x] #10 Token rotation is documented: where to change the secret and which components must be updated together
- [x] #11 The auth-enabled API and UI images are built for ARM64 and pushed, and the k3s deployments are rolled out with API_TOKEN present in the gsd-secrets Secret
- [x] #12 On the deployed cluster, an unauthenticated request to a data endpoint returns 401 and an authenticated one returns 200, confirming auth is live in production and not only locally
- [x] #13 The deployed UI still loads and reads/writes data through its proxy, with no token present in anything the browser receives
- [x] #14 A capture through the live n8n workflow creates an inbox item against the auth-enforcing API, proving the GSD API Token credential is correctly attached and valued rather than merely present
- [x] #15 The deployed /health endpoint still answers unauthenticated so the k8s probes keep the pods ready
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Research findings that shape this plan

**The UI never makes a cross-origin request to the API.** `ui/src/api/client.ts` sets `BASE = "/api"` and issues same-origin relative paths. `ui/nginx.conf` proxies `/api/` to `http://api:8000/` in production, and `ui/vite.config.ts` proxies the same path in dev. Two consequences: the CORS middleware is functionally unused today, and the token can be injected by the proxy rather than by the browser.

**The token must never reach the browser.** Because the proxy sits between them, nginx and the Vite dev server can attach the secret server-side with `proxy_set_header`. The React application needs no changes and ships no secret. Putting the token in frontend code would expose it to anyone who can load the page, since Cloudflare Access authenticates the human but the delivered JavaScript is still readable.

**`api/app/routers/projects.py` alone exposes 12 endpoints**, plus 4 on next-actions and 1 on tags. Applying the guard per route would be 17 edit sites and easy to miss one, so it is applied once per router at include time in `main.py`.

**No test dependencies are declared.** Neither `api/requirements.txt` nor `api/pyproject.toml` lists pytest, httpx or requests, though `api/tests/test_digest_pipeline.py` imports pytest and requests and runs against a live API_URL. Auth tests need pytest plus httpx for the FastAPI TestClient, added as dev dependencies.

## Steps

1. `api/app/config.py` — add `API_TOKEN: str` and `CORS_ALLOW_ORIGINS: str = ""` to Settings. Required with no default, so the API fails loudly at startup if unset rather than silently running unprotected.

2. `api/app/auth.py` (new) — `require_token` dependency reading the `X-API-Token` header and comparing with `secrets.compare_digest` (constant time, AC #2). Returns 401 with a generic body on missing or wrong token, revealing nothing about which. Chosen over Authorization/Bearer because iOS Shortcuts sets custom headers trivially and it will not collide with the Cloudflare Access headers added in TASK-004.

3. `api/app/main.py` — attach `dependencies=[Depends(require_token)]` to each of the three `include_router` calls, covering all 17 data endpoints in one place (AC #1). Leave `/health` untouched and unauthenticated for the k8s probes in `k8s/api/deployment.yaml` (AC #7). Narrow `allow_origins` from `["*"]` to the parsed `CORS_ALLOW_ORIGINS` list (AC #6).

4. `ui/nginx.conf` — add `proxy_set_header X-API-Token "${API_TOKEN}";` and convert the file to an nginx template so the value comes from the environment at container start. The `nginx:alpine` image already runs envsubst over `/etc/nginx/templates/*.template`, so this needs a Dockerfile path change rather than a custom entrypoint. `ui/vite.config.ts` — add the same header to the dev proxy so local development matches production.

5. `n8n/workflows/inbox-capture.json` — add the `X-API-Token` header to the HTTP Request node that posts to the API (AC #4).

6. `n8n/workflows/inbox-capture.json` — enforce a shared secret on the webhook itself so public exposure does not allow anonymous writes (AC #5), using the webhook node header-auth credential rather than a comparison node, so the secret is stored in n8n credentials rather than embedded in the exported workflow JSON.

7. `docker-compose.yml`, `.env.example`, `k8s/secrets.yaml.example`, `k8s/api/deployment.yaml`, `k8s/ui/deployment.yaml` — wire `API_TOKEN` through as an env var sourced from the existing `gsd-secrets` Secret. `.env.example` documents it with a placeholder and generation command, never a real value (AC #3). `.gitignore` already covers `.env` and `k8s/secrets.yaml`.

8. `api/tests/test_auth.py` (new) — TestClient tests over a representative read (`GET /tags`) and a representative write (`POST /next-actions`), asserting 401 with no body content when the header is absent, 401 when wrong, and success when correct, plus `/health` reachable unauthenticated. `get_db` is overridden and the crud functions stubbed so the tests need no database (AC #8). Add pytest and httpx as dev dependencies.

9. `README.md` — document local setup with the token, how to generate one, and a token rotation procedure naming every component that must change together: the k8s Secret, the UI deployment env, both n8n workflows, and the iOS Shortcut (AC #9, #10).

10. Verify: run the test suite; bring up docker compose and confirm an unauthenticated request is refused while a correctly authenticated one succeeds; confirm the UI still loads and reads/writes through the proxy without any token in browser-visible code; confirm `/health` still answers unauthenticated.

## Open scope question, unresolved

`n8n/workflows/weekly-digest.json` makes four API calls (`/next-actions?status=inbox`, `?status=active`, `?status=pending`, and `/projects?status=active`). Adding auth breaks the Sunday digest unless that workflow also presents the token. The acceptance criteria name only the capture workflow, so this is outside the stated scope and needs a decision before implementation: extend AC #4 to cover both workflows, or track it separately. Leaving it unaddressed would ship a known regression in a scheduled job that fails quietly once a week.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Scope decision 2026-09-26: AC #4 widened to cover weekly-digest.json as well as inbox-capture.json. The digest makes four API calls and would otherwise be silently broken by the new auth requirement. Adding the token there is the same one-line change as the capture workflow. The separate question of why the digest has not been working is tracked in its own task rather than here; this task only ensures auth does not make it worse.

IMPLEMENTED 2026-09-26, commit 6580d1e. 18 files changed.

Design: shared secret in the X-API-Token header, constant-time compared via secrets.compare_digest. Missing and wrong tokens return an identical 401 so the response reveals nothing about which occurred. API_TOKEN has no default in Settings, so the API raises a pydantic ValidationError at import and refuses to start rather than coming up unprotected (verified).

The guard is attached to the three include_router calls rather than per route, because projects.py alone exposes 12 of the 17 data endpoints and 17 separate edit sites invites missing one.

Key design outcome: the token never reaches the browser. ui/src/api/client.ts already used BASE = "/api" with same-origin relative paths, so the proxy in front of the UI attaches the secret server-side. ui/nginx.conf became ui/nginx.conf.template, rendered by the nginx:alpine envsubst entrypoint with NGINX_ENVSUBST_FILTER limited to API_TOKEN so nginx own $uri/$host survive. vite.config.ts does the same for dev. No frontend file changed and none holds the secret. Cloudflare Access authenticates the person but does not hide delivered JavaScript, so a token in frontend code would have been readable by any authenticated viewer.

CORS narrowed from ["*"] to a parsed CORS_ALLOW_ORIGINS list, default empty, since nothing is cross-origin.

Webhook auth (AC #5) uses the n8n webhook node header-auth credential referenced by name (GSD Capture Webhook Token) rather than a value embedded in the exported JSON, so the workflow stays committable. This is separate from API_TOKEN: the webhook secret guards n8n front door, API_TOKEN guards the API behind it. The credential must be created in the n8n UI.

VERIFICATION EVIDENCE
- 11/11 tests pass in api/tests/test_auth.py, covering missing token, wrong token, no data leaked on rejection, missing-vs-wrong indistinguishable, a tripwire proving the handler is never reached unauthorized, authorized read, authorized write, and /health open.
- Behavioural sweep over every endpoint enumerated from the routers: 17/17 return 401 with no token, 17/17 return 401 with a wrong token.
- /health returns 200 {"status":"ok"} unauthenticated, as the k8s probes require.
- API_TOKEN unset: refuses to start with a ValidationError naming API_TOKEN.
- docker compose config resolves API_TOKEN into api and ui and GSD_API_TOKEN into n8n; CORS_ALLOW_ORIGINS resolves empty.
- Both k8s deployments source API_TOKEN from secret gsd-secrets; the migrate initContainer deliberately does not, since it needs no token.
- nginx template renders the token while leaving $uri and $host intact.
- Secret scan over all tracked files: only placeholders, ${VAR} references and secretKeyRef pointers. .env and k8s/secrets.yaml confirmed gitignored. api/tests/test_auth.py contains the literal test-token-not-a-real-secret as a fixture, deliberately named so it cannot be mistaken for a credential.

Two notes for reviewers. Test dependencies (pytest, httpx, requests) were previously undeclared despite test_digest_pipeline.py importing pytest and requests; they are now declared in requirements.txt and as a pyproject test extra. Tests were run in a throwaway venv because the repo has no local Python environment. Also, route introspection via app.routes is misleading on current FastAPI, which wraps included routers in _IncludedRouter rather than flattening them; enumerate from each router instead, which is why the sweep above walks mod.router.routes.

NOT YET VERIFIED: AC #9 requires a live docker compose run and Docker Desktop is not running on this machine. Everything statically checkable about compose passes, but the running-stack confirmation (UI loads and reads/writes through the proxy with no token in browser-visible code, unauthenticated curl refused, authenticated curl succeeds) is outstanding and must be done before this task closes.

LIVE VERIFICATION COMPLETE 2026-09-26, commit 2cc1d36. Docker running; full stack exercised. Two real defects were found by testing a running stack rather than trusting the static checks, both fixed.

DEFECT 1: auth ran after body parsing. FastAPI decodes the request body before resolving dependencies, so an unauthenticated POST carrying malformed JSON returned 422 instead of 401, confirming the endpoint existed and spending parse effort on an unauthenticated caller. Fixed by adding token_auth_middleware, which checks the token before anything reads the body. It also fails safe: a router added later without dependencies=auth is still covered rather than silently shipping open. The per-router dependency is retained as a second layer and for OpenAPI visibility. OPTIONS and the health/docs paths are exempt so CORS preflight and the k8s probes keep working, and the middleware is registered before CORSMiddleware so CORS stays outermost. Two tests added for this.

DEFECT 2: the production UI image did not build. vite.config.ts reads process.env for the proxy token, but npm run build runs `tsc -b` first and @types/node was not a devDependency, failing with TS2580. The dev server never type-checks, so the dev path worked and only the production build broke. This would have failed at deploy time. Added @types/node ^22.0.0. Worth noting the dev and production UI paths differ: docker compose uses Dockerfile.dev (vite), while k3s uses Dockerfile (nginx), so verifying only compose would have missed this entirely.

EVIDENCE, live stack
- 13/13 tests pass.
- /health 200 unauthenticated. /tags 401 with no token, 401 with a wrong token, 200 with the correct one. Refusal bodies for missing and wrong tokens are byte-identical.
- Unauthenticated POST with malformed JSON now returns 401 (was 422). Unrouted path returns 401 rather than leaking 404 vs 401.
- Authorized write created a row via POST /next-actions and read back through GET /next-actions.
- Dev path (vite proxy): GET :3000/api/tags returns data with NO token supplied by the client; the token appears in none of the served sources.
- Production path (nginx image built and run against the compose network): envsubst substituted the token into /etc/nginx/conf.d/default.conf while leaving nginx own $uri and $host intact; :3100/api/tags and /api/next-actions return data with no client token; SPA fallback at /engage returns 200; grep for the secret across all four served files in /usr/share/nginx/html found no match, so the browser bundle is clean.
- Secret scan over tracked files clean; .env confirmed gitignored.

A .env was created locally from .env.example with freshly generated random values so the stack could run. It is gitignored and left in place for local development.

Still requires manual setup outside this repo, and NOT verified here: the n8n header-auth credential named "GSD Capture Webhook Token" must be created in the n8n UI for AC #5 to be operationally true. The workflow declares authentication: headerAuth and references the credential by name, which is the committable half; the secret itself lives in n8n. End-to-end capture through the webhook is exercised in TASK-005.

DESIGN CORRECTION 2026-09-26, commit 4df2c48. The $env approach for the n8n side was wrong and is replaced.

n8n blocks environment variable access inside expressions by default via N8N_BLOCK_ENV_ACCESS_IN_NODE, so {{ $env.GSD_API_TOKEN }} can never resolve. The live homelab instance (n8n 2.38.7) failed with "ExpressionError: access to env vars denied" in the Create Inbox Item node. All five HTTP Request nodes across both workflows now use a stored Header Auth credential named "GSD API Token" instead, matching the mechanism already used for the webhook secret. GSD_API_TOKEN removed from docker-compose.yml and .env.example since nothing reads it.

How it was caught, worth recording: posting to the live webhook returned 200 but created no inbox item. The webhook uses responseMode onReceived, so it acknowledges receipt before the downstream API call runs. A 200 from that webhook is therefore not evidence the capture succeeded, and any future end-to-end check must assert the item appears rather than trusting the status code.

AC #5 IS OPERATIONALLY VERIFIED against the live homelab n8n: POST /webhook/capture returns 403 without the header and 200 with it, so the public webhook rejects anonymous writes. The GSD Capture Webhook Token credential exists and is enforcing.

HOMELAB FINDINGS, relevant to other tasks rather than this one:
- 192.168.50.122 is entirely down: both :5678 and :80 closed, ICMP reports host down. That is the address the Siri Shortcut posts to, so capture has been broken on the home network too, not only away from it. Relevant to TASK-005.
- The live n8n is served through Traefik at n8n.home.lab, which resolves to 192.168.50.240, with /healthz returning 200. This answers the open question in TASK-004 about which n8n serves capture: it is reached through the ingress, not at 192.168.50.122:5678.
- The k3s cluster is healthy: gsd.home.lab and gsd.home.lab/api/health both return 200.
- The deployed API still returns 200 on /api/tags, confirming the auth change is not yet deployed, as expected.
- The n8n-to-API hop uses api.gsd.svc.cluster.local, which has NOT yet been proven to resolve from that n8n; the expression error failed before the request was attempted, so that question is still open and belongs to TASK-004.

Correction: the design-correction commit hash above is wrong. The credential change is commit 728b8a3, not 4df2c48.

AC #4 PARTIALLY VERIFIED 2026-09-26. The capture chain completes end to end against the live homelab: an in-editor test execution of inbox-capture.json ran the Create Inbox Item node successfully, returning a created next action (id a4b7fb72, title e2e-test, status inbox), and the row was independently confirmed via GET gsd.home.lab/api/next-actions?status=inbox.

IMPORTANT CAVEAT on AC #4: this does NOT prove the token is being presented or accepted. The deployed API is still the pre-auth image and returns 200 on every endpoint, so the call would have succeeded with no credential attached at all. What is proven is that the workflow reaches the API and creates items. Whether the GSD API Token credential is correctly attached and valued can only be tested once the auth-enabled image is deployed, which happens in TASK-004. That verification is the first thing to do after deployment: if the credential is wrong, every capture and all four digest fetches will start returning 401.

CROSS-TASK FINDING, resolves the open question in TASK-004: api.gsd.svc.cluster.local:8000 DOES resolve from the live n8n, so n8n runs inside the k3s cluster and is reached externally through Traefik at n8n.home.lab (192.168.50.240). It is not the instance at 192.168.50.122:5678, which is down entirely. This also eliminates hypothesis 3 in TASK-006: the digest is not failing because it cannot reach the API, since it uses the same cluster-internal hostname that just worked. The remaining digest hypotheses are the missing SMTP credential and the unwired SMTP settings.

Debugging note worth keeping: verifying the webhook via curl proved unreliable because it depended on clipboard contents matching the stored credential, and several rounds of 403 results were invalid for that reason rather than indicating a real fault. The reliable method was an in-editor test execution in n8n, which exercises the downstream nodes without involving the webhook auth layer or any shell state. Use that first next time.

SCOPE EXTENDED 2026-09-26 at user direction. Five acceptance criteria added to cover deploying the auth change to k3s and verifying it there. Rationale: the central claim of this task is that the API requires a token, and that claim cannot be demonstrated while the deployed image still accepts unauthenticated requests. A capture succeeding against a no-auth API is not evidence the credential works. Deployment was also not covered by any other task, so deferring verification to TASK-004 would have left it unowned.

DEPLOYMENT DISCOVERY AND DECISION 2026-09-26. A third API consumer was found on the cluster that neither the repo nor the task accounted for: deployment/mcp in the gsd namespace, image jaymztheking/gsd-mcp:latest, configured with GSD_API_URL=http://api. Its manifests are not in this repository, so it was deployed from elsewhere, and its source could not be located locally. It has no token and no means of obtaining one, so enabling auth breaks its API calls with 401. Its logs show only /health polling, which stays unauthenticated, so whether it is actively doing real API work could not be determined from logs alone.

User decision: proceed with deployment and accept that the MCP server is broken until it is updated separately. Recorded here so the breakage is traceable rather than mysterious later. The MCP server will need to send the X-API-Token header, sourced from the same gsd-secrets API_TOKEN key.

Also confirmed during this inspection: n8n runs in its own n8n namespace on node cherrypi, inside the k3s cluster, which is why api.gsd.svc.cluster.local resolves for it. The cluster is three ARM64 Raspberry Pi nodes running k3s v1.33.6.

DEPLOYED AND VERIFIED IN PRODUCTION 2026-09-26.

Deployment: API_TOKEN added to the existing gsd-secrets Secret by patch, leaving DATABASE_URL, POSTGRES_PASSWORD and N8N_BASIC_AUTH_PASSWORD untouched; stored value confirmed to match what was generated. ARM64 images built and pushed for jaymztheking/gsd-api:latest and jaymztheking/gsd-ui:latest; both deployments rolled out on the three-node k3s cluster.

TWO DEFECTS FOUND ONLY BY DEPLOYING, both invisible locally:

1. The migrate initContainer crash-looped (Init:CrashLoopBackOff). alembic/env.py imports app.config, so Settings is instantiated and requires API_TOKEN even though migrations never authenticate. The token had been deliberately withheld from that container on the reasoning that it needed none. docker compose never caught this because it runs the migration and the server in a single container that already had the token. Fixed by adding API_TOKEN to the initContainer with a comment explaining why a container that never authenticates still needs it. No outage occurred: the old pod kept serving while the new one failed to start.

2. Traefik intercepted /api before the UI nginx, so the token injection was bypassed in k3s and the deployed UI got 401s. Two ingresses existed for gsd.home.lab: gsd-api-ingress on path /api pointing at the api service, and gsd-ingress on / pointing at ui. Traefik matches the more specific path first, so browser calls to /api/* went straight to the API with no token. Verified the injection itself was correct by curling localhost:3000/api/tags from inside the ui pod, which returned 200. Fixed by deleting gsd-api-ingress and its strip-api-prefix middleware so /api falls through to the ui service, where nginx adds the header. The reasoning is documented in k8s/ingress.yaml so the ingress is not reinstated later.

CONSEQUENCE THAT MATTERS FOR TASK-004: anything able to reach gsd.home.lab can use the API without presenting a token, because nginx attaches it in transit. That is inherent to a browser application that cannot hold a secret, and it means the Cloudflare Tunnel must point at the ui service and never at the api service directly, or it will bypass the injection exactly as Traefik did.

PRODUCTION EVIDENCE
- gsd.home.lab/api/health 200 unauthenticated; /api/tags and /api/next-actions 401 with no token and 401 with a wrong token when reached directly; 200 with the correct token.
- After the ingress fix: gsd.home.lab/ 200, /engage 200 (SPA fallback), /api/tags and /api/next-actions 200 with NO token supplied by the client, served through the UI nginx.
- From inside the cluster, api:8000/tags returns 401 without a token and 200 with it, so the API enforces independently of the ingress path.
- The deployed browser bundle (/assets/index-D4L2-qn5.js, 258656 bytes) contains no occurrence of the token, nor does the served index.
- Both pods Ready with 0 restarts, so /health remained open to the probes throughout.
- AC #14, the verification this task was extended for: a capture run through the live n8n workflow created next action c91e49c6 against the auth-enforcing API. The api log shows POST /next-actions 201 Created from 10.42.2.175, the n8n pod, while the same endpoint returns 401 without a token. This proves the GSD API Token credential is correctly attached and valued rather than merely present, which was untestable before deployment.
- AC #5 re-confirmed after auth was restored on the webhook node: POST /webhook/capture returns 403 with no header.

AC #4 FULLY VERIFIED 2026-09-26, both workflows, against the auth-enforcing deployed API.

Capture: POST /next-actions 201 Created from 10.42.2.175 (n8n pod), creating next action c91e49c6.
Digest: all four fetches returned 200 from the same pod -- GET /next-actions?status=inbox, ?status=active, ?status=pending, and GET /projects?status=active. Zero 401s from the n8n pod in the log. The same four endpoints return 401 when called without a token from inside the cluster, so the 200s are evidence the credential authenticated rather than evidence auth was absent.

UNEXPECTED FINDING FOR TASK-006: the digest ran end to end and actually delivered. The Send Digest Email node returned "250 2.0.0 OK ... gsmtp" with james.medaugh@gmail.com accepted and message id 37f94ea0-6d31-d58e-34bc-ac7b8f918f39. This disproves the leading hypothesis recorded in TASK-006, that no SMTP credential was attached: a credential exists and works. Combined with the earlier finding that the cluster-internal API hostname resolves correctly, two of the three hypotheses in TASK-006 are now eliminated. What remains is that the workflow can send when triggered manually but is not being delivered on schedule, which points at the schedule trigger rather than at the pipeline: the trigger is configured triggerAtDay 7, triggerAtHour 19, and the day-of-week numbering plus the instance timezone should be checked first. TASK-006 should be renarrowed accordingly.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added shared-secret authentication to the GSD API, wired every consumer to it, and deployed and verified it on the k3s cluster. The API previously had no authentication of any kind and allow_origins=["*"], which blocked exposing GSD to the internet.

Auth is a token in the X-API-Token header, chosen because the primary client is an iOS Shortcut that can set headers but cannot log in. Compared with secrets.compare_digest; missing and wrong tokens return identical 401s; API_TOKEN has no default so the API refuses to start unprotected. Enforcement is a middleware plus a per-router dependency: the middleware runs before FastAPI decodes the request body, which the dependency alone could not do, and it fails safe if a future router omits the dependency.

The token never reaches the browser. The UI already called the API as same-origin relative paths through a proxy, so nginx (production, via envsubst) and Vite (dev) attach the secret server-side. No frontend code holds it, verified by grepping the deployed 258KB bundle.

Both n8n workflows authenticate with a stored Header Auth credential rather than an environment variable, after the first approach failed on the live instance: n8n blocks $env access in expressions, so {{ $env.GSD_API_TOKEN }} threw "access to env vars denied". The capture webhook separately validates its own distinct secret so the public endpoint cannot be written to anonymously.

Scope was extended mid-task to include deployment, because the central claim could not be demonstrated while the deployed image still accepted unauthenticated requests. That proved worthwhile: deployment exposed two defects invisible locally. The migrate initContainer crash-looped because alembic imports the settings object and so needs API_TOKEN to exist despite never authenticating. Traefik matched its /api ingress before the UI nginx, bypassing the token injection entirely and 401-ing the deployed UI; that ingress was removed so /api routes through the UI service.

Verified in production: data endpoints return 401 unauthenticated and with a wrong token, 200 with the correct one; /health stays open and both pods are Ready with no restarts; the UI loads and reads and writes through its proxy with no client token and no token in the served bundle; a capture through live n8n created next action c91e49c6 with POST /next-actions 201 Created from the n8n pod; and all four weekly-digest fetches returned 200 from that pod with zero 401s, against endpoints that refuse unauthenticated callers. Locally, 13 tests pass and all 17 data endpoints refuse both a missing and a wrong token.

Two consequences are recorded rather than fixed here. The GSD MCP server calls the API with no credential and is now broken, tracked as TASK-007 at the user direction. And because nginx attaches the token in transit, anything that can reach the UI host can use the API without one, so the Cloudflare Tunnel in TASK-004 must point at the ui service and never at api directly.
<!-- SECTION:FINAL_SUMMARY:END -->
