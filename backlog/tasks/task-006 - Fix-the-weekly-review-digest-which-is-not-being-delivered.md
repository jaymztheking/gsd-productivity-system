---
id: TASK-006
title: Fix the weekly digest not firing on schedule
status: In Progress
assignee:
  - '@claude'
created_date: '2026-09-26 03:55'
updated_date: '2026-09-26 16:02'
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
The GSD Weekly Review Digest does not arrive, but the pipeline itself works. On 2026-09-26, while verifying TASK-003, the workflow was run manually against the live cluster and completed end to end: all four API fetches returned 200, the digest compiled, and the email was accepted by Gmail with response `250 2.0.0 OK ... gsmtp`, message id 37f94ea0-6d31-d58e-34bc-ac7b8f918f39. So the problem is the trigger, not the data pipeline or delivery.

Two of the three causes originally suspected are now eliminated:

- **SMTP credential missing** — disproved. A credential is attached and a manual run delivered successfully.
- **Cluster-internal API hostname unreachable** — disproved. n8n runs inside the k3s cluster in the `n8n` namespace on node cherrypi, and `api.gsd.svc.cluster.local:8000` resolves for it; all four fetches returned 200 and are visible in the api pod log from 10.42.2.175.

What remains is that a manual run works while a scheduled run never arrives. The trigger is configured `triggerAtDay: 7, triggerAtHour: 19`, and the README describes the intent as Sunday 19:00. Day-of-week numbering is the obvious first suspect: n8n uses 0 for Sunday in its schedule trigger, so 7 may be out of range or interpreted unexpectedly, in which case the trigger never fires. Timezone is the second: n8n evaluates schedules in its own configured timezone (`GENERIC_TIMEZONE`), which if unset defaults to UTC and would fire at a different local hour than intended.

Also worth confirming the workflow is actually active in the live instance, since an inactive workflow still runs manually but is never triggered on a schedule, and imports do not preserve the active flag.

Note the workflow was re-imported during TASK-003, so check for duplicate copies of "GSD Weekly Review Digest" in the workflows list; n8n creates new workflows on import rather than replacing them, and a stale inactive copy alongside an active one is confusing to diagnose.

One hardcoded-configuration issue found earlier still stands and is worth fixing while in here: the workflow hardcodes `james.medaugh@gmail.com` as both sender and recipient, while `.env.example` documents `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` and `DIGEST_RECIPIENT` that the n8n service in `docker-compose.yml` never passes into the container. The documented configuration path connects to nothing.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The reason scheduled runs do not fire is identified from the n8n execution history and the trigger configuration, distinguishing a trigger that never fires from one that fires at an unexpected time
- [ ] #2 The schedule trigger day-of-week value is corrected against the numbering used by the n8n version in use, so that it resolves to Sunday
- [ ] #3 The timezone the schedule is evaluated in is confirmed, and 19:00 means 19:00 local rather than UTC
- [ ] #4 The workflow is confirmed active in the live instance, and any duplicate copies created by re-import are removed
- [ ] #5 Sender and recipient come from configuration rather than hardcoded addresses, with the variables actually passed into the n8n container and documented in `.env.example`
- [ ] #6 A scheduled run is confirmed delivered without manual intervention, observed on the next scheduled occurrence or by temporarily setting the schedule to a near-future time
- [ ] #7 The digest email renders legibly in a mail client, with empty sections handled gracefully rather than shown as broken or blank blocks
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Findings (2026-09-26): live n8n is 2.38.7 in namespace n8n (not this repo's k8s/n8n manifest), no GENERIC_TIMEZONE so it runs in UTC. There are SIX 'GSD Weekly Review Digest' workflows and NONE is active/published, so the schedule never fires. Every live copy's trigger is {triggerAtHour: 19} with no field, which would run daily at 19:00 at a pseudo-random minute. The repo copy's triggerAtDay: 7 is ignored without field: weeks. n8n source confirms weekday values are 0=Sunday..6=Saturday.
1. Repo: trigger -> field weeks, triggerAtDay [0], triggerAtHour 19, triggerAtMinute 0; workflow settings.timezone America/Denver (user is in Mountain time). DONE on branch.
2. Sender/recipient from configuration (approach pending user decision).
3. Live: import the fixed workflow over the copy that holds the working credentials (wayvHwteu1n9IPRk, last updated during TASK-003), publish it, archive the other five digest copies (pending user approval).
4. Verify: temporarily schedule a near-future time (or wait for Sunday 19:00 MT), confirm a trigger-mode execution and email delivery, check rendering incl. empty sections, then restore the Sunday schedule.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Renarrowed 2026-09-26 after TASK-003 deployment testing. A manual run delivered successfully, which eliminated the missing-SMTP-credential and unreachable-API hypotheses this task was created with. Evidence: four fetches 200 from the n8n pod in the api log, and SMTP response 250 2.0.0 OK from Gmail. Scope is now the schedule trigger rather than the pipeline. Also note the digest now authenticates to the API using the GSD API Token credential added in TASK-003, so if it ever starts returning 401 the credential is the first thing to check.
<!-- SECTION:NOTES:END -->
