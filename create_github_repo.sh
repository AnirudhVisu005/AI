#!/usr/bin/env bash
# Helper: create a GitHub repo using gh CLI and push current repo

REPO_NAME="AI"
VISIBILITY="private" # change to public if desired

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is not installed. Install it and authenticate before running this script."
  exit 1
fi

echo "Creating GitHub repo '$REPO_NAME' (visibility=$VISIBILITY) and pushing..."
gh repo create "$REPO_NAME" --$VISIBILITY --source=. --remote=origin --push

echo "Done."
