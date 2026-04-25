#!/usr/bin/env python3
"""
chalie_setup.py

Prepares a Chalie instance for membench:
  1. Wait for /ready
  2. Register or login
  3. Deactivate deprecated providers
  4. Find or create Ollama provider for the target model
  5. Assign all cognitive jobs to that provider
  6. Wait for worker sync
  7. Reset conversation thread (clean slate for the benchmark)
  8. Save session cookies to JSON file
"""

import argparse
import json
import sys
import time

import requests

# Auth + provider calls are made seconds after Chalie reports ready, but
# Flask's worker pool can still be warming up — a connection reset on the
# first request is common.  Retry transient network errors before bailing.
RETRYABLE_EXCEPTIONS = (
    requests.exceptions.ConnectionError,
    requests.exceptions.ChunkedEncodingError,
    requests.exceptions.ReadTimeout,
)
NETWORK_RETRIES = 5
NETWORK_RETRY_BACKOFF_S = 2.0

JOBS = [
    "frontal-cortex-unified",
    "frontal-cortex-act",
    "frontal-cortex-scheduled-tool",
    "plan-decomposition",
    "episodic-memory",
    "semantic-memory",
    "compaction",
    "autobiography",
    "goal-strategy",
    "goal-emergence",
    "cognitive-triage",
    "experience-assimilation",
    "failure-analysis",
    "trait-extraction",
    "moment-enrichment",
    "document-synthesis",
    "ambient-wrapper",
]

