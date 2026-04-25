#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN_DATE=$(date +%Y-%m-%d_%H%M%S)
WORKDIR=$(mktemp -d /tmp/membench_claude_local_XXXXXX)
LOCAL_CLAUDE="$HOME/.claude/local"
HARNESS="cd $WORKDIR && bash $LOCAL_CLAUDE -p {prompt} --dangerously-skip-permissions --resume"

# Ensure claude binary is on PATH (installed via Claude desktop app)
CLAUDE_BIN="$(find "$HOME/Library/Application Support/Claude/claude-code" -name claude -type f 2>/dev/null | head -1)"
if [ -n "$CLAUDE_BIN" ]; then
  export PATH="$(dirname "$CLAUDE_BIN"):$PATH"
fi

echo "Work directory: $WORKDIR"
echo "Run date: $RUN_DATE"

# ── Setup: init session in a clean /tmp dir ──────────────────────────────────
SESSION_ID=$(cd "$WORKDIR" && bash "$LOCAL_CLAUDE" -p "You are part of a memory benchmark. You will receive documents one at a time. Memorize every detail. Later you will be quizzed." \
  --dangerously-skip-permissions --output-format json | python3 -c "import sys,json; print(next(m['session_id'] for m in json.load(sys.stdin) if m.get('session_id')))")
echo "Session: $SESSION_ID"

# ── Step 1: Biography recall ───────────────────────────────────────────────
python3 "$ROOT/src/run_eval.py" \
  --harness-cmd "$HARNESS $SESSION_ID" \
  --seeds-dir "$ROOT/eval/step_1/seeds" \
  --pattern "bio_*.md" \
  --label "biographies" \
  --questions "$ROOT/eval/step_1/tests/questions.json" \
  --output "$ROOT/results/claude_code_local/$RUN_DATE/step_1.json"

# ── Step 2: Reasoning over connections (disabled — eval 1 only) ───────────
# python3 "$ROOT/src/run_eval.py" \
#   --harness-cmd "$HARNESS $SESSION_ID" \
#   --seeds-dir "$ROOT/eval/step_1/seeds" \
#   --questions "$ROOT/eval/step_2/tests/questions.json" \
#   --output "$ROOT/results/claude_code_local/$RUN_DATE/step_2.json" \
#   --timeout 300 \
#   --skip-ingestion \
#   --label "biographies"

# ── Step 3: Project trait extraction (disabled — eval 1 only) ─────────────
# python3 "$ROOT/src/run_eval.py" \
#   --harness-cmd "$HARNESS $SESSION_ID" \
#   --seeds-dir "$ROOT/eval/step_1/seeds" \
#   --pattern "project_*.md" \
#   --label "project specs" \
#   --questions "$ROOT/eval/step_3/tests/questions.json" \
#   --output "$ROOT/results/claude_code_local/$RUN_DATE/step_3.json" \
#   --timeout 300

echo "Done. Results: results/claude_code_local/$RUN_DATE/"
