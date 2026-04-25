#!/usr/bin/env python3
"""
chalie_chat.py

Sends a single chat message to Chalie via WebSocket and prints the response text.
Used as the per-call harness command for membench run_eval.py.

Usage (inline prompt — fine for short strings):
  python3 src/chalie_chat.py \
    --base-url http://localhost:19082 \
    --cookie-file /tmp/chalie_cookies.json \
    --prompt "Your prompt here"

Usage (prompt from file — required for large prompts):
  python3 src/chalie_chat.py \
    --base-url http://localhost:19082 \
    --cookie-file /tmp/chalie_cookies.json \
    --prompt-file /tmp/bio_42.txt

WHY --prompt-file EXISTS:
  On TrueNAS Scale, /etc/sudoers has `Defaults log_subcmds`, which attaches a
  ptrace/seccomp monitor to every descendant of a sudo'd shell.  When argv on
  execve() is large (the 15–20 KB bio bodies membench feeds us), the monitor's
  argv consistency check fails and the kernel delivers SIGKILL to the child
  before main() runs — visible upstream as `rc=-9` after ~0.5 s.  Passing the
  prompt via file keeps execve() argv tiny (just the filename) so the check
  passes, and the harness works whether the user invokes the runner directly
  or under `sudo bash`.

Exits 0 and prints response text to stdout on success.
Exits 1 and prints error to stderr on failure (run_eval.py will retry).
"""

import argparse
import json
import sys
import time

try:
    import websocket
except ImportError:
    print("ERROR: websocket-client not installed. Run: pip install websocket-client", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--cookie-file", required=True)
    # Exactly one of --prompt / --prompt-file must be given.  argparse's
    # mutually-exclusive group enforces that, and also prints a clean error
    # if the caller forgets both (rather than crashing inside recv()).
    pgrp = parser.add_mutually_exclusive_group(required=True)
    pgrp.add_argument("--prompt", help="Inline prompt string (short inputs only)")
    pgrp.add_argument("--prompt-file",
                      help="Path to a UTF-8 file whose contents are the prompt")
    args = parser.parse_args()

    if args.prompt is not None:
        prompt = args.prompt
    else:
        try:
            with open(args.prompt_file, encoding="utf-8") as pf:
                prompt = pf.read()
        except OSError as e:
            print(f"ERROR: cannot read prompt file {args.prompt_file}: {e}",
                  file=sys.stderr)
            sys.exit(1)

    # Load session cookies
    try:
        with open(args.cookie_file) as f:
            cookies = json.load(f)
    except Exception as e:
        print(f"ERROR: cannot load cookies from {args.cookie_file}: {e}", file=sys.stderr)
        sys.exit(1)

    cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())
    ws_url = args.base_url.replace("https://", "wss://").replace("http://", "ws://") + "/ws"

    # Connect — no timeout, large bios can take a long time to process
    try:
        ws = websocket.create_connection(
            ws_url,
            header={"Cookie": cookie_header},
        )
    except Exception as e:
        print(f"ERROR: WebSocket connection failed to {ws_url}: {e}", file=sys.stderr)
        sys.exit(1)

    response_text = ""
    last_event = None  # keep the final event so we can diagnose empty responses
    terminator = None  # "done" | "error" | None (socket closed mid-stream)
    try:
        # Send chat message
        ws.send(json.dumps({"type": "chat", "text": prompt, "source": "text"}))

        # Block on recv() until "done" or "error" — no deadline
        while True:
            try:
                raw = ws.recv()
            except Exception as exc:
                last_event = {"_recv_exception": f"{type(exc).__name__}: {exc}"}
                break
            if not raw:
                last_event = {"_recv": "empty"}
                break
            try:
                event = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                continue

            etype = event.get("type", "")
            if etype == "ping":
                continue
            last_event = event
            if etype == "message":
                # Response is in blocks[].content, not a top-level "text" field
                blocks = event.get("blocks", [])
                text_parts = [b.get("content", "") for b in blocks if b.get("type") == "text"]
                if text_parts:
                    response_text = "\n".join(text_parts)
            if etype in ("done", "error"):
                terminator = etype
                break

        # Brief drain for async card/push events
        if terminator == "done":
            ws.settimeout(2)
            drain_end = time.time() + 2
            while time.time() < drain_end:
                try:
                    raw = ws.recv()
                    if not raw:
                        break
                    event = json.loads(raw)
                    if event.get("type") == "message":
                        blocks = event.get("blocks", [])
                        text_parts = [b.get("content", "") for b in blocks if b.get("type") == "text"]
                        if text_parts:
                            response_text = "\n".join(text_parts)
                except Exception:
                    break
    finally:
        ws.close()

    if response_text:
        print(response_text)
    else:
        # Include terminator + last event so run_eval's stderr snippet shows WHY
        # the response was empty (server error, WS closed early, etc.) rather
        # than just "empty response from Chalie".
        preview = json.dumps(last_event)[:400] if last_event else "<no events received>"
        print(
            f"ERROR: empty response from Chalie (terminator={terminator}; last_event={preview})",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
