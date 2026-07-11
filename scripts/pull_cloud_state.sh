#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

: "${AI_DAILY_REMOTE:?Set AI_DAILY_REMOTE to your SSH host, for example aliyun-ai or user@host}"
REMOTE_DIR="${AI_DAILY_REMOTE_DIR:-/home/lsh/AI-daily-update}"

mkdir -p "$PROJECT_DIR/data/feedback"
mkdir -p "$PROJECT_DIR/data/features"
mkdir -p "$PROJECT_DIR/config"
mkdir -p "$PROJECT_DIR/notes/briefs"
mkdir -p "$PROJECT_DIR/notes/cards"
mkdir -p "$PROJECT_DIR/notes/inbox"
mkdir -p "$PROJECT_DIR/notes/trash"
mkdir -p "$PROJECT_DIR/ppt"

FAILED_PATHS=()

sync_path() {
  local remote_path="$1"
  local local_path="$2"
  if ! rsync -avz "$AI_DAILY_REMOTE:$remote_path" "$local_path"; then
    FAILED_PATHS+=("$remote_path")
  fi
}

sync_path "$REMOTE_DIR/data/feedback/" "$PROJECT_DIR/data/feedback/"
sync_path "$REMOTE_DIR/data/features/" "$PROJECT_DIR/data/features/"
sync_path "$REMOTE_DIR/data/manual_urls.txt" "$PROJECT_DIR/data/manual_urls.txt"
sync_path "$REMOTE_DIR/data/source_proposals.json" "$PROJECT_DIR/data/source_proposals.json"
sync_path "$REMOTE_DIR/data/ppt_source_suggestions.md" "$PROJECT_DIR/data/ppt_source_suggestions.md"
sync_path "$REMOTE_DIR/config/sources.yaml" "$PROJECT_DIR/config/sources.yaml"
sync_path "$REMOTE_DIR/notes/briefs/" "$PROJECT_DIR/notes/briefs/"
sync_path "$REMOTE_DIR/notes/cards/" "$PROJECT_DIR/notes/cards/"
sync_path "$REMOTE_DIR/notes/inbox/" "$PROJECT_DIR/notes/inbox/"
sync_path "$REMOTE_DIR/notes/trash/" "$PROJECT_DIR/notes/trash/"
sync_path "$REMOTE_DIR/ppt/" "$PROJECT_DIR/ppt/"

if [ "${#FAILED_PATHS[@]}" -gt 0 ]; then
  echo "Cloud state pulled from $AI_DAILY_REMOTE:$REMOTE_DIR with ${#FAILED_PATHS[@]} failure(s):"
  for path in "${FAILED_PATHS[@]}"; do
    echo "  FAILED: $path"
  done
else
  echo "Cloud state pulled from $AI_DAILY_REMOTE:$REMOTE_DIR"
fi

echo "Rebuilding local SQLite index from pulled Markdown cards..."
"$PROJECT_DIR/.venv/bin/ai-daily" index

if [ "${#FAILED_PATHS[@]}" -gt 0 ]; then
  exit 1
fi
