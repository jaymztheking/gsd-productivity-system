---
id: TASK-006
title: 'Fix the weekly review digest, which is not being delivered'
status: To Do
assignee: []
created_date: '2026-09-26 03:55'
labels:
  - n8n
  - digest
  - email
dependencies:
  - TASK-003
  - TASK-004
references:
  - n8n/workflows/weekly-digest.json
  - docker-compose.yml
  - api/tests/test_digest_pipeline.py
  - LOG.md
priority: medium
type: bug
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The GSD Weekly Review Digest is not arriving. The workflow (`n8n/workflows/weekly-digest.json`) is marked `active: true` and is meant to run Sundays at 19:00, query the API for inbox items, active items, pending items and projects, compile an HTML summary, and email it. James reports it has not been working. LOG.md and commit history show a previous fix attempt plus integration tests (`api/tests/test_digest_pipeline.py`), so the data pipeline itself has been exercised before; what is failing now is unconfirmed.

Three candidate causes were identified by inspecting the workflow, in rough order of likelihood. All are hypotheses and none has been verified against the running instance:

1. **No SMTP credential attached.** The `Send Digest Email` node carries no `credentials` key in the exported workflow. An n8n `emailSend` node with no SMTP credential cannot send, which would break delivery while leaving every earlier node green. Note that n8n exports reference credentials by id rather than embedding them, so absence in the JSON is suggestive rather than conclusive; the live instance must be checked.

2. **SMTP settings are documented but never wired up.** `.env.example` defines `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` and `DIGEST_RECIPIENT`, but the n8n service in `docker-compose.yml` passes none of them into the container, and the workflow hardcodes `james.medaugh@gmail.com` as both sender and recipient instead of reading them. So the documented configuration path does not connect to anything.

3. **Cluster-internal API hostname may be unreachable from n8n.** All four fetch nodes call `http://api.gsd.svc.cluster.local:8000`, a name that only resolves inside the k3s cluster. If the live n8n runs outside the cluster — which the capture webhook at `192.168.50.122:5678` suggests, since every Service in `k8s/` is ClusterIP with no NodePort — all four fetches fail and the digest never has data to send. This is the same unresolved question TASK-004 settles, which is why this task depends on it.

Worth also confirming the schedule itself fires: the trigger is configured `triggerAtDay: 7, triggerAtHour: 19`, and day-of-week numbering should be checked against the n8n version in use so that 7 means Sunday rather than being out of range.

Depends on TASK-003 because the digest fetches will need the new API token, and on TASK-004 because that task establishes where n8n actually runs and how it reaches the API.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The actual point of failure is identified from n8n execution history for the digest workflow, naming which node fails and with what error, rather than inferred from the workflow definition
- [ ] #2 Whether the four API fetch calls succeed from the live n8n instance is confirmed, with the working API base URL recorded
- [ ] #3 An SMTP credential is attached to the email node and a test send succeeds
- [ ] #4 Sender and recipient come from configuration rather than hardcoded addresses, with the corresponding variables passed into the n8n container and documented in `.env.example`
- [ ] #5 The schedule trigger is confirmed to fire on Sunday at 19:00 in the expected timezone, verified against the n8n version in use rather than assumed from the day number
- [ ] #6 A manual run of the workflow produces a digest email containing real data in all four sections
- [ ] #7 A scheduled run is confirmed delivered without manual intervention
- [ ] #8 The digest email renders legibly in a mail client, with empty sections handled gracefully rather than shown as broken or blank blocks
<!-- AC:END -->