DEPRECATED_PATTERNS = ["2.0-flash"]
WORKER_SYNC_WAIT = 12


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--username", default="membench")
    parser.add_argument("--password", default="membench123")
    parser.add_argument("--cookie-file", required=True)
    parser.add_argument("--model", default="gemma4:31b-cloud")
    parser.add_argument("--ollama-host", default="http://grck.lan:30068")
    parser.add_argument("--ready-timeout", type=int, default=300)
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    session = requests.Session()

    # 1. Wait for /ready
    print(f"  [setup] Waiting for {base}/ready ...", flush=True)
    deadline = time.time() + args.ready_timeout
    ready = False
    last_err_reported: str | None = None
    while time.time() < deadline:
        try:
            r = requests.get(f"{base}/ready", timeout=5)
            if r.status_code == 200 and r.json().get("ready"):
                ready = True
                break
            err_key = f"status={r.status_code}"
        except Exception as exc:
            err_key = f"{type(exc).__name__}: {exc}"
        # Log only when the failure reason changes, so the user sees why we're
        # retrying without spamming. Silently-eaten errors previously hid the
        # IPv6/docker-proxy reset bug for 5 minutes before timeout.
        if err_key != last_err_reported:
            print(f"  [setup] /ready not yet — {err_key}", flush=True)
            last_err_reported = err_key
        time.sleep(2)

    if not ready:
        print(
            f"  [setup] ERROR: /ready did not return true within {args.ready_timeout}s — aborting",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(1)
    print("  [setup] System ready", flush=True)

    # 2. Authenticate
    print("  [setup] Authenticating ...", flush=True)
    reg = _post(session, f"{base}/auth/register", {"username": args.username, "password": args.password})
    if reg.get("ok"):
        print("  [setup] Registered new account", flush=True)
    else:
        login = _post(session, f"{base}/auth/login", {"username": args.username, "password": args.password})
        if not login.get("ok"):
            print(f"  [setup] ERROR: auth failed — register={reg}, login={login}", file=sys.stderr)
            sys.exit(1)
        print("  [setup] Logged in", flush=True)

    # Save cookies immediately after auth
    _save_cookies(session, args.cookie_file)

    # 3. Deactivate deprecated providers
    providers_resp = _get(session, f"{base}/providers")
    providers = providers_resp.get("providers", [])
    for p in providers:
        if any(pat in (p.get("model") or "") for pat in DEPRECATED_PATTERNS):
            _put(session, f"{base}/providers/{p['id']}", {"is_active": False})
            print(f"  [setup] Deactivated deprecated provider: {p['model']}", flush=True)

    # 4. Find or create Ollama provider
    existing = [
        p for p in providers
        if p.get("model") == args.model and p.get("platform") == "ollama"
    ]
    if existing:
        provider_id = existing[0]["id"]
        _put(session, f"{base}/providers/{provider_id}", {"is_active": True})
        print(f"  [setup] Provider ollama/{args.model} active (id={provider_id})", flush=True)
    else:
        safe_model = args.model.replace(".", "-").replace(":", "-")
        body = {
            "name": f"ollama-membench-{safe_model}",
            "platform": "ollama",
            "model": args.model,
            "host": args.ollama_host,
        }
        resp = _post(session, f"{base}/providers", body)
        provider_id = (resp.get("provider") or {}).get("id")
        if not provider_id:
            print(f"  [setup] ERROR: failed to create provider: {resp}", file=sys.stderr)
            sys.exit(1)
        print(f"  [setup] Created provider ollama/{args.model} (id={provider_id})", flush=True)

    # 5. Assign all jobs to this provider
    for job in JOBS:
        r = _put(session, f"{base}/providers/jobs/{job}", {"job_name": job, "provider_id": provider_id})
        if not (r.get("assignment") or {}).get("provider_id"):
            print(f"  [setup] WARNING: job assignment may have failed for {job}: {r}", flush=True)
    print(f"  [setup] {len(JOBS)} jobs assigned to provider {provider_id}", flush=True)

    # 6. Worker sync
    print(f"  [setup] Waiting {WORKER_SYNC_WAIT}s for worker sync ...", flush=True)
    time.sleep(WORKER_SYNC_WAIT)

    # 7. Reset conversation thread (clean slate)
    r = session.post(f"{base}/system/reset-thread", json={"channel": "user"}, timeout=30)
    print(f"  [setup] Thread reset: {r.status_code}", flush=True)

    # 8. Health check
    health = _get(session, f"{base}/health")
    if health.get("status") != "ok":
        print(f"  [setup] WARNING: health={health}", flush=True)
    else:
        print("  [setup] Health OK", flush=True)

    # Re-save cookies (may have been refreshed)
    _save_cookies(session, args.cookie_file)
    print("  [setup] Done", flush=True)


def _save_cookies(session: requests.Session, path: str):
    cookies = {c.name: c.value for c in session.cookies}
    with open(path, "w") as f:
        json.dump(cookies, f)
    print(f"  [setup] Cookies saved → {path}", flush=True)


def _request_with_retry(method, session, url, body=None):
    """Wrap session.<method>() with bounded retries on transient network errors.

    Chalie's Flask worker pool can close the first connection after a warm
    restart; one retry almost always succeeds.  Returns {"error": str} only
    after exhausting retries so callers can still branch on the result.
    """
    last_exc: Exception | None = None
    for attempt in range(1, NETWORK_RETRIES + 1):
        try:
            if method == "GET":
                resp = session.get(url, timeout=30)
            elif method == "POST":
                resp = session.post(url, json=body, timeout=30)
            elif method == "PUT":
                resp = session.put(url, json=body, timeout=30)
            else:
                return {"error": f"unsupported method {method}"}
            try:
                return resp.json()
            except ValueError:
                return {"error": f"non-json response ({resp.status_code}): {resp.text[:200]}"}
        except RETRYABLE_EXCEPTIONS as exc:
            last_exc = exc
            if attempt < NETWORK_RETRIES:
                wait = NETWORK_RETRY_BACKOFF_S * attempt
                print(
                    f"  [setup] transient {type(exc).__name__} on {method} {url} "
                    f"(attempt {attempt}/{NETWORK_RETRIES}) — retrying in {wait:.1f}s",
                    flush=True,
                )
                time.sleep(wait)
                continue
            break
        except Exception as exc:
            return {"error": str(exc)}
    return {"error": f"{type(last_exc).__name__ if last_exc else 'unknown'}: {last_exc}"}


def _post(session, url, body):
    return _request_with_retry("POST", session, url, body)


def _get(session, url):
    return _request_with_retry("GET", session, url)


def _put(session, url, body):
    return _request_with_retry("PUT", session, url, body)


if __name__ == "__main__":
    main()
