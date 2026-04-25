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
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path

INGESTION_TEMPLATE = """Memorise this document: {bio_contents}"""


MAX_RETRIES = 3
RETRY_BACKOFF_S = 5.0  # linear backoff between failed attempts — stops us from
                       # hammering a flaky backend when every attempt fails fast.


def call_harness(cmd_template: str, prompt: str, timeout: int = 600) -> str:
    """Build command from template and execute.  Retries on timeout or empty response.

    Template supports two placeholders (pick whichever the harness needs):

      {prompt}       — inline, shell-quoted prompt string.  Fine for short
                       inputs.  On hosts where sudoers has `Defaults
                       log_subcmds` (TrueNAS Scale), large prompts (>~8 KB)
                       get SIGKILL'd by sudo's ptrace argv-consistency check,
                       which is why {prompt_file} exists.
      {prompt_file}  — path to a temp file containing the prompt body.  Keeps
                       execve() argv tiny and sudo-safe.  The file is written
                       under /tmp and unlinked after the subprocess exits.

    A template may use only one of the two; whichever is present gets
    substituted and the other is ignored.
    """
    prompt_file_path: str | None = None
    if "{prompt_file}" in cmd_template:
        # Write the prompt to a tempfile so the subprocess argv stays small.
        # NamedTemporaryFile with delete=False because we pass the path to a
        # child process; we clean it up explicitly in the `finally` below.
        tf = tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8",
            prefix="membench_prompt_", suffix=".txt",
            delete=False,
        )
        try:
            tf.write(prompt)
        finally:
            tf.close()
        prompt_file_path = tf.name
        cmd = cmd_template.replace("{prompt_file}", shlex.quote(prompt_file_path))
    else:
        cmd = cmd_template.replace("{prompt}", shlex.quote(prompt))

    try:
        return _run_with_retries(cmd, timeout)
    finally:
        if prompt_file_path is not None:
            try:
                os.unlink(prompt_file_path)
            except OSError:
                pass


