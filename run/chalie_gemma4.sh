#!/bin/bash
# membench — Chalie harness with gemma4:31b-cloud via Ollama
#
# Lifecycle (unconditional on every run):
#   1. Destroy prior membench-chalie container + anonymous volumes
#   2. Pull + run chalieai/chalie:latest (binds GPU 0 when available)
#   3. Wait for /ready
#   4. Auth + provider setup (gemma4:31b-cloud on all jobs)
#   5. Reset conversation thread
#   6. Run membench eval — biography recall
#
# Container:  membench-chalie (no -p; harness talks to container's bridge IP)
# Image:      ${CHALIE_IMAGE:-chalieai/chalie:latest}
# Model:      gemma4:31b-cloud (via Ollama at grck.lan:30068)
#
# Invocation:
#   bash        run/chalie_gemma4.sh   # as truenas_admin (or any docker user)
#   sudo bash   run/chalie_gemma4.sh   # as a sudo-only account (works too)
#
# Both work.  TrueNAS Scale's sudoers enables `Defaults log_subcmds`, which
# attaches a ptrace monitor that SIGKILLs any child whose execve() argv is
# large enough to fail sudo's argv-consistency check.  Earlier versions of
# this runner tripped that trap by passing the 15–20 KB bio bodies through
# `--prompt "<huge string>"` — every ingestion died with rc=-9 at 0.5 s.
# The harness now writes the prompt to /tmp/membench_prompt_*.txt and calls
# chalie_chat.py with `--prompt-file <path>`, so argv stays ~200 bytes and
# sudo's monitor is happy regardless of how the outer shell was launched.
# Docker calls are wrapped in `sudo -n docker` when the invoking user isn't
# in the docker group (i.e. truenas_admin).  Under `sudo bash`, the wrapper
# resolves to plain `docker` because root is already in the docker group.
set -euo pipefail

# Wrapper for docker — truenas_admin isn't in the docker group on grck, so
# every docker call needs sudo.  -n fails fast instead of prompting (user
# has NOPASSWD:ALL; if that's ever tightened, we want a loud failure rather
# than a hung script).
if groups 2>/dev/null | tr ' ' '\n' | grep -qx docker; then
  DOCKER=(docker)
else
  DOCKER=(sudo -n docker)
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN_DATE=$(date +%Y-%m-%d_%H%M%S)

IMAGE="${CHALIE_IMAGE:-chalieai/chalie:latest}"
CONTAINER="membench-chalie"
CHALIE_PORT=8081
# BASE_URL is set after `docker run` — we use the container's bridge IP
# directly (no -p, no docker-proxy, no IPv6/IPv4 games).
COOKIE_FILE="/tmp/membench_chalie_cookies.json"
MODEL="gemma4:31b-cloud"
OLLAMA_HOST="http://grck.lan:30068"
USERNAME="membench"
PASSWORD="membench123"
HEALTH_TIMEOUT=600

echo "Image:     $IMAGE"
echo "Container: $CONTAINER"
echo "Model:     $MODEL"
echo "Run date:  $RUN_DATE"
echo ""

# ── 1. Nuke prior state — loud and complete ─────────────────────────────────
# Every run is a clean slate. We show each removal so you can SEE it happened
# instead of trusting a silent || true.
echo "[lifecycle] === TEARDOWN ==="

# 1a. Kill any lingering harness procs from a previous interrupted run.
#     These hold the cookie file open and can race the setup on re-entry.
STALE_PIDS=$(pgrep -f 'chalie_setup\.py|chalie_chat\.py|run_eval\.py' || true)
if [ -n "$STALE_PIDS" ]; then
  echo "[lifecycle] Killing stale harness procs: $STALE_PIDS"
  # shellcheck disable=SC2086
  kill -9 $STALE_PIDS 2>/dev/null || true
else
  echo "[lifecycle] No stale harness procs."
fi

# 1b. Container.  docker rm -fv drops the container AND its anonymous volumes
#     (the image declares VOLUME /data — that anonymous mount goes with -v).
if "${DOCKER[@]}" inspect "$CONTAINER" >/dev/null 2>&1; then
  echo "[lifecycle] Removing container $CONTAINER + its anonymous volumes..."
  "${DOCKER[@]}" rm -fv "$CONTAINER"
else
  echo "[lifecycle] No container named $CONTAINER."
fi

# 1c. Named volumes.  The image doesn't create these, but if someone made them
#     manually (`docker volume create membench-chalie`) they'd persist across
#     container removals — scrub them too.  -Fxq = exact match, never substring.
for v in "$CONTAINER" "${CONTAINER}-data"; do
  if "${DOCKER[@]}" volume ls -q 2>/dev/null | grep -Fxq "$v"; then
    echo "[lifecycle] Removing named volume: $v"
    "${DOCKER[@]}" volume rm -f "$v"
  fi
done

# 1d. Host-side scratch.  Cookies from a prior auth are stale after the DB nuke
#     and would confuse chalie_chat.py with a session that no longer exists.
#     If the file is owned by root (left over from a historical `sudo bash`
#     run of this script), try `sudo -n rm` as a fallback so the next steps
#     don't choke on "Operation not permitted".
if [ -f "$COOKIE_FILE" ]; then
  echo "[lifecycle] Removing stale cookie file: $COOKIE_FILE"
  if ! rm -f "$COOKIE_FILE" 2>/dev/null; then
    echo "[lifecycle]   (cookie file not removable as $USER — trying sudo -n rm)"
    sudo -n rm -f "$COOKIE_FILE"
  fi
fi

# 1e. Verify.  If ANY membench-chalie state survives at this point, bail —
#     a run that starts with polluted state is worse than a run that fails
#     to start.
if "${DOCKER[@]}" inspect "$CONTAINER" >/dev/null 2>&1; then
  echo "[lifecycle] ERROR: container $CONTAINER still exists after removal." >&2
  exit 1
