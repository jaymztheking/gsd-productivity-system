---
id: TASK-020
title: >-
  Rotate the weak n8n Postgres password and close the .gitignore gap for
  secret.yaml
status: Done
assignee:
  - '@James'
created_date: '2026-10-13 02:30'
updated_date: '2026-10-13 02:33'
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
- [x] #1 The n8n Postgres role has a new randomly generated password of at least 32 characters, and the old password `n8n` no longer authenticates
- [x] #2 n8n-secrets holds the new password and n8n runs normally after restart: both GSD workflows activate and the capture webhook responds
- [x] #3 The new password value never appears in the repo, commit history, task notes, or command output
- [x] #4 A file named secret.yaml or secrets.yaml anywhere under k8s/ is gitignored, while the *.example templates stay tracked
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. .gitignore: replace *secrets*.yaml with *secret*.yaml, verify example files remain tracked and copies are ignored
2. Generate a 48-char hex password in a single shell pipeline (never printed); patch n8n-secrets first, then ALTER ROLE n8n as the Postgres superuser, then immediately restart n8n so the window with mismatched credentials is seconds long. Rollback if anything fails: ALTER ROLE back and restore the secret
3. Verify: old password rejected, new password from the Secret accepted, n8n logs activate both workflows, capture webhook returns 403 without token
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-12:
- .gitignore: *secrets*.yaml/yml -> *secret*.yaml/yml, negations aligned to *secret*.example.*. Verified: secret.yaml and secrets.yaml under k8s/ are ignored; all three *.example templates remain tracked.
- Pre-checks: pg_hba is md5 from 0.0.0.0/0 (so the weak password was usable from the LAN via the 192.168.50.241 LoadBalancer); log_statement=none and password_encryption=scram-sha-256, so ALTER ROLE does not log the value.
- Rotation: 48-char hex password generated inside the script; n8n-secrets patched via stdin, then ALTER ROLE n8n via psql stdin as the superuser, then n8n rollout restart. Rollback path (restore secret) was not needed. N8N_ENCRYPTION_KEY untouched.
- Verified: old password 'n8n' rejected on localhost and via the LAN LoadBalancer; new password from the Secret authenticates; new n8n pod activated GSD Inbox Capture and GSD Weekly Review Digest; capture webhook returns 403 without token. New value found in 0 tracked files, 0 commits, 0 untracked files; command output printed only its length.
- Not changed (other projects / shared infra, raised with user): Postgres superuser password is 6 chars; airflow and sports_user roles exist on the same LAN-exposed Postgres.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Rotated the n8n Postgres role from the password 'n8n' to a random 48-char value, updated n8n-secrets and restarted n8n; the old password is now rejected (including via the LAN LoadBalancer) and n8n came back with both GSD workflows active and the capture webhook responding. The value was never printed or written to the repo. Widened .gitignore from *secrets*.yaml to *secret*.yaml so filled-in copies of the cloudflared and n8n secret templates are ignored, with the .example files still tracked.
<!-- SECTION:FINAL_SUMMARY:END -->
