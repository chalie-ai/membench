#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN_DATE=$(date +%Y-%m-%d_%H%M%S)
WORKDIR=$(mktemp -d /tmp/membench_claude_sonnet_XXXXXX)

echo "Work directory: $WORKDIR"
echo "Run date: $RUN_DATE"

# ── Setup: init session in a clean /tmp dir ──────────────────────────────────
SESSION_ID=$(cd "$WORKDIR" && claude -p "You are part of a memory benchmark. You will receive biographies one at a time. Memorize every detail. Later you will be quizzed." \
  --model claude-sonnet-4-6 --dangerously-skip-permissions --output-format json | python3 -c "import sys,json; print(next(m['session_id'] for m in json.load(sys.stdin) if m.get('session_id')))")
echo "Session: $SESSION_ID"

# ── Step 1: Biography memory ────────────────────────────────────────────────
python3 "$ROOT/src/run_eval.py" \
  --harness-cmd "cd $WORKDIR && claude -p {prompt} --model claude-sonnet-4-6 --dangerously-skip-permissions --resume $SESSION_ID" \
  --bios-dir "$ROOT/eval/step_1/seeds" \
  --questions "$ROOT/eval/step_1/tests/questions.json" \
  --output "$ROOT/results/claude_code_sonnet/$RUN_DATE/step_1.json" \
  --timeout 300

echo "Done. Results: results/claude_code_sonnet/$RUN_DATE/"
