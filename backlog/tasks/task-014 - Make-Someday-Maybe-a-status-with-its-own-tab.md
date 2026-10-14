---
id: TASK-014
title: Make Someday/Maybe a status with its own tab
status: In Progress
assignee:
  - '@James'
created_date: '2026-10-13 01:47'
updated_date: '2026-10-14 01:34'
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
- [ ] #1 Someday exists as a next-action status alongside inbox, active, pending and complete, added by an Alembic migration
- [ ] #2 Existing items tagged `#someday` are migrated to the someday status, and the `#someday` tag is retired so it no longer appears in tag pickers or filters
- [ ] #3 Someday items do not appear in the Engage view
- [ ] #4 A Someday tab lists all someday items, and each can be promoted to active or deleted from there
- [ ] #5 An inbox item can be filed straight to someday from the Intake view
- [ ] #6 The weekly digest Someday/Maybe section is built from the someday status, and nothing tagged otherwise leaks into it
- [ ] #7 DECISIONS.md, README.md and the digest pipeline tests are updated to describe someday as a status
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
