#!/usr/bin/env bash
set -euo pipefail

cd /code
export PYTHONPATH="/code/.python:${PYTHONPATH:-}"

python3 -m uvicorn agent.main:app --host 0.0.0.0 --port "${PORT:-9000}"
