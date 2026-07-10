#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

: "${AI_DAILY_REMOTE:?Set AI_DAILY_REMOTE to your SSH host, for example aliyun-ai or user@host}"
REMOTE_DIR="${AI_DAILY_REMOTE_DIR:-/home/lsh/AI-daily-update}"
SERVICE_NAME="${AI_DAILY_SERVICE_NAME:-ai-daily}"
RUN_TESTS="${AI_DAILY_RUN_TESTS:-1}"
PIP_INDEX_URL_REMOTE="${AI_DAILY_PIP_INDEX_URL:-https://mirrors.aliyun.com/pypi/simple/}"
PIP_TIMEOUT="${AI_DAILY_PIP_TIMEOUT:-120}"
PIP_RETRIES="${AI_DAILY_PIP_RETRIES:-5}"
SYNC_STATE="${AI_DAILY_SYNC_STATE:-0}"

cd "$PROJECT_DIR"

if [ "$RUN_TESTS" = "1" ]; then
  "$PROJECT_DIR/.venv/bin/python" -m pytest
fi

RSYNC_EXCLUDES=(
  --exclude '.git/'
  --exclude '.venv/'
  --exclude '.env'
  --exclude '__pycache__/'
  --exclude '.pytest_cache/'
  --exclude '*.pyc'
  --exclude '*.log'
  --exclude 'data/kb.sqlite'
  --exclude 'data/logs/'
  --exclude 'data/raw/'
  --exclude 'data/cache/'
  --exclude 'ppt/backups/'
)

if [ "$SYNC_STATE" != "1" ]; then
  RSYNC_EXCLUDES+=(
    --exclude 'data/'
    --exclude 'notes/'
    --exclude 'ppt/'
    --exclude 'config/sources.yaml'
  )
fi

rsync -avz \
  --no-owner \
  --no-group \
  "${RSYNC_EXCLUDES[@]}" \
  "$PROJECT_DIR/" \
  "$AI_DAILY_REMOTE:$REMOTE_DIR/"

ssh "$AI_DAILY_REMOTE" "
  set -e
  cd '$REMOTE_DIR'
  if [ ! -f .venv/bin/activate ]; then
    rm -rf .venv
    if ! python3 -m venv .venv; then
      echo 'Failed to create .venv on remote.'
      echo 'On Ubuntu/Debian, install venv support first:'
      echo '  sudo apt update && sudo apt install -y python3-venv python3-pip'
      exit 1
    fi
  fi
  . .venv/bin/activate
  python -m pip install --timeout '$PIP_TIMEOUT' --retries '$PIP_RETRIES' -i '$PIP_INDEX_URL_REMOTE' -e .
  if systemctl list-unit-files '$SERVICE_NAME.service' >/dev/null 2>&1; then
    if sudo -n true >/dev/null 2>&1; then
      sudo systemctl restart '$SERVICE_NAME'
      sudo systemctl status '$SERVICE_NAME' --no-pager
    else
      echo 'Deployed. Restart requires sudo password on remote:'
      echo '  sudo systemctl restart $SERVICE_NAME'
    fi
  else
    echo 'Deployed. No systemd service found yet.'
    echo 'Install scripts/systemd/ai-daily-web.service on the remote host, then enable it.'
  fi
"

echo "Cloud deploy finished: $AI_DAILY_REMOTE:$REMOTE_DIR"
