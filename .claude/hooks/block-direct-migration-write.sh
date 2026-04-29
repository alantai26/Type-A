#!/bin/bash
# Hook: block-direct-migration-write
# Event: PreToolUse (Edit|Write)
# Blocks direct edits/writes to alembic/versions/ — Claude must use the alembic CLI instead.

set -e

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

if echo "$FILE_PATH" | grep -q 'alembic/versions/'; then
  cat >&2 <<'EOF'
BLOCKED: Migration files must be created via the alembic CLI, not direct Write/Edit.

Output the commands for the user to run instead. Example:
  cd backend
  alembic revision -m "<descriptive message>"

Alembic generates the stub with a proper revision ID. Then guide the user through editing the generated file (don't try to edit it yourself — this hook will block that too).
EOF
  exit 2
fi

exit 0
