#!/bin/zsh
# Headless scheduled job search for the job_agents skill (invoked by launchd).
# SEARCH + SCORE + TRACK ONLY: never drafts-to-submit, never opens application forms, never submits.
# Logs contain job titles/companies/scores/URLs only - no CV contents or credentials.
set -u
SKILL_DIR="${0:A:h:h}"
DATA_HOME="${JOB_AGENTS_HOME:-$HOME/.job_agents}"
LOG_DIR="$DATA_HOME/logs"
LOCK="$DATA_HOME/.search.lock"
mkdir -p "$LOG_DIR" && chmod 700 "$DATA_HOME" "$LOG_DIR"

CLAUDE_BIN="${CLAUDE_BIN:-$(command -v claude || echo "$HOME/.local/bin/claude")}"
if [[ ! -x "$CLAUDE_BIN" ]]; then
  echo "$(date -Iseconds) claude CLI not found" >> "$LOG_DIR/scheduler-errors.log"; exit 1
fi

# Prevent overlapping runs.
if ! mkdir "$LOCK" 2>/dev/null; then
  echo "$(date -Iseconds) previous run still active - skipping" >> "$LOG_DIR/scheduler-errors.log"; exit 0
fi
trap 'rmdir "$LOCK"' EXIT

LOG="$LOG_DIR/search-$(date +%Y%m%d-%H%M).log"
umask 077
cd "$SKILL_DIR" || exit 1
"$CLAUDE_BIN" -p "/job_agents search --scheduled" \
  --allowedTools "WebSearch" "WebFetch" "Read" "Write" "Bash(python3 *)" \
  > "$LOG" 2>&1
echo "exit=$? at $(date -Iseconds)" >> "$LOG"
# Keep 30 days of logs.
find "$LOG_DIR" -name 'search-*.log' -mtime +30 -delete 2>/dev/null
exit 0
