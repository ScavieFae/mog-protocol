#!/bin/bash
# Wrapper: sets LOOP_DIR then execs the real daemon.sh with it patched in.
# daemon.sh hardcodes LOOP_DIR="$PROJECT_DIR/.loop" — this wrapper overrides
# that by sed-patching the line before execution.

PROJECT_DIR="${1:?Usage: daemon-wrapper.sh <project_dir> [heartbeat_seconds]}"
PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"

# Set LOOP_DIR for assess.py and any child processes
export LOOP_DIR="$PROJECT_DIR/.loop-backoffice"

# Run daemon.sh with the LOOP_DIR line patched to respect env var
exec bash <(sed 's|^LOOP_DIR="\$PROJECT_DIR/\.loop"|LOOP_DIR="${LOOP_DIR:-$PROJECT_DIR/.loop}"|' "$PROJECT_DIR/lib/daemon.sh") "$@"
