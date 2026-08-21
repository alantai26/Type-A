---
name: wrap-ticket
description: Finish a TypeA ticket (e.g. /wrap-ticket TYP-70). Writes the per-ticket handoff doc, prepends an entry to CURRENT_HANDOFF, updates CLAUDE.md, refreshes memory, then outputs ONLY the PR body markdown for copy-paste. Use when a ticket's implementation is done and it's time to document and open the PR.
---

# Wrap ticket

Document the work, then hand Alan a PR body he can paste. Docs first, PR body last.

`$ARGUMENTS` is the ticket ID (e.g. `TYP-70`). If absent, infer it from the branch name and confirm.

## Hard rules

- **Never run git commands that mutate state.** No `commit`, `push`, `gh pr create`. Read-only inspection only. Alan opens the PR himself.
- **The PR body is the last thing in the response, and it is the only command-free output he needs.** Do not print `git commit`/`git push`/`gh pr create` walls — he has explicitly asked for the PR markdown alone.
- **PRs target `dev`**, never `main`.

## Steps

### 1. Establish what actually changed

```
git status --short
git diff --stat HEAD
git diff HEAD          # skim the real diff, not just names
```

Read the changed files. Don't document from memory of the session — document from the diff. If work happened in Alan's IDE that you didn't write, it still needs documenting.

### 2. Write the per-ticket handoff — `docs/TYP_<N>_HANDOFF.md`

Write this for anything substantial (roughly 4+ points, or anything with non-obvious design decisions). Skip for trivial tickets and say you're skipping.

Follow the established structure:

```markdown
# TYP-<N> Handoff — <short title>

**Status:** <Done / In review> (PR #<n>, commit `<sha>`)
**Branch:** `<branch>`
**Estimate:** <n> pts

<1–3 sentence framing: what this ticket is in the arc of the project>

---

## What shipped in this ticket

### <subsystem — e.g. Backend, iOS, Seed script>
<what changed and why, with real file paths and real numbers>

## Design decisions worth knowing

### <decision as a heading>
<the reasoning, including what was rejected and why>

## ⚠️ Known issues / gotchas   (only if there are any)

## Files touched

| file | change |
|---|---|

## How to verify locally

<exact commands + expected output; include a SQL query if the ticket touches data>

## PR description (copy-paste)

<the same markdown emitted in step 6>

## What's next

<the natural follow-up ticket, plus anything to carry forward>
```

**Quality bar:** state real numbers, real file paths, real column names. Record decisions that were *rejected* and why — that's what makes these useful six months later. Surface anything discovered that's out of scope but real (a stale doc, a data-hygiene problem, a latent bug) rather than dropping it.

### 3. Prepend an entry to `docs/CURRENT_HANDOFF.md`

Insert directly below the `## Recent decisions` header (newest first). Format:

```markdown
### <YYYY-MM-DD> — TYP-<N> shipped: <short title>

- **Merged in PR #<n>** (commit `<sha>`). Branch `<branch>`. Full breakdown in `docs/TYP_<N>_HANDOFF.md`.
- <bold lead-in> — the decision or change, one bullet each
```

If the same date already has an entry, use `### <date> (later) — ...`.

Then update the `## Current state` section (Backend / iOS / ML / Design) if this ticket changed it, and resolve or add to `## Active questions / open decisions`.

### 4. Update `CLAUDE.md`

Required — the `auto-update-docs.sh` Stop hook blocks completion if `app/models/`, `app/routes/`, `app/services/`, `app/repositories/`, `alembic/`, or `requirements.txt` changed without a `CLAUDE.md` or `README.md` edit.

Sections to check, in order:
- **Completed tickets** — add a bullet (backend or iOS list). Always.
- **API Endpoints** — new/changed endpoints, with the ticket ID
- **Data Model** — new tables/columns + the migration revision ID
- **Architecture** — new modules or layers
- **Stack** — new dependencies
- **Commands** — new scripts or workflows
- **Repo Layout** / **Claude Code Hooks** — if either changed

Fix any staleness noticed in passing, and mention it. Project name is always **TypeA** — never "Type A" or "Type-A".

### 5. Update memory

Write to the project memory dir if the ticket produced anything durable: a new working preference from Alan, a project decision not derivable from the code, or a correction to an existing memory. Update existing files rather than duplicating; add the one-line pointer to `MEMORY.md`. Skip if nothing qualifies — don't manufacture entries.

### 6. Offer the Linear update

Ask before writing: whether to move the ticket to Done via `mcp__linear__save_issue`. Don't do it unprompted — the PR merge may be what he wants to trigger it.

### 7. Output the PR body — and nothing after it

End the response with a single fenced `markdown` block, in his established format:

````
```markdown
## Summary
- <3–5 bullets: what changed and why it matters, not a file list>

## Implementation notes
- <design decisions a reviewer needs; anything non-obvious; anything deliberately deferred>

## Test plan
- [ ] <concrete verifiable steps — commands to run, screens to check, expected values>

Fixes TYP-<N>
```
````

Include `Fixes TYP-<N>` so Linear auto-closes. If the PR covers two tickets, add a `Fixes` line for each.

No prose after this block. No git commands anywhere in the response.
