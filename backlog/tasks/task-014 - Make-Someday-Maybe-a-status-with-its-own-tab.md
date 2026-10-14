---
id: TASK-014
title: Make Someday/Maybe a status with its own tab
status: Done
assignee:
  - '@James'
created_date: '2026-10-13 01:47'
updated_date: '2026-10-14 02:13'
labels:
  - ui
  - api
  - digest
dependencies: []
references:
  - DECISIONS.md
  - README.md
  - api/app/models/enums.py
  - n8n/workflows/weekly-digest.json
  - api/tests/test_digest_pipeline.py
priority: medium
type: feature
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Someday/Maybe is currently modelled as active next actions tagged `#someday`, which is one of the time tags (#now < #today < #week < #month < #someday). James was unsure what belongs in the digest's Someday/Maybe section, and because these items are "active", they show up in Engage alongside real next actions. In GTD, Someday/Maybe is a separate list of things you are not committed to yet, reviewed weekly and either promoted or dropped. A time-horizon tag does not convey that. James has chosen to make it a distinct status with its own tab. This deliberately reverses the "`#someday` Is a Tag, Not a Status" entry in DECISIONS.md, which should be revised rather than left contradicting the code.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Someday exists as a next-action status alongside inbox, active, pending and complete, added by an Alembic migration
- [x] #2 Existing items tagged `#someday` are migrated to the someday status, and the `#someday` tag is retired so it no longer appears in tag pickers or filters
- [x] #3 Someday items do not appear in the Engage view
- [x] #4 A Someday tab lists all someday items, and each can be promoted to active or deleted from there
- [x] #5 An inbox item can be filed straight to someday from the Intake view
- [x] #6 The weekly digest Someday/Maybe section is built from the someday status, and nothing tagged otherwise leaks into it
- [x] #7 DECISIONS.md, README.md and the digest pipeline tests are updated to describe someday as a status
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add someday to ActionStatus; Alembic migration 007 adds the enum value, moves active/pending/inbox items tagged #someday to status someday, deletes the #someday tag (downgrade restores tag, re-tags someday items and sets them active)
2. API: no special casing needed beyond the enum; GET /next-actions?status=someday serves the tab and digest
3. MCP server: add someday to the status enum
4. UI: add someday to ActionStatus type; new Someday tab/page listing someday items with Promote (to active) and Delete; Intake gets a 'Someday' button that files the item as someday with optional title/notes
5. Engage already only fetches active/pending, so someday items drop out automatically; verify
6. n8n digest: add Fetch Someday Items node (status=someday), build Someday/Maybe section from it, remove tag-based filter
7. Tests: API test for someday status (create, list, promote, excluded from active); update digest pipeline tests to use status
8. Docs: revise DECISIONS.md entry, README tag table and status list, FILE-GLOSSARY digest description
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented on branch task-014-someday-status (commit c2312e8, plus bf16c45 syncing package-lock.json with @types/node, which npm ci needed).

Verification, 2026-10-13:
- Migration 007 against a throwaway postgres:15-alpine (same as k3s): upgrade moved an open #someday-tagged item to someday and kept its +easy tag, left a completed #someday item complete, deleted the tag; downgrade restored #someday on the item and set it active; re-upgrade clean. ALTER TYPE runs in an autocommit block because Postgres cannot use a new enum value in the transaction that added it. Downgrade leaves 'someday' in the enum (Postgres cannot drop enum values).
- API: new tests/test_someday.py (4 tests) plus new shared conftest api_client fixture; full unit suite 65 passed.
- Digest: test_digest_pipeline.py rewritten for the status and now sends X-API-Token (it had been unable to run since TASK-003); 12 passed against a local uvicorn on the Postgres container. Compile Digest JS executed in node against the local API data: Someday / Maybe section lists exactly the two someday items.
- UI (Playwright, 375px viewport, Vite dev against the local API): Intake Someday button files the item and it appears on the Someday tab; Make Active moves it to Engage; someday items absent from Engage; Time Horizon picker shows #now..#month only. The four Intake triage buttons overflowed at 375px (scrollWidth 466), so they are now a 2x2 grid (scrollWidth 375).
- Also: TaskCard status select gains Someday (removes the card from Engage); MCP create_task status enum includes someday.

Not yet deployed: API/UI images, migration on k3s Postgres, MCP image, and re-import of weekly-digest.json into live n8n (needs an n8n restart afterwards per TASK-018 README note).

Deployed 2026-10-13 (~20:15 MT) from main 65355f3: images jaymztheking/gsd-api@sha256:bf35def8, gsd-ui@sha256:74dbadb3, gsd-mcp@sha256:9ac7511c (previous images kept as :pre-areas for rollback). API init container ran migrations 007-009 (alembic now 009). DB backup taken first: ~/gsd-backups/gsd-pre-areas-20261013-1956.dump. Checked live through gsd.home.lab: the API returns areas/someday/tags (#someday gone), Engage order populated, UI bundle has the new features.

n8n: updated digest imported over wayvHwteu1n9IPRk with its live credential IDs, published with the CLI, then n8n restarted. Startup activated GSD Weekly Review Digest and GSD Inbox Capture. Exported published version shows the Sunday 19:00 America/Denver trigger and Fetch Someday Items (status=someday) with the GSD API Token credential. Capture webhook without a token returns 403 as expected. The two #someday-tagged items were both already complete, so no task moved to Someday. First digest with the new section: Sun 2026-10-18 19:00 MT.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Someday/Maybe is now a next-action status instead of the #someday time tag. Migration 007 adds the enum value, moves open #someday items to it and deletes the tag. A new Someday tab lists them with Make Active and Delete, Intake triage has a Someday button (triage buttons now a 2x2 grid to fit phones), and the Engage status select can send a task to Someday. The weekly digest fetches ?status=someday for its Someday/Maybe section. DECISIONS.md, README and FILE-GLOSSARY updated; digest pipeline tests rewritten for the status and fixed to send the API token. Verified with 65 API unit tests, 12 digest pipeline tests against Postgres 15, a migration up/down/up run on Postgres 15, the digest code executed in node, and a Playwright click-through at phone width. Deployment to k3s and the n8n re-import are still to do.
<!-- SECTION:FINAL_SUMMARY:END -->