fi
if "${DOCKER[@]}" volume ls -q | grep -Fxq "$CONTAINER" \
   || "${DOCKER[@]}" volume ls -q | grep -Fxq "${CONTAINER}-data"; then
  echo "[lifecycle] ERROR: named volume for $CONTAINER still exists after removal." >&2
  exit 1
fi
echo "[lifecycle] Teardown verified clean."
echo ""

# ── 2. Pull + run ────────────────────────────────────────────────────────────
echo "[lifecycle] Pulling ${IMAGE}..."
"${DOCKER[@]}" pull "$IMAGE"

# GPU 0 when the host advertises nvidia-smi.  We used to additionally grep
# `docker info` for `runtimes:.*nvidia`, but that check flapped under the
# running script (empty pipeline → CPU-only fallback) even though the host
# truly has the runtime configured.  Simpler, more reliable rule: if
# nvidia-smi is on PATH, bind device=0 and let `docker run` fail loudly if
# the runtime isn't actually wired up — we'd rather see an error than
# silently run the embedder on CPU.
GPU_ARGS=()
if command -v nvidia-smi >/dev/null 2>&1; then
  GPU_ARGS=(--gpus "device=0")
  echo "[lifecycle] GPU: binding device=0 (nvidia-smi present)"
else
  echo "[lifecycle] GPU: no nvidia-smi on PATH — running CPU-only"
fi

# Map grck.lan inside the container to the Docker host's gateway address.
# We can't use the host's own `getaddrinfo('grck.lan')` — on grck that returns
# 127.0.0.1 (loopback entry in /etc/hosts), which inside the container points
# to the container's own loopback, not the host. `host-gateway` is Docker's
# official magic for "the host as seen from this container" (Linux 20.10+).
echo "[lifecycle] Starting container..."
"${DOCKER[@]}" run -d \
  --name "$CONTAINER" \
  --add-host "grck.lan:host-gateway" \
  "${GPU_ARGS[@]}" \
  "$IMAGE"

# Resolve the container's bridge IP — this is what the harness talks to.
# No -p, no docker-proxy, no IPv6/IPv4 ambiguity.
CONTAINER_IP=$("${DOCKER[@]}" inspect -f '{{.NetworkSettings.IPAddress}}' "$CONTAINER")
if [ -z "$CONTAINER_IP" ]; then
  echo "[lifecycle] ERROR: could not resolve bridge IP for $CONTAINER" >&2
  exit 1
fi
BASE_URL="http://${CONTAINER_IP}:${CHALIE_PORT}"
echo "[lifecycle] Chalie bridge IP: $CONTAINER_IP"
echo "[lifecycle] Base URL:         $BASE_URL"

# ── 3. Wait for /ready ───────────────────────────────────────────────────────
echo "[lifecycle] Waiting for Chalie to become ready (up to ${HEALTH_TIMEOUT}s)..."
ELAPSED=0
until curl -sf "${BASE_URL}/ready" 2>/dev/null \
  | python3 -c "import sys,json; sys.exit(0 if json.load(sys.stdin).get('ready') else 1)" 2>/dev/null; do
  sleep 3
  ELAPSED=$((ELAPSED + 3))
  if [ $ELAPSED -ge $HEALTH_TIMEOUT ]; then
    echo "[lifecycle] ERROR: Chalie not ready after ${HEALTH_TIMEOUT}s" >&2
    echo "[lifecycle] Last container log lines:" >&2
    "${DOCKER[@]}" logs --tail 50 "$CONTAINER" >&2 || true
    exit 1
  fi
  [ $((ELAPSED % 15)) -eq 0 ] && echo "[lifecycle]   still waiting... (${ELAPSED}s)"
done
echo "[lifecycle] Chalie ready at $BASE_URL"
echo ""

# ── 4. Auth + provider setup ─────────────────────────────────────────────────
# Generous ready-timeout — even after the outer check passes, Chalie's
# sub-initialisation (ONNX warmup, personality load, thread manager) can
# briefly re-flap /ready on a cold boot.
python3 "$ROOT/src/chalie_setup.py" \
  --base-url "$BASE_URL" \
  --username "$USERNAME" \
  --password "$PASSWORD" \
  --cookie-file "$COOKIE_FILE" \
  --model "$MODEL" \
  --ready-timeout 300 \
  --ollama-host "$OLLAMA_HOST"
echo ""

# ── 5. Harness command (per-prompt) ──────────────────────────────────────────
# Use {prompt_file}, NOT {prompt}.  The bio bodies we memorise can be 15–20 KB;
# on TrueNAS Scale the sudoers' `Defaults log_subcmds` attaches a ptrace
# monitor that SIGKILLs any child whose execve() argv exceeds its consistency
# check, which is why the whole run died at 0.5 s under `sudo bash` last time.
# Writing the prompt to a tempfile keeps argv tiny (~200 bytes) and makes the
# harness sudo-safe end to end.
HARNESS="python3 $ROOT/src/chalie_chat.py --base-url $BASE_URL --cookie-file $COOKIE_FILE --prompt-file {prompt_file}"

# ── 6. Step 1: Biography recall ──────────────────────────────────────────────
python3 "$ROOT/src/run_eval.py" \
  --harness-cmd "$HARNESS" \
  --seeds-dir "$ROOT/eval/step_1/seeds" \
  --pattern "bio_*.md" \
  --label "biographies" \
  --questions "$ROOT/eval/step_1/tests/questions.json" \
  --output "$ROOT/results/chalie_gemma4/$RUN_DATE/step_1.json"

echo "Done. Results: results/chalie_gemma4/$RUN_DATE/"
