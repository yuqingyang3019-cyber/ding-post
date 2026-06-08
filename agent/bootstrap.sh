#!/usr/bin/env bash
set -euo pipefail

export PATH="/code/.venv/bin:${PATH}"
cd /code

python -m uvicorn agent.main:app --host 0.0.0.0 --port "${PORT:-9000}"
