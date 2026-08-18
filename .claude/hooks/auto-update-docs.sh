#!/bin/bash
# Hook: auto-update-docs
# Event: Stop
# Blocks Claude from finishing if significant code changes were made
# but CLAUDE.md / README.md were not updated to reflect them.

INPUT=$(cat)

# Don't recurse
STOP_HOOK_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')
if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR" || exit 0

CHANGED_FILES=$(
  git diff --name-only HEAD 2>/dev/null
  git diff --name-only --cached 2>/dev/null
  git ls-files --others --exclude-standard 2>/dev/null
)

if [ -z "$CHANGED_FILES" ]; then
  exit 0
fi

# Only care about structural code changes — things that make docs stale
SIGNIFICANT_PATTERNS=(
  "app/models/.*\.py$"        # New/changed models → update Data Model section
  "app/routes/.*\.py$"        # New/changed endpoints → update API Endpoints section
  "app/services/.*\.py$"      # New services → update Architecture section
  "app/repositories/.*\.py$"  # New repos → update Architecture section
  "alembic/.*\.py$"           # Migrations → update Commands section if new workflow
  "requirements\.txt$"        # Deps → update Stack section
)

SIG_COUNT=0
SIG_FILES=""
for pattern in "${SIGNIFICANT_PATTERNS[@]}"; do
  MATCHES=$(echo "$CHANGED_FILES" | grep -E "$pattern" || true)
  if [ -n "$MATCHES" ]; then
    SIG_COUNT=$((SIG_COUNT + $(echo "$MATCHES" | wc -l | tr -d ' ')))
    SIG_FILES="${SIG_FILES}${MATCHES}\n"
  fi
done

# No significant changes → don't nag
if [ "$SIG_COUNT" -eq 0 ]; then
  exit 0
fi

# Check if docs were also updated
DOCS_UPDATED=false
if echo "$CHANGED_FILES" | grep -qE "(CLAUDE\.md|README\.md)"; then
  DOCS_UPDATED=true
fi

if [ "$DOCS_UPDATED" = false ]; then
  TRIMMED=$(echo -e "$SIG_FILES" | head -15 | sed '/^$/d')
  jq -n --arg files "$TRIMMED" '{
    "decision": "block",
    "reason": ("Significant code changes were made but CLAUDE.md and/or README.md were not updated:\n" + $files + "\n\nUpdate the relevant documentation sections (Data Model, API Endpoints, Architecture, Stack, Commands) to reflect these changes, then continue.")
  }'
  exit 0
fi

exit 0
