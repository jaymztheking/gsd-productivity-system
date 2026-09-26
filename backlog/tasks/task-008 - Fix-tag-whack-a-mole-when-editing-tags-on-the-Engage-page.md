---
id: TASK-008
title: Fix tag whack-a-mole when editing tags on the Engage page
status: To Do
assignee: []
created_date: '2026-09-26 14:17'
labels:
  - ui
  - bug
dependencies: []
references:
  - ui/src/pages/TaskCard.tsx
  - ui/src/pages/EngagePage.tsx
  - ui/src/components/TagSelector.tsx
  - api/app/crud/next_actions.py
priority: high
type: bug
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Editing a task's tags on the Engage page drops tags the user did not touch. Repro reported by the user (2026-09-26): task "Buy Anniversary card" was tagged only energy=easy. In the Engage card editor they added context=errands and time horizon=now and hit Save; the new tags were applied but energy=easy was removed. The result is "tag whack-a-mole": fixing one category knocks out another, so tags can never be set reliably and Engage filtering (which ANDs tags) becomes untrustworthy.

The API update replaces the whole tag set whenever `tag_ids` is sent (api/app/crud/next_actions.py), so whatever the UI sends on save must be the complete intended set. A lead worth checking first: TaskCard (ui/src/pages/TaskCard.tsx) seeds its per-category `selectedTags` state from `action.tags` only once on mount and never resyncs, so the editor state can diverge from the badges shown on the card. Confirm the actual root cause before fixing; do not assume this is it.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Reproduce the reported case: a task tagged only energy=easy, then adding context and time tags in the Engage editor and saving, keeps energy=easy alongside the new tags
- [ ] #2 Saving from the Engage editor never removes a tag in a category the user did not change
- [ ] #3 Explicitly deselecting a tag in the editor and saving still removes that tag
- [ ] #4 The tags pre-selected in the editor always match the tag badges displayed on the card, including after a previous save, a list refresh, or a filter change
- [ ] #5 Behaviour is correct across repeated edit/save cycles on the same card without reloading the page
- [ ] #6 Root cause is recorded in the implementation notes
- [ ] #7 A regression test (UI or API, whichever layer holds the bug) covers the reported scenario
<!-- AC:END -->
