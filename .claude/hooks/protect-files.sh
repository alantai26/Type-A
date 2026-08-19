#!/bin/bash
# Hook: protect-files
# Event: PreToolUse (Edit|Write)
# Blocks:
#   1. Edits to sensitive files (.env, .git/, credentials, keys)
#   2. Writing sensitive VALUES into OTHER files (env-looking assignments,
#      DB URLs with baked-in credentials, inline private keys, etc.)

set -e

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# .env.example is a committed template with placeholder values — allow edits
# and skip content scan. Must come before both Part 1 and Part 2 because the
# `\.env\.` filepath pattern below would otherwise match it.
if echo "$FILE_PATH" | grep -qE -- "\.env\.example$"; then
  exit 0
fi

# --- Part 1: block edits to sensitive file PATHS -----------------------------

PROTECTED_PATTERNS=(
  "\.env$"
  "\.env\."
  "/\.git/"
  "\.git$"
  "credentials"
  "secrets"
  "\.pem$"
  "\.key$"
  "\.p12$"
  "\.pfx$"
  "id_rsa"
  "id_ed25519"
)

for pattern in "${PROTECTED_PATTERNS[@]}"; do
  if echo "$FILE_PATH" | grep -qiE -- "$pattern"; then
    echo "BLOCKED: Cannot edit protected file: $FILE_PATH" >&2
    exit 2
  fi
done

# --- Part 2: block writing sensitive VALUES into other files -----------------

if [ "$TOOL_NAME" = "Write" ]; then
  CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty')
elif [ "$TOOL_NAME" = "Edit" ]; then
  CONTENT=$(echo "$INPUT" | jq -r '.tool_input.new_string // empty')
else
  exit 0
fi

if [ -z "$CONTENT" ]; then
  exit 0
fi

VALUE_PATTERNS=(
  # env-var-style assignments carrying real values (not doc references)
  "DATABASE_URL[[:space:]]*=[[:space:]]*[a-zA-Z]+[+a-zA-Z]*://[^[:space:]]+@"
  "SUPABASE_[A-Z_]+_KEY[[:space:]]*=[[:space:]]*[a-zA-Z0-9]"
  "SUPABASE_URL[[:space:]]*=[[:space:]]*https?://[a-z0-9]+\\.supabase"
  "SUPABASE_JWT_SECRET[[:space:]]*="

  # Postgres/MySQL/Mongo URLs with embedded credentials (user@host form)
  "postgres(ql)?[+a-z]*://[a-zA-Z0-9_-]+@[a-zA-Z0-9.-]+:[0-9]+/"
  "mysql://[a-zA-Z0-9_-]+:[^@]*@"
  "mongodb(\\+srv)?://[a-zA-Z0-9_-]+:[^@]*@"

  # Inline private keys pasted into a doc/config
  "-----BEGIN (RSA|EC|OPENSSH|DSA|PGP) PRIVATE KEY-----"

  # AWS access key IDs
  "AKIA[0-9A-Z]{16}"

  # Heuristic: SECRET/TOKEN/PASSWORD/API_KEY = long-looking value
  "(API_KEY|SECRET|TOKEN|PASSWORD)[[:space:]]*=[[:space:]]*[a-zA-Z0-9._+/=-]{20,}"
)

for pattern in "${VALUE_PATTERNS[@]}"; do
  if echo "$CONTENT" | grep -qE -- "$pattern"; then
    echo "BLOCKED: Content going to $FILE_PATH looks like it contains a secret or credential." >&2
    echo "Matched pattern: $pattern" >&2
    echo "If intentional (docs meta-discussing env shape), reference the value by NAME not by literal." >&2
    exit 2
  fi
done

exit 0
