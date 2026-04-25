#!/usr/bin/env python3
"""
openclaw_chat.py

Sends a single chat message to an OpenClaw gateway via its OpenAI-compatible
chat completions endpoint and prints the response text.
Used as the per-call harness command for membench run_eval.py.

Session continuity across calls is handled by the x-openclaw-session-key header
— every call using the same key is routed to the same OpenClaw session.

Usage:
  python3 src/openclaw_chat.py \
    --base-url http://localhost:19089 \
    --session-key membench-eval \
    --prompt "Your prompt here"

Exits 0 and prints response text to stdout on success.
Exits 1 and prints error to stderr on failure (run_eval.py will retry).
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--session-key", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--model", default="openclaw/default")
    parser.add_argument("--auth-token", default=os.environ.get("OPENCLAW_TOKEN", ""))
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    url = args.base_url.rstrip("/") + "/v1/chat/completions"
    body = json.dumps({
        "model": args.model,
        "messages": [{"role": "user", "content": args.prompt}],
        "stream": False,
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "x-openclaw-session-key": args.session_key,
    }
    if args.auth_token:
        headers["Authorization"] = f"Bearer {args.auth_token}"

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"ERROR: HTTP {e.code} from {url}: {err_body[:500]}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: request to {url} failed: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        print(f"ERROR: non-JSON response: {raw[:500]}", file=sys.stderr)
        sys.exit(1)

    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        print(f"ERROR: unexpected response shape: {json.dumps(payload)[:500]}", file=sys.stderr)
        sys.exit(1)

    if not content or not content.strip():
        print("ERROR: empty response from OpenClaw", file=sys.stderr)
        sys.exit(1)

    print(content)


if __name__ == "__main__":
    main()
