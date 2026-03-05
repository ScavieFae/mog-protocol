# .loop/config.sh — project configuration
PROJECT_NAME="mog-protocol"
HEARTBEAT_INTERVAL=300        # Idle interval (seconds)
WORKER_COOLDOWN=30            # Between worker iterations
MAX_ITERATIONS=20             # Safety limit per brief
NTFY_TOPIC=""     # ntfy.sh topic (empty = no push notifications)
VERIFY_CMD="python3 -c 'import sys; sys.exit(0)'"     # Command to run after each task
GIT_REMOTE="origin"
GIT_MAIN_BRANCH="main"
