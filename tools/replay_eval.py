#!/usr/bin/env python3
"""
Decision replay evaluation for boss-skills.

Measures persona fidelity: can the distilled decision model (rubric +
decision_rules + cases) reproduce the boss's real historical decisions?

Workflow (agent-driven, the script stays LLM-free):

1. split  : hold out a fraction of cases; write a question pack with the
            decision/rationale/quote stripped, plus a separate answer key.
2. (agent): answer each held-out case as the boss, using only rubric.json,
            decision_rules.md and the remaining training cases; then compare
            with the answer key and write graded.json
            [{"id": "case-002", "match": true, "note": "..."}, ...]
3. score  : compute accuracy overall / by scene / by confidence from graded.json.

Usage:
  python tools/replay_eval.py --action split --slug lao-zhou --holdout 0.2
  python tools/replay_eval.py --action score --slug lao-zhou
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

HIDDEN_FIELDS = ("decision", "rationale", "quote", "outcome")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_cases(skill_dir: Path) -> list[dict]:
    cases_dir = skill_dir / "cases"
    if not cases_dir.exists():
        return []
    cases = []
    for case_path in sorted(cases_dir.glob("*.json")):
        try:
            cases.append(read_json(case_path))
        except Exception:
            continue
    return cases


def split(skill_dir: Path, holdout_ratio: float, seed: int) -> None:
    cases = load_cases(skill_dir)
    if len(cases) < 3:
        print(f"Error: need at least 3 cases to run replay eval, found {len(cases)}", file=sys.stderr)
        sys.exit(1)

    rng = random.Random(seed)
    shuffled = cases[:]
    rng.shuffle(shuffled)
    holdout_count = max(1, round(len(shuffled) * holdout_ratio))
    holdout, train = shuffled[:holdout_count], shuffled[holdout_count:]

    eval_dir = skill_dir / "eval"
    eval_dir.mkdir(exist_ok=True)

    questions = []
    answer_key = []
    for case in holdout:
        question = {key: value for key, value in case.items() if key not in HIDDEN_FIELDS}
        questions.append(question)
        answer_key.append({key: case.get(key, "") for key in ("id",) + HIDDEN_FIELDS})

    write_json(eval_dir / "replay_pack.json", questions)
    write_json(eval_dir / "answer_key.json", answer_key)
    write_json(eval_dir / "train_ids.json", [case.get("id") for case in train])

    print(f"Split {len(cases)} cases -> train {len(train)} / holdout {len(holdout)} (seed={seed})")
    print(f"Question pack : {eval_dir / 'replay_pack.json'}")
    print(f"Answer key    : {eval_dir / 'answer_key.json'}")
    print("Next: answer each question as the boss using ONLY rubric.json, decision_rules.md")
    print("and the training cases, then write eval/graded.json:")
    print('  [{"id": "case-002", "match": true, "note": "why"}, ...]')
    print("Finally run: --action score")


def score(skill_dir: Path) -> None:
    eval_dir = skill_dir / "eval"
    graded_path = eval_dir / "graded.json"
    if not graded_path.exists():
        print(f"Error: {graded_path} not found. Run split and grade the predictions first.", file=sys.stderr)
        sys.exit(1)

    graded = read_json(graded_path)
    if not isinstance(graded, list) or not graded:
        print("Error: graded.json must be a non-empty list", file=sys.stderr)
        sys.exit(1)

    cases_by_id = {case.get("id"): case for case in load_cases(skill_dir)}

    total = len(graded)
    matched = sum(1 for item in graded if item.get("match") is True)

    by_scene: dict[str, list[bool]] = defaultdict(list)
    by_confidence: dict[str, list[bool]] = defaultdict(list)
    for item in graded:
        case = cases_by_id.get(item.get("id"), {})
        by_scene[case.get("scene", "unknown")].append(item.get("match") is True)
        by_confidence[case.get("confidence", "unknown")].append(item.get("match") is True)

    print(f"Replay fidelity: {matched}/{total} = {matched / total:.0%}\n")
    print("By scene:")
    for scene, results in sorted(by_scene.items()):
        print(f"  {scene}: {sum(results)}/{len(results)}")
    print("By source confidence:")
    for confidence, results in sorted(by_confidence.items()):
        print(f"  {confidence}: {sum(results)}/{len(results)}")

    misses = [item for item in graded if item.get("match") is not True]
    if misses:
        print("\nMisses (use these to refine rubric/rules):")
        for item in misses:
            print(f"  [{item.get('id')}] {item.get('note', '')}")

    report = {
        "total": total,
        "matched": matched,
        "accuracy": round(matched / total, 4),
        "by_scene": {scene: f"{sum(r)}/{len(r)}" for scene, r in by_scene.items()},
        "by_confidence": {conf: f"{sum(r)}/{len(r)}" for conf, r in by_confidence.items()},
    }
    write_json(eval_dir / "report.json", report)
    print(f"\nReport saved: {eval_dir / 'report.json'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="boss-skills decision replay evaluation")
    parser.add_argument("--action", required=True, choices=["split", "score"])
    parser.add_argument("--slug", required=True)
    parser.add_argument("--base-dir", default="./bosses")
    parser.add_argument("--holdout", type=float, default=0.2, help="holdout ratio for split")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    skill_dir = Path(args.base_dir).expanduser() / args.slug
    if not skill_dir.exists():
        print(f"Error: skill directory not found: {skill_dir}", file=sys.stderr)
        sys.exit(1)

    if args.action == "split":
        split(skill_dir, args.holdout, args.seed)
    else:
        score(skill_dir)


if __name__ == "__main__":
    main()
