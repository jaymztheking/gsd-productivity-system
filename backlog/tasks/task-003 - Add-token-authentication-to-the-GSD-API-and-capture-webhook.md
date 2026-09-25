---
id: TASK-003
title: Add token authentication to the GSD API and capture webhook
status: To Do
assignee: []
created_date: '2026-09-25 18:09'
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
- [ ] #1 All API endpoints that read or modify data require a valid secret token and return 401 with no data when it is missing or wrong
- [ ] #2 The token is presented in an HTTP header that iOS Shortcuts can set, and is verified with a constant-time comparison
- [ ] #3 The token is supplied via environment variable or Kubernetes Secret, is absent from the repository and from committed manifests, and `.env.example` documents it without a real value
- [ ] #4 The n8n capture workflow presents the token on its call to the API, so captures continue to create inbox items end to end
- [ ] #5 The capture webhook itself validates a shared secret, so that public exposure does not permit anonymous writes even if the API is reachable only through it
- [ ] #6 CORS `allow_origins` is narrowed from `["*"]` to the known UI origin(s)
- [ ] #7 The `/health` endpoint remains unauthenticated for Kubernetes probes and exposes no task data
- [ ] #8 Tests cover both the authorized and unauthorized paths for a representative read endpoint and a representative write endpoint
- [ ] #9 Local development via docker compose still works, with the required setup documented in the README
- [ ] #10 Token rotation is documented: where to change the secret and which components must be updated together
<!-- AC:END -->
