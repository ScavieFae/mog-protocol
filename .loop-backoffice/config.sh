#!/bin/bash
# Back-office daemon config — API portfolio manager

PROJECT_NAME="mog-backoffice"
HEARTBEAT_INTERVAL=120        # 2 min between ticks (faster than build daemon)
WORKER_COOLDOWN=15            # 15s between worker iterations
MAX_ITERATIONS=10             # max iterations per brief
GIT_REMOTE="origin"
GIT_MAIN_BRANCH="backoffice"  # operates on backoffice branch
