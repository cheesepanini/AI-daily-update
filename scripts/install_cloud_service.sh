#!/usr/bin/env bash
set -euo pipefail

: "${AI_DAILY_REMOTE:?Set AI_DAILY_REMOTE to your SSH host, for example aliyun-ai or user@host}"

REMOTE_DIR="${AI_DAILY_REMOTE_DIR:-/home/lsh/AI-daily-update}"
SERVICE_NAME="${AI_DAILY_SERVICE_NAME:-ai-daily}"
SERVICE_HOST="${AI_DAILY_SERVICE_HOST:-0.0.0.0}"
SERVICE_PORT="${AI_DAILY_SERVICE_PORT:-8001}"

ssh -tt "$AI_DAILY_REMOTE" \
  "REMOTE_DIR='$REMOTE_DIR' SERVICE_NAME='$SERVICE_NAME' SERVICE_HOST='$SERVICE_HOST' SERVICE_PORT='$SERVICE_PORT' bash -s" <<'REMOTE_SCRIPT'
set -euo pipefail

if [ ! -d "$REMOTE_DIR" ]; then
  echo "Remote project directory does not exist: $REMOTE_DIR"
  exit 1
fi

if [ ! -f "$REMOTE_DIR/.env" ]; then
  echo "Missing remote .env: $REMOTE_DIR/.env"
  echo "Create it before installing the service."
  exit 1
fi

if [ ! -x "$REMOTE_DIR/.venv/bin/ai-daily" ]; then
  echo "Missing ai-daily executable: $REMOTE_DIR/.venv/bin/ai-daily"
  echo "Run scripts/deploy_cloud.sh first."
  exit 1
fi

tmp_file="$(mktemp)"
cat > "$tmp_file" <<EOF
[Unit]
Description=AI Daily Update web service
After=network.target

[Service]
Type=simple
WorkingDirectory=$REMOTE_DIR
EnvironmentFile=$REMOTE_DIR/.env
ExecStart=$REMOTE_DIR/.venv/bin/ai-daily serve --host $SERVICE_HOST --port $SERVICE_PORT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo install -m 0644 "$tmp_file" "/etc/systemd/system/$SERVICE_NAME.service"
rm -f "$tmp_file"

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl status "$SERVICE_NAME" --no-pager
REMOTE_SCRIPT

echo "Cloud service installed: $SERVICE_NAME on $AI_DAILY_REMOTE"
