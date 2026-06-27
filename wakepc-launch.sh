#!/bin/bash
BIN=/Volumes/Home/alvise/miniforge3/envs/tools/bin/streamlit
APP=/Volumes/Home/alvise/GIT/wakepc/app.py
for i in $(seq 1 60); do [ -x "$BIN" ] && [ -r "$APP" ] && break; sleep 2; done
[ -x "$BIN" ] || { echo "$(date '+%F %T') volume non pronto, esco" >&2; exit 0; }
exec "$BIN" run --server.headless=true --server.address=0.0.0.0 \
  --browser.gatherUsageStats=false "$APP"
