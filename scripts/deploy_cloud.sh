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
  --exclude '.venv-linux/'
  --exclude '.env*'
  --exclude '.claude/'
  --exclude '__pycache__/'
  --exclude '.pytest_cache/'
  --exclude 'AI-introduction/'
  --exclude '*.pdf'
  --exclude '*.docx'
  --exclude 'docs/learning-*'
  --exclude 'nettest/'
  --exclude '*.pyc'
  --exclude '*.log'
  --exclude '**/.gradle/'
  --exclude '**/build/'
  --exclude '**/node_modules/'
  --exclude '**/dist/'
  --exclude '**/.DS_Store'
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

# ssh concatenates multiple command-line arguments with plain spaces before
# handing them to the remote shell, so we cannot rely on argv boundaries to
# keep untrusted values (env vars) from being re-interpreted as shell syntax.
# Instead, quote each value into a safe shell literal locally (printf %q) and
# build one fully-quoted command string.
q_remote_dir=$(printf '%q' "$REMOTE_DIR")
q_pip_timeout=$(printf '%q' "$PIP_TIMEOUT")
q_pip_retries=$(printf '%q' "$PIP_RETRIES")
q_pip_index_url=$(printf '%q' "$PIP_INDEX_URL_REMOTE")
q_service_name=$(printf '%q' "$SERVICE_NAME")

REMOTE_SCRIPT="
  set -e
  cd $q_remote_dir
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
  python -m pip install --timeout $q_pip_timeout --retries $q_pip_retries -i $q_pip_index_url -e .
  if systemctl list-unit-files $q_service_name.service >/dev/null 2>&1; then
    if sudo -n true >/dev/null 2>&1; then
      sudo systemctl restart $q_service_name
      sudo systemctl status $q_service_name --no-pager
    else
      echo 'Deployed. Restart requires sudo password on remote:'
      echo '  sudo systemctl restart $SERVICE_NAME'
      exit 2
    fi
  else
    echo 'Deployed. No systemd service found yet.'
    echo 'Install scripts/systemd/ai-daily-web.service on the remote host, then enable it.'
  fi
"

set +e
ssh "$AI_DAILY_REMOTE" "$REMOTE_SCRIPT"
DEPLOY_STATUS=$?
set -e

if [ "$DEPLOY_STATUS" -eq 2 ]; then
  echo "Cloud deploy finished but the remote service was NOT restarted: $AI_DAILY_REMOTE:$REMOTE_DIR"
  exit 2
elif [ "$DEPLOY_STATUS" -ne 0 ]; then
  echo "Cloud deploy failed: $AI_DAILY_REMOTE:$REMOTE_DIR"
  exit "$DEPLOY_STATUS"
fi

echo "Cloud deploy finished: $AI_DAILY_REMOTE:$REMOTE_DIR"
