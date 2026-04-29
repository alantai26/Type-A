#!/bin/bash
# Hook: block-dangerous
# Event: PreToolUse (Bash)
# Blocks destructive shell commands

set -e

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [ -z "$COMMAND" ]; then
  exit 0
fi

DANGEROUS_PATTERNS=(
  "rm\s+-rf\s+/"
  "rm\s+-rf\s+\.\s"
  "rm\s+-rf\s+\.$"
  "rm\s+-rf\s+\*"
  "DROP\s+TABLE"
  "DROP\s+DATABASE"
  "TRUNCATE\s+TABLE"
  ":\(\)\{.*\}.*;"
  "dd\s+if=/dev"
  "mkfs\b"
  "git\s+push.*--force\b"
  "git\s+push.*-f\b"
  "git\s+reset\s+--hard"
  "git\s+clean\s+-f"
  "git\s+checkout\s+\."
  "chmod\s+-R\s+777"
  "> /dev/sd"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qiE "$pattern"; then
    echo "BLOCKED: Dangerous command detected (pattern: $pattern)" >&2
    exit 2
  fi
done

exit 0
