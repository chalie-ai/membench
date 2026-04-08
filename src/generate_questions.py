#!/usr/bin/env python3
"""
generate_questions.py

Generates 20 deterministic trait-extraction questions from seed_gen.json
and writes them to eval/step_1/tests/questions.json.

Each question includes scoring bands that grade proximity to the correct answer:
  - Numeric: percentage-based bands (exact=1.0, ≤10% off=0.7, ≤30% off=0.4, else=0.0)
  - String:  exact match=1.0, else=0.0
"""

import json
import math
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent.parent
SEED_GEN_JSON = ROOT / "eval" / "step_1" / "seed_gen.json"
OUT_PATH = ROOT / "eval" / "step_1" / "tests" / "questions.json"


def numeric_scoring(n: int) -> list:
    """Build scoring bands for a numeric answer.

    Bands are evaluated top-to-bottom, first match wins.
    Ranges are inclusive [min, max].
    """
    if n == 0:
        return [
            {"min": 0, "max": 0, "score": 1.0},
            {"min": 0, "max": 1, "score": 0.4},
            {"score": 0.0},
        ]

    lo_70 = math.ceil(n * 0.90)
    hi_70 = math.floor(n * 1.10)
    lo_40 = math.ceil(n * 0.70)
    hi_40 = math.floor(n * 1.30)

    return [
        {"min": n,     "max": n,     "score": 1.0},
        {"min": lo_70, "max": hi_70, "score": 0.7},
        {"min": lo_40, "max": hi_40, "score": 0.4},
        {"score": 0.0},
    ]


def exact_match_scoring() -> list:
    return [
        {"match": "exact", "score": 1.0},
        {"score": 0.0},
    ]


def build_questions(variants: list, rng: random.Random) -> list:
    questions = []

    def count(field):
        return Counter(v[field] for v in variants)

    def add_numeric(q, a):
        questions.append({
            "question": q,
            "answer": a,
            "answer_type": "numeric",
            "scoring": numeric_scoring(a),
        })

    def add_exact(q, a):
        questions.append({
            "question": q,
            "answer": a,
            "answer_type": "exact_match",
            "scoring": exact_match_scoring(),
        })

    city_counts = count("current_city")
    origin_counts = count("origin")
    prof_counts = count("profession")
    age_counts = count("age")
    color_counts = count("fav_color")
    chrono_counts = count("chronotype")
    hobby1_counts = count("hobby_1")
    religion_counts = count("religion")
    pet_counts = count("pet")

    # ── Counting: how many people have trait X (Q0–Q9) ─────────────────────

    city, n = rng.choice(list(city_counts.items()))
    add_numeric(f"How many people currently live in {city}?", n)

    origin, n = rng.choice(list(origin_counts.items()))
    add_numeric(f"How many people were born and raised in {origin}?", n)

    prof, n = rng.choice(list(prof_counts.items()))
    add_numeric(f"How many people work as a {prof}?", n)

    age, n = rng.choice(list(age_counts.items()))
    add_numeric(f"How many people are {age} years old?", int(n))

    color, n = rng.choice(list(color_counts.items()))
    add_numeric(f"How many people have {color} as their favorite color?", n)

    chrono, n = rng.choice(list(chrono_counts.items()))
    add_numeric(f"How many people are described as: {chrono}?", n)

    hobby, n = rng.choice(list(hobby1_counts.items()))
    add_numeric(f"How many people have \"{hobby}\" as their primary hobby?", n)

    rel, n = rng.choice(list(religion_counts.items()))
    add_numeric(f"How many people identify as: {rel}?", n)

    pet, n = rng.choice(list(pet_counts.items()))
    add_numeric(f"How many people have \"{pet}\" as their pet situation?", n)

    city2, n = rng.choice([(c, n) for c, n in city_counts.items() if c != city])
    add_numeric(f"How many people currently live in {city2}?", n)

    # ── Most / least common (Q10–Q15) ──────────────────────────────────────

    top_prof, _ = prof_counts.most_common(1)[0]
    add_exact("What is the most common profession in the dataset?", top_prof)

    top_city, _ = city_counts.most_common(1)[0]
    add_exact("What is the most common current city of residence?", top_city)

    top_color, _ = color_counts.most_common(1)[0]
    add_exact("What is the most popular favorite color?", top_color)

    top_origin, _ = origin_counts.most_common(1)[0]
    add_exact("What is the most common birthplace?", top_origin)

    least_pet, _ = pet_counts.most_common()[-1]
    add_exact("What is the least common pet situation?", least_pet)

    top_age, _ = age_counts.most_common(1)[0]
    add_exact(f"What is the most common age in the dataset?", top_age)

    # ── Cross-field / derived (Q16–Q19) ────────────────────────────────────

    target_city = city_counts.most_common(1)[0][0]
    profs_in_city = sorted(set(v["profession"] for v in variants if v["current_city"] == target_city))
    add_numeric(f"How many distinct professions are there among people living in {target_city}?", len(profs_in_city))

    combo = sum(1 for v in variants if v["profession"] == top_prof and v["current_city"] == target_city)
    add_numeric(f"How many people work as a {top_prof} and live in {target_city}?", combo)

    add_numeric("How many distinct birthplaces are represented in the dataset?", len(origin_counts))

    over_50 = sum(1 for v in variants if int(v["age"]) > 50)
    add_numeric("How many people in the dataset are over 50 years old?", over_50)

    return questions


def main():
    rng = random.Random(42)

    with open(SEED_GEN_JSON) as f:
        data = json.load(f)
    variants = data["variants"]

    questions = build_questions(variants, rng)

    for i, q in enumerate(questions):
        q["id"] = i

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(questions, f, indent=2)

    print(f"Wrote {len(questions)} questions to {OUT_PATH}")


if __name__ == "__main__":
    main()
