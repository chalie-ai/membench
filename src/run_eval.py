#!/usr/bin/env python3
"""
run_eval.py

Runs a membench evaluation against any harness via a command template.

The harness command uses {prompt} as a placeholder:
  --harness-cmd "claude -p {prompt} --model claude-sonnet-4-6 --resume abc123"

Two phases:
  1. Ingestion — sends all bios with a "remember this" instruction
  2. Questions — sends each question, captures stdout, scores it

Usage:
  python src/run_eval.py \
    --harness-cmd "claude -p {prompt} --model claude-sonnet-4-6 --resume SESSION" \
    --bios-dir eval/step_1/seeds \
    --questions eval/step_1/tests/questions.json \
    --output eval/step_1/results.json
"""

import argparse
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

INGESTION_TEMPLATE = """{bio_contents}

---

Above is a biography of one person in a large person database. Remember this person for later."""


def call_harness(cmd_template: str, prompt: str, timeout: int = 300) -> str:
    """Replace {prompt} in cmd_template and execute. Returns stdout."""
    cmd = cmd_template.replace("{prompt}", shlex.quote(prompt))

    result = subprocess.run(
        ["bash", "-c", cmd],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.stdout.strip()


def score_numeric(response: str, scoring: dict) -> tuple[float, str]:
    """Extract numbers from response, check against scoring map."""
    numbers = re.findall(r'\b\d+\b', response)
    best_score = 0.0
    best_match = None
    for num in numbers:
        if num in scoring:
            s = scoring[num]
            if s > best_score:
                best_score = s
                best_match = num
    return best_score, best_match


def score_keywords(response: str, scoring: list) -> tuple[float, list]:
    """Check keyword groups against response (case-insensitive)."""
    lower = response.lower()
    for entry in scoring:
        keywords = entry["keywords"]
        if all(kw.lower() in lower for kw in keywords):
            return entry["score"], keywords
    return 0.0, None


def score_question(question: dict, response: str) -> dict:
    answer_type = question.get("answer_type")
    scoring = question["scoring"]

    if answer_type == "keywords":
        score, matched = score_keywords(response, scoring)
    else:
        score, matched = score_numeric(response, scoring)

    return {
        "question_id": question["id"],
        "question": question["question"],
        "expected": question["answer"],
        "response": response,
        "score": score,
        "matched": matched,
    }


def run_ingestion(cmd_template: str, bios_dir: Path, timeout: int):
    bio_files = sorted(bios_dir.glob("bio_*.md"), key=lambda p: int(p.stem.split("_")[1]))
    total = len(bio_files)

    if total == 0:
        print("ERROR: no bio_*.md files found in", bios_dir)
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f" PHASE 1: INGESTION — {total} biographies")
    print(f"{'='*60}\n")

    errors = []
    for i, bio_path in enumerate(bio_files):
        bio_contents = bio_path.read_text(encoding="utf-8")
        prompt = INGESTION_TEMPLATE.format(bio_contents=bio_contents)

        try:
            response = call_harness(cmd_template, prompt, timeout=timeout)
            print(f"  [{i+1:>4}/{total}] ingested {bio_path.name}")
            print(f"        response: {response}")
        except subprocess.TimeoutExpired:
            print(f"  [{i+1:>4}/{total}] TIMEOUT {bio_path.name}")
            errors.append(("timeout", bio_path.name))
        except Exception as e:
            print(f"  [{i+1:>4}/{total}] ERROR {bio_path.name}: {e}")
            errors.append(("error", bio_path.name, str(e)))

    print(f"\nIngestion complete: {total - len(errors)}/{total} succeeded")
    if errors:
        print(f"  {len(errors)} failures")
    return errors


def run_questions(cmd_template: str, questions_path: Path, timeout: int) -> list:
    with open(questions_path) as f:
        questions = json.load(f)

    total = len(questions)

    print(f"\n{'='*60}")
    print(f" PHASE 2: QUESTIONS — {total} questions")
    print(f"{'='*60}\n")

    results = []
    for q in questions:
        qid = q["id"]
        print(f"  [Q{qid:>2}] {q['question']}")

        try:
            response = call_harness(cmd_template, q["question"], timeout=timeout)
        except subprocess.TimeoutExpired:
            response = ""
            print(f"        TIMEOUT")
        except Exception as e:
            response = ""
            print(f"        ERROR: {e}")

        result = score_question(q, response)
        results.append(result)

        icon = "PASS" if result["score"] == 1.0 else "PARTIAL" if result["score"] > 0 else "FAIL"
        print(f"        expected={result['expected']}  got={result['matched']}  score={result['score']}  [{icon}]")

    return results


def print_summary(results: list):
    total = len(results)
    scores = [r["score"] for r in results]
    perfect = sum(1 for s in scores if s == 1.0)
    partial = sum(1 for s in scores if 0 < s < 1.0)
    failed = sum(1 for s in scores if s == 0.0)
    avg = sum(scores) / total if total else 0

    print(f"\n{'='*60}")
    print(f" RESULTS")
    print(f"{'='*60}")
    print(f"  Total questions:  {total}")
    print(f"  Perfect (1.0):    {perfect}")
    print(f"  Partial (>0):     {partial}")
    print(f"  Failed  (0):      {failed}")
    print(f"  Average score:    {avg:.2%}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Run membench evaluation")
    parser.add_argument("--harness-cmd", required=True,
                        help="Command template with {prompt} placeholder")
    parser.add_argument("--bios-dir", required=True,
                        help="Directory containing bio_*.md files")
    parser.add_argument("--questions", required=True,
                        help="Path to questions.json")
    parser.add_argument("--output", default=None,
                        help="Path to write results JSON")
    parser.add_argument("--timeout", type=int, default=300,
                        help="Per-call timeout in seconds (default: 300)")
    parser.add_argument("--skip-ingestion", action="store_true",
                        help="Skip phase 1, go straight to questions")
    args = parser.parse_args()

    bios_dir = Path(args.bios_dir)
    questions_path = Path(args.questions)

    # Phase 1
    if not args.skip_ingestion:
        run_ingestion(args.harness_cmd, bios_dir, args.timeout)

    # Phase 2
    results = run_questions(args.harness_cmd, questions_path, args.timeout)

    # Summary
    print_summary(results)

    # Write output
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "harness_cmd": args.harness_cmd,
            "total_questions": len(results),
            "average_score": sum(r["score"] for r in results) / len(results) if results else 0,
            "results": results,
        }
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Results written to {output_path}")


if __name__ == "__main__":
    main()
