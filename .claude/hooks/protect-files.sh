#!/bin/bash
# Hook: protect-files
# Event: PreToolUse (Edit|Write)
# Blocks edits to sensitive files: .env, .git/, credentials, keys, secrets

set -e

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

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
  if echo "$FILE_PATH" | grep -qiE "$pattern"; then
    echo "BLOCKED: Cannot edit protected file: $FILE_PATH" >&2
    exit 2
  fi
done

exit 0
