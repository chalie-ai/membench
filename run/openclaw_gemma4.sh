#!/bin/bash
# membench — OpenClaw harness with gemma4:31b-cloud via Ollama
#
# Lifecycle:
#   1. Ensure membench-openclaw container exists and is running
#      (uses the official ghcr.io/openclaw/openclaw image)
#   2. Non-interactive onboarding pointing at Ollama Cloud
#   3. Enable the OpenAI-compatible gateway endpoint + set default model
#   4. Wait for the gateway to become responsive
#   5. Run membench eval via src/openclaw_chat.py (sticky session-key header)
#
# Container:   membench-openclaw
# Host port:   19089 → container 18789  (OpenClaw gateway)
# Model:       gemma4:31b-cloud         (via Ollama at grck.lan:30068)
# Session:     membench-eval             (x-openclaw-session-key)
#
# Note: OpenClaw's Ollama integration requires the native base URL without /v1
# (tool calling breaks on the /v1 path — documented in OpenClaw's provider guide).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN_DATE=$(date +%Y-%m-%d_%H%M%S)
CONTAINER="membench-openclaw"
HOST_PORT=19089
GATEWAY_PORT=18789
BASE_URL="http://localhost:${HOST_PORT}"
MODEL="gemma4:31b-cloud"
OLLAMA_BASE_URL="http://grck.lan:30068"
SESSION_KEY="membench-eval"
OPENCLAW_IMAGE="${OPENCLAW_IMAGE:-ghcr.io/openclaw/openclaw:latest}"
DEPLOY_MARKER="/home/node/.openclaw/.membench_onboarded"
HEALTH_TIMEOUT=600

echo "Container:  $CONTAINER"
echo "Image:      $OPENCLAW_IMAGE"
echo "Base URL:   $BASE_URL"
echo "Model:      $MODEL"
echo "Run date:   $RUN_DATE"
echo ""

# ── 1. Ensure container is running ──────────────────────────────────────────
is_running() {
  [ "$(docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null)" = "true" ]
}
container_exists() {
  docker inspect "$CONTAINER" &>/dev/null
}

if is_running; then
  echo "[lifecycle] Container already running — reusing"
elif container_exists; then
  echo "[lifecycle] Starting existing container..."
  docker start "$CONTAINER"
else
  echo "[lifecycle] Pulling $OPENCLAW_IMAGE..."
  docker pull "$OPENCLAW_IMAGE"

  echo "[lifecycle] Creating fresh OpenClaw container..."
  GRCK_IP=$(python3 -c "import socket; print(socket.gethostbyname('grck.lan'))")
  docker run -d \
    --name "$CONTAINER" \
    --network bridge \
    --add-host "grck.lan:${GRCK_IP}" \
    -p "${HOST_PORT}:${GATEWAY_PORT}" \
    -e "OLLAMA_API_BASE=${OLLAMA_BASE_URL}" \
    -e "OLLAMA_API_KEY=ollama" \
    "$OPENCLAW_IMAGE" \
    sleep infinity
fi

# ── 2. Non-interactive onboard (idempotent) ─────────────────────────────────
if docker exec "$CONTAINER" test -f "$DEPLOY_MARKER" 2>/dev/null; then
  echo "[lifecycle] OpenClaw already onboarded"
else
  echo "[lifecycle] Onboarding OpenClaw (non-interactive, Ollama)..."
  docker exec "$CONTAINER" bash -lc \
    "openclaw onboard --non-interactive --auth-choice ollama --accept-risk"
  docker exec "$CONTAINER" bash -lc \
    "mkdir -p /home/node/.openclaw && touch ${DEPLOY_MARKER}"
  echo "[lifecycle] Onboard complete"
fi

# ── 3. Configure model + enable OpenAI-compat gateway endpoint ──────────────
echo "[lifecycle] Configuring default model + gateway..."
docker exec "$CONTAINER" bash -lc \
  "openclaw config set model '${MODEL}'" || true
docker exec "$CONTAINER" bash -lc \
  "openclaw config set gateway.openaiApi.enabled true" || true
docker exec "$CONTAINER" bash -lc \
  "openclaw config set gateway.auth.mode open" || true

# Ensure the daemon/gateway is running
docker exec "$CONTAINER" bash -lc "openclaw gateway start" >/dev/null 2>&1 || true

# ── 4. Wait for gateway to respond ──────────────────────────────────────────
echo "[lifecycle] Waiting for gateway on ${BASE_URL} (up to ${HEALTH_TIMEOUT}s)..."
ELAPSED=0
until curl -sf "${BASE_URL}/v1/models" >/dev/null 2>&1 \
   || curl -sf "${BASE_URL}/health" >/dev/null 2>&1; do
  sleep 3
  ELAPSED=$((ELAPSED + 3))
  if [ $ELAPSED -ge $HEALTH_TIMEOUT ]; then
    echo "[lifecycle] ERROR: gateway not ready after ${HEALTH_TIMEOUT}s" >&2
    docker exec "$CONTAINER" bash -lc \
      "openclaw logs --tail 40 2>/dev/null || tail -40 /home/node/.openclaw/logs/*.log 2>/dev/null || true" >&2
    exit 1
  fi
  [ $((ELAPSED % 15)) -eq 0 ] && echo "[lifecycle]   still waiting... (${ELAPSED}s)"
done
echo "[lifecycle] Gateway ready at $BASE_URL"
echo ""

# ── 5. Harness command (per-prompt) ─────────────────────────────────────────
HARNESS="python3 $ROOT/src/openclaw_chat.py --base-url $BASE_URL --session-key $SESSION_KEY --prompt {prompt}"

# Seed session with benchmark preamble
echo "[lifecycle] Seeding benchmark session..."
python3 "$ROOT/src/openclaw_chat.py" \
  --base-url "$BASE_URL" \
  --session-key "$SESSION_KEY" \
  --prompt "You are part of a memory benchmark. You will receive documents one at a time. Memorise every detail. Later you will be quizzed." \
  >/dev/null
echo "[lifecycle] Session seeded"
echo ""

# ── 6. Step 1: Biography recall ─────────────────────────────────────────────
python3 "$ROOT/src/run_eval.py" \
  --harness-cmd "$HARNESS" \
  --seeds-dir "$ROOT/eval/step_1/seeds" \
  --pattern "bio_*.md" \
  --label "biographies" \
  --questions "$ROOT/eval/step_1/tests/questions.json" \
  --output "$ROOT/results/openclaw_gemma4/$RUN_DATE/step_1.json"

echo "Done. Results: results/openclaw_gemma4/$RUN_DATE/"
