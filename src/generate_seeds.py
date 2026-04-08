#!/usr/bin/env python3
"""
generate_seeds.py

Reads seed_gen.json, constructs a prompt per variant, sends it to Ollama,
and stores the generated biography as eval/step_1/seeds/bio_{id}.md.

Usage:
  python src/generate_seeds.py --host localhost:11434 --model llama3

  # Process a specific range of IDs
  python src/generate_seeds.py --host localhost:11434 --model llama3 --start 0 --end 10
"""

import argparse
import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).parent.parent
SEED_GEN_JSON = ROOT / "eval" / "step_1" / "seed_gen.json"
SEEDS_DIR = ROOT / "eval" / "step_1" / "seeds"


def load_seed_gen() -> dict:
    with open(SEED_GEN_JSON) as f:
        return json.load(f)


def build_prompt(template: str, variant: dict) -> str:
    return template.format(**{k: v for k, v in variant.items() if k != "id"})


def call_ollama(host: str, model: str, prompt: str, timeout: int = 300) -> str:
    url = f"http://{host}/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    response = requests.post(url, json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()["response"]


def main():
    parser = argparse.ArgumentParser(description="Generate membench biography seeds via Ollama")
    parser.add_argument("--host", required=True, help="Ollama host:port (e.g. localhost:11434)")
    parser.add_argument("--model", required=True, help="Ollama model name (e.g. llama3)")
    parser.add_argument("--start", type=int, default=None, help="First variant ID to process (inclusive)")
    parser.add_argument("--end", type=int, default=None, help="Last variant ID to process (exclusive)")
    parser.add_argument("--timeout", type=int, default=300, help="Ollama request timeout in seconds (default: 300)")
    args = parser.parse_args()

    SEEDS_DIR.mkdir(parents=True, exist_ok=True)

    data = load_seed_gen()
    template = data["prompt_template"]
    variants = data["variants"]

    if args.start is not None or args.end is not None:
        start = args.start or 0
        end = args.end if args.end is not None else len(variants)
        variants = [v for v in variants if start <= v["id"] < end]

    print(f"Generating {len(variants)} biography/biographies via {args.host} ({args.model})...")

    errors = []
    for variant in variants:
        vid = variant["id"]
        bio_path = SEEDS_DIR / f"bio_{vid}.md"

        if bio_path.exists():
            print(f"  [{vid:>4}] bio_{vid}.md already exists, skipping")
            continue

        prompt = build_prompt(template, variant)

        try:
            biography = call_ollama(args.host, args.model, prompt, timeout=args.timeout)
            bio_path.write_text(biography, encoding="utf-8")
            print(f"  [{vid:>4}] wrote bio_{vid}.md")
        except requests.exceptions.RequestException as e:
            print(f"  [{vid:>4}] ERROR: {e}")
            errors.append((vid, str(e)))
            time.sleep(1)

    if errors:
        print(f"\n{len(errors)} error(s):")
        for vid, msg in errors:
            print(f"  variant {vid}: {msg}")
        sys.exit(1)
    else:
        print("\nDone.")


if __name__ == "__main__":
    main()
