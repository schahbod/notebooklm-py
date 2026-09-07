#!/usr/bin/env python3
"""Validate quiz JSON structure and learning-data constraints.

Usage:
  python scripts/validate_quiz_json.py "MQTT Quiz.json"
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ALLOWED_DIFFICULTY = {"easy", "medium", "hard"}


def _fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def validate_quiz(path: Path) -> tuple[bool, list[str], list[str]]:
    errors: list[str] = []
    checks: list[str] = []

    if not path.exists():
        return False, [], [f"File not found: {path}"]

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, [], [f"Invalid JSON: {exc}"]

    questions = payload.get("questions")
    if not isinstance(questions, list) or not questions:
        return False, [], ["questions must be a non-empty array"]

    checks.append(f"{len(questions)} questions")

    seen_ids: set[str] = set()
    seen_questions: set[str] = set()

    for idx, q in enumerate(questions, start=1):
        q_label = f"Question {idx}"

        qid = q.get("id")
        if not isinstance(qid, str) or not qid.strip():
            _fail(f"{q_label}: missing ID", errors)
        elif qid in seen_ids:
            _fail(f"{q_label}: duplicate ID '{qid}'", errors)
        else:
            seen_ids.add(qid)

        difficulty = q.get("difficulty")
        if difficulty not in ALLOWED_DIFFICULTY:
            _fail(
                f"{q_label}: invalid difficulty '{difficulty}' (allowed: easy, medium, hard)",
                errors,
            )

        q_text = q.get("question")
        if not isinstance(q_text, str) or not q_text.strip():
            _fail(f"{q_label}: missing question text", errors)
        elif q_text in seen_questions:
            _fail(f"{q_label}: duplicate question text", errors)
        else:
            seen_questions.add(q_text)

        options = q.get("answerOptions")
        if not isinstance(options, list):
            _fail(f"{q_label}: answerOptions must be an array", errors)
            continue

        if len(options) < 3:
            _fail(f"{q_label}: fewer than 3 answer options", errors)

        correct_count = 0
        for option_index, option in enumerate(options, start=1):
            is_correct = option.get("isCorrect")
            if is_correct is True:
                correct_count += 1
            elif is_correct is not False:
                _fail(
                    f"{q_label}: option {option_index} has non-boolean isCorrect value",
                    errors,
                )

        if correct_count == 0:
            _fail(f"{q_label}: 0 correct answers", errors)
        elif correct_count > 1:
            _fail(f"{q_label}: {correct_count} correct answers", errors)

    if not errors:
        checks.append(f"{len(seen_ids)} unique IDs")
        checks.append("Each question has exactly one correct answer")
        checks.append("All questions have >=3 options")
        checks.append("No duplicate question text")
        checks.append("Valid difficulty values")

    return (len(errors) == 0), checks, errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python scripts/validate_quiz_json.py <quiz.json>")
        return 2

    quiz_path = Path(argv[1])
    ok, checks, errors = validate_quiz(quiz_path)

    if ok:
        print("Validation passed")
        for item in checks:
            print(f"[OK] {item}")
        return 0

    print("Validation failed")
    for err in errors:
        print(f"[ERR] {err}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
