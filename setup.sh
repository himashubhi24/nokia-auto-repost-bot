#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

command -v python3 >/dev/null || {
  echo "python3 is required"
  exit 1
}

python3 -m venv venv
venv/bin/python -m pip install --upgrade pip wheel
venv/bin/pip install -r requirements.txt
mkdir -p downloads

if [[ ! -f .env ]]; then
  cp .env.example .env
  chmod 600 .env
  echo "Created .env. Fill its required values before starting the bot."
fi

venv/bin/python -m py_compile \
  main.py bot.py config.py helper_func.py auto_repost.py \
  database/database.py plugins/*.py

echo "Setup complete. Run: set -a && source .env && set +a && venv/bin/python main.py"

