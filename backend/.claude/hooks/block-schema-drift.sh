#!/bin/bash
# Hook: block-schema-drift
# Event: Stop
# Ensures consistency: if SQLAlchemy models changed, a migration must exist.
# If Pydantic schemas changed, reminds about frontend TypeScript types.

set -e

INPUT=$(cat)

# Don't recurse — if this hook already forced Claude to continue, let it finish
STOP_HOOK_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')
if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR" || exit 0

# Collect all changed files (staged, unstaged, and new untracked)
CHANGED_FILES=$(
  git diff --name-only HEAD 2>/dev/null
  git diff --name-only --cached 2>/dev/null
  git ls-files --others --exclude-standard 2>/dev/null
)

if [ -z "$CHANGED_FILES" ]; then
  exit 0
fi

MODEL_CHANGED=false
MIGRATION_PRESENT=false
PYDANTIC_CHANGED=false

# SQLAlchemy model files (not __init__.py, not schemas)
if echo "$CHANGED_FILES" | grep -qE "app/models/[a-z_]+\.py$" | grep -vE "__init__|schema"; then
  MODEL_CHANGED=true
fi

# More precise: check for actual model changes
if [ "$MODEL_CHANGED" = false ]; then
  if echo "$CHANGED_FILES" | grep -qE "app/models/.*\.py$"; then
    # Check if any changed model file contains Column/mapped_column definitions
    for f in $(echo "$CHANGED_FILES" | grep -E "app/models/.*\.py$"); do
      if [ -f "$f" ] && grep -qE "(mapped_column|Column|relationship|__tablename__)" "$f" 2>/dev/null; then
        MODEL_CHANGED=true
        break
      fi
    done
  fi
fi

# Alembic migration created
if echo "$CHANGED_FILES" | grep -qE "alembic/versions/.*\.py$"; then
  MIGRATION_PRESENT=true
fi

# Pydantic schema files
if echo "$CHANGED_FILES" | grep -qE "app/(models|schemas)/.*schema.*\.py$|app/schemas/.*\.py$"; then
  PYDANTIC_CHANGED=true
fi

REASONS=""

if [ "$MODEL_CHANGED" = true ] && [ "$MIGRATION_PRESENT" = false ]; then
  REASONS="${REASONS}- SQLAlchemy models were modified but no Alembic migration was created. Run: alembic revision --autogenerate -m \"description\"\n"
fi

if [ "$PYDANTIC_CHANGED" = true ]; then
  REASONS="${REASONS}- Pydantic schemas were modified. Ensure corresponding frontend TypeScript types are updated if applicable.\n"
fi

if [ -n "$REASONS" ]; then
  jq -n --arg reason "Schema drift detected. Fix before finishing:\n$REASONS" '{
    "decision": "block",
    "reason": $reason
  }'
  exit 0
fi

exit 0
