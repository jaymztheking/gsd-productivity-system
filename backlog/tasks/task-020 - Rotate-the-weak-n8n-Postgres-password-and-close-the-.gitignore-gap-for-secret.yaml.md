---
id: TASK-020
title: >-
  Rotate the weak n8n Postgres password and close the .gitignore gap for
  secret.yaml
status: In Progress
assignee:
  - '@James'
created_date: '2026-10-13 02:30'
updated_date: '2026-10-13 02:30'
labels:
  - n8n
  - security
dependencies: []
references:
  - k8s/n8n/secret.yaml.example
  - .gitignore
priority: high
type: chore
ordinal: 15000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The n8n role on the shared Postgres (namespace postgres, bitnami chart, database n8n) has the password `n8n`. That Postgres is a LoadBalancer on 192.168.50.241:5432 and pg_hba allows md5 password auth from 0.0.0.0/0, so anyone on the LAN can log in as n8n and read or change workflows, executions and the encrypted credential rows. Stored credentials stay protected by N8N_ENCRYPTION_KEY, which is not affected by this change and must not be.

Separately, .gitignore only ignores `*secrets*.yaml`, so a filled-in copy of k8s/n8n/secret.yaml.example or k8s/cloudflared/secret.yaml.example saved as `secret.yaml` would not be ignored. Found while auditing the repo for committed secrets on 2026-10-12; no real secret values were found in the tree or history.

Out of scope, noted for the user: the Postgres superuser password is 6 characters, and the airflow and sports_user roles belong to other projects.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The n8n Postgres role has a new randomly generated password of at least 32 characters, and the old password `n8n` no longer authenticates
- [ ] #2 n8n-secrets holds the new password and n8n runs normally after restart: both GSD workflows activate and the capture webhook responds
- [ ] #3 The new password value never appears in the repo, commit history, task notes, or command output
- [ ] #4 A file named secret.yaml or secrets.yaml anywhere under k8s/ is gitignored, while the *.example templates stay tracked
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. .gitignore: replace *secrets*.yaml with *secret*.yaml, verify example files remain tracked and copies are ignored
2. Generate a 48-char hex password in a single shell pipeline (never printed); patch n8n-secrets first, then ALTER ROLE n8n as the Postgres superuser, then immediately restart n8n so the window with mismatched credentials is seconds long. Rollback if anything fails: ALTER ROLE back and restore the secret
3. Verify: old password rejected, new password from the Secret accepted, n8n logs activate both workflows, capture webhook returns 403 without token
<!-- SECTION:PLAN:END -->
