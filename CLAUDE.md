
<!-- BACKLOG.MD GUIDELINES START -->
<!-- backlog.md-instructions-version: 1.52.0 -->
<CRITICAL_INSTRUCTION>

## Backlog.md Workflow

This project uses Backlog.md for task and project management.

**At the beginning of each conversation in this project, run `backlog instructions overview` before answering or taking action. Re-read it only if you have not read it yet in the current conversation.**

Use the overview to decide whether to search, read, create, or update Backlog tasks.

Before task lifecycle actions, read the matching detailed guide:
- `backlog instructions task-creation` before creating or splitting tasks
- `backlog instructions task-execution` before planning, changing status or assignee, adding a plan or implementation notes, or implementing task work
- `backlog instructions task-finalization` before checking acceptance criteria, writing final summaries, or moving tasks to terminal statuses

Use `backlog <command> --help` before running unfamiliar commands. Help shows options, fields, and examples.

Do not edit Backlog task, draft, document, decision, or milestone markdown files directly. Use the `backlog` CLI so metadata, relationships, and history stay consistent.

</CRITICAL_INSTRUCTION>
<!-- BACKLOG.MD GUIDELINES END -->

<!-- Project-specific. Kept outside the generated block above so `backlog` upgrades do not overwrite it. -->
<CRITICAL_INSTRUCTION>

## Branch Policy for Backlog Tasks

**Create, edit, and archive Backlog tasks on `main`. Branch only when implementation begins.**

Backlog.md runs with `auto_commit: true`, so every `backlog task create|edit|archive` immediately commits to whichever branch is checked out. Task records describe work that has not been done yet and are not tied to any one implementation, so they belong on `main` where every branch and every agent can see them. Tasks created on a feature branch are invisible to anyone not on that branch and go stale if it is abandoned.

- Before running any `backlog` command that writes (`create`, `edit`, `archive`, `complete`), check out `main` first.
- Create the feature branch at the moment you start changing code, not when you plan the work.
- Code changes belong on the feature branch. Backlog writes made *during* implementation — status changes, plans, implementation notes, final summaries — travel with that branch and merge back alongside the code, which is expected.
- If task commits land on a feature branch by mistake, cherry-pick them onto `main` rather than leaving them stranded there.

</CRITICAL_INSTRUCTION>
