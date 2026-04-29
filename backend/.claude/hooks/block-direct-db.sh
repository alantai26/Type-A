#!/bin/bash
# Hook: block-direct-db
# Event: PreToolUse (Bash)
# Blocks raw SQL data manipulation — all schema/data changes must go through
# Alembic migrations or the application layer

set -e

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [ -z "$COMMAND" ]; then
  exit 0
fi

# Allow read-only psql commands (SELECT, \dt, \d, etc.)
# Block any data/schema mutation via psql or direct SQL
DB_WRITE_PATTERNS=(
  "psql.*\bINSERT\b"
  "psql.*\bUPDATE\b"
  "psql.*\bDELETE\b"
  "psql.*\bDROP\b"
  "psql.*\bALTER\b"
  "psql.*\bTRUNCATE\b"
  "psql.*\bCREATE\s+TABLE\b"
  "psql.*\bCREATE\s+INDEX\b"
  "psql.*-c\s+['\"]?\s*(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE)"
)

for pattern in "${DB_WRITE_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qiE "$pattern"; then
    echo "BLOCKED: Direct database writes are not allowed. Use Alembic migrations for schema changes and the app layer for data changes." >&2
    exit 2
  fi
done

exit 0
