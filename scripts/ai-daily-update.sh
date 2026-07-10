#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/lsh/Documents/AI-daily-update"
cd "$PROJECT_DIR"

"$PROJECT_DIR/.venv/bin/ai-daily" daily
