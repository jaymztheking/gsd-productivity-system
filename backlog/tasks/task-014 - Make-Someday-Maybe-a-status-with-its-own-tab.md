---
id: TASK-014
title: Make Someday/Maybe a status with its own tab
status: To Do
assignee: []
created_date: '2026-10-13 01:47'
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
