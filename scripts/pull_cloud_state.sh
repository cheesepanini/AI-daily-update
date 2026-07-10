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

rsync -avz "$AI_DAILY_REMOTE:$REMOTE_DIR/data/feedback/" "$PROJECT_DIR/data/feedback/" || true
rsync -avz "$AI_DAILY_REMOTE:$REMOTE_DIR/data/features/" "$PROJECT_DIR/data/features/" || true
rsync -avz "$AI_DAILY_REMOTE:$REMOTE_DIR/data/manual_urls.txt" "$PROJECT_DIR/data/manual_urls.txt" || true
rsync -avz "$AI_DAILY_REMOTE:$REMOTE_DIR/data/source_proposals.json" "$PROJECT_DIR/data/source_proposals.json" || true
rsync -avz "$AI_DAILY_REMOTE:$REMOTE_DIR/data/ppt_source_suggestions.md" "$PROJECT_DIR/data/ppt_source_suggestions.md" || true
rsync -avz "$AI_DAILY_REMOTE:$REMOTE_DIR/config/sources.yaml" "$PROJECT_DIR/config/sources.yaml" || true
rsync -avz "$AI_DAILY_REMOTE:$REMOTE_DIR/notes/briefs/" "$PROJECT_DIR/notes/briefs/" || true
rsync -avz "$AI_DAILY_REMOTE:$REMOTE_DIR/notes/cards/" "$PROJECT_DIR/notes/cards/" || true
rsync -avz "$AI_DAILY_REMOTE:$REMOTE_DIR/notes/inbox/" "$PROJECT_DIR/notes/inbox/" || true
rsync -avz "$AI_DAILY_REMOTE:$REMOTE_DIR/notes/trash/" "$PROJECT_DIR/notes/trash/" || true
rsync -avz "$AI_DAILY_REMOTE:$REMOTE_DIR/ppt/" "$PROJECT_DIR/ppt/" || true

echo "Cloud state pulled from $AI_DAILY_REMOTE:$REMOTE_DIR"