def _run_with_retries(cmd: str, timeout: int) -> str:
    """Execute the fully-formed shell command with MAX_RETRIES + backoff.

    Split out of call_harness() so the tempfile cleanup logic stays readable
    — retries live here, prompt-file lifetime lives in the caller.
    """

    for attempt in range(1, MAX_RETRIES + 1):
        t0 = time.time()
        try:
            result = subprocess.run(
                ["bash", "-c", cmd],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            elapsed = time.time() - t0
            stdout = result.stdout.strip()
            if result.returncode != 0 or not stdout:
                stderr_snippet = (result.stderr or "").strip()[:200]
                if attempt < MAX_RETRIES:
                    wait = RETRY_BACKOFF_S * attempt
                    print(f"        EMPTY/ERROR response (rc={result.returncode}, {elapsed:.1f}s, attempt {attempt}/{MAX_RETRIES}), retrying in {wait:.0f}s...")
                    if stderr_snippet:
                        print(f"        stderr: {stderr_snippet}")
                    time.sleep(wait)
                    continue
                else:
                    print(f"        EMPTY/ERROR after {MAX_RETRIES} attempts (rc={result.returncode}, {elapsed:.1f}s)")
                    if stderr_snippet:
                        print(f"        stderr: {stderr_snippet}")
                    return stdout
            print(f"        ({elapsed:.1f}s)")
            return stdout
        except subprocess.TimeoutExpired:
            elapsed = time.time() - t0
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF_S * attempt
                print(f"        TIMEOUT after {elapsed:.0f}s (attempt {attempt}/{MAX_RETRIES}), retrying in {wait:.0f}s...")
                time.sleep(wait)
            else:
                raise


def extract_answer(response: str) -> str:
    """Extract text from [ANSWER]...[/ANSWER] tags. Falls back to full response."""
    m = re.search(r'\[ANSWER\](.*?)\[/ANSWER\]', response, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return response.strip()


def score_numeric(answer: str, scoring: dict) -> tuple[float, str]:
    """Extract numbers from answer, check against scoring map."""
    numbers = re.findall(r'\b\d+\b', answer)
    best_score = 0.0
    best_match = None
    for num in numbers:
        if num in scoring:
            s = scoring[num]
            if s > best_score:
                best_score = s
                best_match = num
    return best_score, best_match


def score_keywords(answer: str, scoring: list) -> tuple[float, list]:
    """Check keyword groups against answer (case-insensitive).

    Scoring entries are ordered best-to-worst (1.0, 0.7, 0.4, ...).
    First match wins.
    """
    lower = answer.lower()
    for entry in scoring:
        keywords = entry["keywords"]
        if all(kw.lower() in lower for kw in keywords):
            return entry["score"], keywords
    return 0.0, None


def score_question(question: dict, response: str) -> dict:
    answer_type = question.get("answer_type")
    scoring = question["scoring"]
    answer = extract_answer(response)

    if answer_type == "keywords":
        score, matched = score_keywords(answer, scoring)
    elif answer_type == "numeric":
        score, matched = score_numeric(answer, scoring)
    else:
        score, matched = score_numeric(answer, scoring)

    return {
        "question_id": question["id"],
        "question": question["question"],
        "expected": question["answer"],
        "response": response,
        "extracted_answer": answer,
        "score": score,
        "matched": matched,
    }


def run_ingestion(cmd_template: str, seeds_dir: Path, pattern: str, label: str, timeout: int):
    files = sorted(seeds_dir.glob(pattern), key=lambda p: int(p.stem.split("_")[1]))
    total = len(files)

    if total == 0:
        print(f"ERROR: no {pattern} files found in", seeds_dir)
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f" PHASE 1: INGESTION — {total} {label}")
    print(f"{'='*60}\n")

    errors = []
    for i, file_path in enumerate(files):
        contents = file_path.read_text(encoding="utf-8")
        prompt = INGESTION_TEMPLATE.format(bio_contents=contents)

        try:
            response = call_harness(cmd_template, prompt, timeout=timeout)
            print(f"  [{i+1:>4}/{total}] ingested {file_path.name}")
            print(f"        response: {response}")
        except subprocess.TimeoutExpired:
            print(f"  [{i+1:>4}/{total}] TIMEOUT {file_path.name}")
            errors.append(("timeout", file_path.name))
        except Exception as e:
            print(f"  [{i+1:>4}/{total}] ERROR {file_path.name}: {e}")
            errors.append(("error", file_path.name, str(e)))

    print(f"\nIngestion complete: {total - len(errors)}/{total} succeeded")
    if errors:
        print(f"  {len(errors)} failures")
    return errors


def run_questions(cmd_template: str, questions_path: Path, timeout: int, label: str = "documents") -> list:
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

        prompt = (
            f'Based on the {label} I asked you to memorise, answer the following question: '
            f'"{q["question"]}" directly, no reasoning, no narration. '
            f'And within the tags: [ANSWER][/ANSWER]. '
            f'Example: [ANSWER]this is my answer[/ANSWER]'
        )

        try:
            response = call_harness(cmd_template, prompt, timeout=timeout)
        except subprocess.TimeoutExpired:
            response = ""
            print(f"        TIMEOUT")
        except Exception as e:
            response = ""
            print(f"        ERROR: {e}")

        result = score_question(q, response)
        results.append(result)

        icon = "PASS" if result["score"] == 1.0 else "PARTIAL" if result["score"] > 0 else "FAIL"
        print(f"        expected={result['expected']}  extracted={result['extracted_answer']}  matched={result['matched']}  score={result['score']}  [{icon}]")

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
    parser.add_argument("--seeds-dir", required=True,
                        help="Directory containing seed files")
    parser.add_argument("--pattern", default="bio_*.md",
                        help="Glob pattern for seed files (default: bio_*.md)")
    parser.add_argument("--label", default="documents",
                        help="Label for ingestion and question prompts (default: documents)")
    parser.add_argument("--questions", required=True,
                        help="Path to questions.json")
    parser.add_argument("--output", default=None,
                        help="Path to write results JSON")
    parser.add_argument("--timeout", type=int, default=600,
                        help="Per-call timeout in seconds (default: 600)")
    parser.add_argument("--retries", type=int, default=3,
                        help="Max retries on timeout (default: 3)")
    parser.add_argument("--skip-ingestion", action="store_true",
                        help="Skip phase 1, go straight to questions")
    args = parser.parse_args()

    global MAX_RETRIES
    MAX_RETRIES = args.retries

    seeds_dir = Path(args.seeds_dir)
    questions_path = Path(args.questions)

    # Phase 1
    if not args.skip_ingestion:
        run_ingestion(args.harness_cmd, seeds_dir, args.pattern, args.label, args.timeout)

    # Phase 2
    results = run_questions(args.harness_cmd, questions_path, args.timeout, args.label)

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
