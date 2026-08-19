# Alembic Notes

Reference notes on writing migrations for this project. Covers the manual vs autogenerate decision and the data-migration pattern we hit when renaming enum-like CHECK values.

---

## `alembic revision` vs `alembic revision --autogenerate`

| Command | What it does |
|---|---|
| `alembic revision -m "msg"` | Creates an **empty stub** with the right revision ID and `down_revision` chained. You write `upgrade()` and `downgrade()` by hand. |
| `alembic revision --autogenerate -m "msg"` | Diffs your SQLAlchemy models against the current DB schema and tries to fill in `upgrade()` and `downgrade()` automatically. |

Autogenerate is convenient for pure structural changes — adding a column, creating a new table, changing a column type. For anything semantic (renaming enum values, refactoring a constraint, splitting a column), write it manually.

---

## Two Real Limits of `--autogenerate`

### 1. CHECK constraint changes are flaky

Autogenerate detects most schema deltas, but changes inside raw CHECK constraint strings often slip through. If the constraint goes from:

```python
"status IN ('draft', ...)"
```

to:

```python
"status IN ('planning_in_progress', ...)"
```

autogenerate may miss it, or produce a partial diff. Don't trust it for this. Drop and recreate the constraint manually:

```python
op.drop_constraint('check_outing_status', 'outings', type_='check')
op.create_check_constraint(
    'check_outing_status', 'outings',
    "status IN ('planning_in_progress', 'confirmed', 'completed', 'cancelled')"
)
```

### 2. Autogenerate is DDL-only — it never writes DML

Autogenerate can `ADD COLUMN`, `DROP CONSTRAINT`, `ALTER COLUMN TYPE`. It will **never** write:

```python
op.execute("UPDATE outings SET status = 'planning_in_progress' WHERE status = 'draft'")
```

Data migrations are always manual. If you don't include the `UPDATE` step, existing rows with the old value will violate the new constraint and `alembic upgrade head` will fail with an integrity error.

---

## Pattern: Renaming a CHECK Enum Value

When renaming a value inside a CHECK constraint enum, the order matters. Wrong order = constraint violation mid-migration.

**Correct upgrade order:**
1. `UPDATE` existing rows to the new value first.
2. `DROP` the old constraint.
3. `CREATE` the new constraint with the new allowed values.

**Correct downgrade order:**
1. `DROP` the new constraint.
2. `CREATE` the old constraint back.
3. `UPDATE` rows back to the old value.

Note the asymmetry — on upgrade you update *before* swapping the constraint (so the data is valid against both old and new constraints during the brief gap). On downgrade you swap *before* updating (because if the old constraint is in place first, an `UPDATE` to the original value satisfies it).

Actually — careful re-reading: on upgrade, after the `UPDATE` no rows have the old value, so dropping the old constraint and adding the new one works fine. On downgrade, after the `UPDATE` no rows have the new value, so the old constraint is happy. Either order works as long as the rows currently in the table satisfy whichever constraint is active.

---

## Workflow in This Project

```bash
cd backend
alembic revision -m "<descriptive message>"      # creates empty stub
# fill in upgrade() and downgrade() in the generated file
alembic upgrade head                              # applies to the DB in .env
```

A PreToolUse hook (`.claude/hooks/block-direct-migration-write.sh`) prevents Claude from writing migration files directly — they must go through the alembic CLI so revision IDs and `down_revision` chains are generated correctly. If Claude needs to "write" a migration, it should output the SQL/Python for the user to paste into the generated stub.

---

## Concrete Example From This Project

Migration `9a5cecfca606_rename_outing_and_event_draft_status_to_*.py` renamed the `'draft'` status value to `'planning_in_progress'` on both `outings` and `events`. Manual migration with three steps per table: data update, constraint drop, constraint recreate. See that file for the full pattern.
