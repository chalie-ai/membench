#!/bin/bash
# membench — Hermes Agent harness with gemma4:31b-cloud via Ollama
#
# Lifecycle:
#   1. Ensure membench-hermes container exists and is running
#   2. Install Hermes via install.sh if not already installed
#   3. Configure OpenAI-compatible provider pointing at Ollama Cloud
#   4. Set primary model to gemma4:31b-cloud
#   5. Seed a fresh session with the benchmark preamble
#   6. Run membench eval — biography recall (--continue resumes latest session)
#
# Container:  membench-hermes   (separate from chalie / claude-code containers)
# Host port:  19083             (not published — session state lives inside container)
# Model:      gemma4:31b-cloud  (via Ollama at grck.lan:30068)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN_DATE=$(date +%Y-%m-%d_%H%M%S)
CONTAINER="membench-hermes"
HOST_PORT=19083
HERMES_PORT=8080
MODEL="gemma4:31b-cloud"
OLLAMA_BASE_URL="http://grck.lan:30068/v1"
OLLAMA_API_KEY="ollama"
INSTALL_URL="https://hermes-agent.nousresearch.com/install.sh"
DEPLOY_MARKER="/root/.hermes/.membench_installed"
HEALTH_TIMEOUT=600

echo "Container:  $CONTAINER"
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
  echo "[lifecycle] Creating fresh Ubuntu container..."
  GRCK_IP=$(python3 -c "import socket; print(socket.gethostbyname('grck.lan'))")
  docker run -d \
    --name "$CONTAINER" \
    --network bridge \
    --add-host "grck.lan:${GRCK_IP}" \
    -p "${HOST_PORT}:${HERMES_PORT}" \
    ubuntu:22.04 sleep infinity
  echo "[lifecycle] Installing curl + ca-certificates + python3..."
  docker exec "$CONTAINER" bash -c \
    "apt-get update -qq && apt-get install -y -qq curl ca-certificates python3 2>&1 | tail -5"
fi

# ── 2. Install Hermes if not already installed ──────────────────────────────
if docker exec "$CONTAINER" test -f "$DEPLOY_MARKER" 2>/dev/null; then
  echo "[lifecycle] Hermes already installed"
else
  echo "[lifecycle] Installing Hermes Agent — this may take a few minutes..."
  docker exec "$CONTAINER" bash -c \
    "curl -fsSL ${INSTALL_URL} | HERMES_NONINTERACTIVE=1 bash"
  docker exec "$CONTAINER" bash -c "mkdir -p /root/.hermes && touch ${DEPLOY_MARKER}"
  echo "[lifecycle] Install complete"
fi

# ── 3. Configure provider via ~/.hermes/.env + config.yaml ──────────────────
echo "[lifecycle] Writing provider config..."
docker exec "$CONTAINER" bash -c "cat > /root/.hermes/.env <<EOF
OPENAI_BASE_URL=${OLLAMA_BASE_URL}
OPENAI_API_KEY=${OLLAMA_API_KEY}
EOF"

docker exec "$CONTAINER" bash -c "cat > /root/.hermes/config.yaml <<EOF
model:
  provider: custom
  base_url: ${OLLAMA_BASE_URL}
  api_key: ${OLLAMA_API_KEY}
  name: ${MODEL}
EOF"

# Also register via CLI in case the config file is not authoritative
docker exec "$CONTAINER" bash -lc "hermes setup model --non-interactive" || true
docker exec "$CONTAINER" bash -lc "hermes config set model ${MODEL}" || true

# ── 4. Wait for Hermes to be responsive ─────────────────────────────────────
echo "[lifecycle] Waiting for Hermes to respond to 'hermes status' (up to ${HEALTH_TIMEOUT}s)..."
ELAPSED=0
until docker exec "$CONTAINER" bash -lc "hermes status >/dev/null 2>&1"; do
  sleep 3
  ELAPSED=$((ELAPSED + 3))
  if [ $ELAPSED -ge $HEALTH_TIMEOUT ]; then
    echo "[lifecycle] ERROR: Hermes not ready after ${HEALTH_TIMEOUT}s" >&2
    docker exec "$CONTAINER" bash -lc "hermes logs --tail 20 2>&1 || tail -20 /root/.hermes/logs/*.log 2>/dev/null || true" >&2
    exit 1
  fi
  [ $((ELAPSED % 15)) -eq 0 ] && echo "[lifecycle]   still waiting... (${ELAPSED}s)"
done
echo "[lifecycle] Hermes ready"

# ── 5. Seed session with benchmark preamble ─────────────────────────────────
echo "[lifecycle] Seeding benchmark session..."
docker exec "$CONTAINER" bash -lc \
  "hermes chat -q 'You are part of a memory benchmark. You will receive documents one at a time. Memorise every detail. Later you will be quizzed.' >/dev/null"
echo "[lifecycle] Session seeded"
echo ""

# ── 6. Harness command (per-prompt) ─────────────────────────────────────────
# --continue resumes the most recent session — preserves state across ingestion + questions.
HARNESS="docker exec ${CONTAINER} hermes --continue chat -q {prompt}"

# ── 7. Step 1: Biography recall ─────────────────────────────────────────────
python3 "$ROOT/src/run_eval.py" \
  --harness-cmd "$HARNESS" \
  --seeds-dir "$ROOT/eval/step_1/seeds" \
  --pattern "bio_*.md" \
  --label "biographies" \
  --questions "$ROOT/eval/step_1/tests/questions.json" \
  --output "$ROOT/results/hermes_gemma4/$RUN_DATE/step_1.json"

echo "Done. Results: results/hermes_gemma4/$RUN_DATE/"
