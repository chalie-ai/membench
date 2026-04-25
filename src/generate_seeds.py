#!/usr/bin/env python3
"""
generate_seeds.py

Reads eval/step_1/seed_data.json (built by build_seeds.py), renders prompts,
sends them to Ollama, and saves the generated content.

Output files:
  eval/step_1/seeds/bio_{id}.md       — 150 biographies
  eval/step_1/seeds/project_{id}.md   — 300 project specs
  eval/step_1/seeds/article_{id}.md   — 25 articles

Usage:
  python src/generate_seeds.py --host localhost:11434 --model llama3
  python src/generate_seeds.py --host localhost:11434 --model llama3 --type bio --start 0 --end 10
  python src/generate_seeds.py --host localhost:11434 --model llama3 --type article
"""

import argparse
import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).parent.parent
SEED_DATA = ROOT / "eval" / "step_1" / "seed_data.json"
SEEDS_DIR = ROOT / "eval" / "step_1" / "seeds"


def load_seed_data() -> dict:
    with open(SEED_DATA) as f:
        return json.load(f)


def render_prompt(template: str, variant: dict) -> str:
    """Replace {placeholders} with variant values. Skip non-string fields."""
    fields = {k: v for k, v in variant.items() if k not in ("id", "type", "family", "linked_bio_ids") and isinstance(v, str)}
    return template.format(**fields)


def call_ollama(host: str, model: str, prompt: str, timeout: int = 600) -> str:
    url = f"http://{host}/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    response = requests.post(url, json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()["response"]


def process_variants(host, model, template, variants, prefix, timeout):
    """Send each variant to Ollama and save the result."""
    total = len(variants)
    errors = []

    for i, variant in enumerate(variants):
        vid = variant["id"]
        out_path = SEEDS_DIR / f"{prefix}_{vid}.md"

        if out_path.exists():
            print(f"  [{i+1:>4}/{total}] {prefix}_{vid}.md exists, skipping")
            continue

        prompt = render_prompt(template, variant)

        try:
            result = call_ollama(host, model, prompt, timeout=timeout)
            out_path.write_text(result, encoding="utf-8")
            print(f"  [{i+1:>4}/{total}] wrote {prefix}_{vid}.md")
        except requests.exceptions.RequestException as e:
            print(f"  [{i+1:>4}/{total}] ERROR: {e}")
            errors.append((vid, str(e)))
            time.sleep(1)

    return errors


def main():
    parser = argparse.ArgumentParser(description="Generate membench seed content via Ollama")
    parser.add_argument("--host", required=True, help="Ollama host:port")
    parser.add_argument("--model", required=True, help="Ollama model name")
    parser.add_argument("--type", choices=["bio", "project", "article", "all"], default="all",
                        help="Which seed type to generate (default: all)")
    parser.add_argument("--start", type=int, default=None, help="First ID (inclusive)")
    parser.add_argument("--end", type=int, default=None, help="Last ID (exclusive)")
    parser.add_argument("--timeout", type=int, default=900, help="Ollama timeout per request (default: 900)")
    args = parser.parse_args()

    SEEDS_DIR.mkdir(parents=True, exist_ok=True)
    data = load_seed_data()

    def filter_range(variants):
        if args.start is not None or args.end is not None:
            s = args.start or 0
            e = args.end if args.end is not None else len(variants)
            return [v for v in variants if s <= v["id"] < e]
        return variants

    all_errors = []

    if args.type in ("bio", "all"):
        bios = filter_range(data["biographies"])
        print(f"\nGenerating {len(bios)} biographies...")
        all_errors += process_variants(args.host, args.model, data["bio_template"], bios, "bio", args.timeout)

    if args.type in ("project", "all"):
        projects = filter_range(data["project_specs"])
        print(f"\nGenerating {len(projects)} project specs...")
        all_errors += process_variants(args.host, args.model, data["project_template"], projects, "project", args.timeout)

    if args.type in ("article", "all"):
        articles = filter_range(data["articles"])
        print(f"\nGenerating {len(articles)} articles...")
        all_errors += process_variants(args.host, args.model, data["article_template"], articles, "article", args.timeout)

    if all_errors:
        print(f"\n{len(all_errors)} total error(s)")
        sys.exit(1)
    else:
        print("\nDone.")


if __name__ == "__main__":
    main()
