---
name: start-ticket
description: Start work on a TypeA Linear ticket (e.g. /start-ticket TYP-70). Gathers context from CURRENT_HANDOFF, Linear, and the actual codebase; verifies the ticket against reality; surfaces decisions that need Alan's input; outputs a step plan. Use whenever beginning a new ticket or resuming one after a break.
---

# Start ticket

Gather context, verify it, and produce a plan. **Do not write implementation code during this skill** — it ends with a plan and a question.

`$ARGUMENTS` is the ticket ID (e.g. `TYP-70`). If absent, read `docs/CURRENT_HANDOFF.md` + Linear to figure out what's next and confirm with Alan before proceeding.

## Hard rules

- **Never run git commands that mutate state.** No `checkout`, `commit`, `push`, `gh pr create`. Read-only inspection (`git log`, `status`, `diff`, `show`, `branch --list`) is fine. Alan drives git himself — give him the branch name, let him create it.
- **Never edit `alembic/versions/` directly.** If a migration is needed, output the `alembic revision -m "msg"` command for Alan to run, then edit the generated stub.
- **Reference env vars by name, never by literal value.** `protect-files.sh` blocks secret-shaped content, and it is correct to do so.

## Steps

### 1. Read the living context

Read the top ~3 entries under `## Recent decisions` in `docs/CURRENT_HANDOFF.md`, plus its `## Current state` and `## Active questions / open decisions` sections. This is the source of truth for what just happened and what's unresolved.

If a `docs/TYP_<N>_HANDOFF.md` exists for a directly related ticket, skim it.

### 2. Pull the ticket

Use `mcp__linear__get_issue` with `includeRelations: true`. Capture: full description, estimate, status, `gitBranchName`, and blocked-by/blocks relations.

If blocked by something not yet Done, say so immediately and stop.

### 3. Orient in the repo (read-only)

- `git log --oneline -10`, `git status --short`, current branch
- Locate every file the ticket names

### 4. Verify the ticket against reality — do not skip this

**Tickets go stale between filing and starting.** Check each claim the ticket makes about the codebase before planning around it. Common drift:

- Files/modules the ticket names may not exist, or live elsewhere (a ticket once specified `app/routes/predict.py`; the endpoint was actually in `app/routes/places.py`)
- Dependencies the ticket assumes may not be installed — check `requirements.txt` *and* the venv (`./venv/bin/python -c "import x"`), they disagree
- Directories may already exist at a different level than specified
- The ticket may ignore the layered architecture (Route → Service → Repository); business logic belongs in a service, not a route
- Schema/data assumptions — query the local DB with `psql` (SELECT only; writes are hook-blocked) rather than trusting `CLAUDE.md`

Report every discrepancy found. These are the most valuable output of this skill.

### 5. Check the data if the ticket touches it

For ML/data tickets, actually query the local dev DB. Row counts, distinct values on any column being used as a feature or filter, duplicates. Assume nothing.

### 6. Output

Produce, in this order:

1. **Context** — what the ticket is, what it depends on, what shipped just before it
2. **Discrepancies** — everything from step 4, stated plainly
3. **Decisions needed** — anything where two readings lead to materially different work. Use `AskUserQuestion` when there are 2–4 real options; give a recommendation, don't just survey. Skip this section if there's nothing genuinely ambiguous.
4. **Step plan** — ordered, concrete, file-by-file
5. **Branch name** — from Linear's `gitBranchName`, for Alan to create
6. **The ask** — per Alan's "let me try first" preference, offer three modes: (a) hints + scaffolding, he writes the core logic; (b) build it end to end, he reviews; (c) walk through the concepts first. Default to asking rather than assuming.

Then **stop**. Wait for his answer before writing implementation code.

## Notes

- Estimates are capped at 8 points. If the work looks bigger, say so and propose a split.
- PRs target `dev`, never `main`.
- On iOS tickets: function first, polish last. Wire all data with minimal styling, then do one UI/UX pass.
- Alan is learning — prefer explaining the *why* over pasting the *what*.
