#!/usr/bin/env python3
"""Analyze quiz results and print learning-focused feedback.

Input formats:
1) Answers file as mapping from question id to selected option index (0-based):
   {
     "mqtt-001": 1,
     "mqtt-002": 1
   }

2) Or as mapping from question id to selected option text:
   {
     "mqtt-001": "Daten werden vom Absender an ein Topic gesendet ..."
   }

Usage:
  python scripts/analyze_quiz_results.py "MQTT Quiz.json" answers.json
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path


def _question_area(question_id: str) -> str:
    mapping = {
        "mqtt-001": "Pub/Sub",
        "mqtt-002": "Broker",
        "mqtt-003": "Topics",
        "mqtt-004": "Wildcards",
        "mqtt-005": "QoS",
        "mqtt-006": "Retain",
        "mqtt-007": "LWT",
        "mqtt-008": "Session/Keep Alive",
        "mqtt-009": "IoT Szenario",
        "mqtt-010": "IoT Troubleshooting",
    }
    return mapping.get(question_id, "Sonstiges")


def _selected_is_correct(question: dict, selected: object) -> bool:
    options = question.get("answerOptions", [])
    if isinstance(selected, int):
        if selected < 0 or selected >= len(options):
            return False
        return bool(options[selected].get("isCorrect") is True)

    if isinstance(selected, str):
        for option in options:
            if option.get("text") == selected:
                return bool(option.get("isCorrect") is True)
    return False


def analyze(quiz: dict, answers: dict[str, object]) -> str:
    questions = quiz.get("questions", [])
    total = len(questions)
    score = 0

    per_area = defaultdict(lambda: {"ok": 0, "total": 0})

    for q in questions:
        qid = q.get("id", "")
        area = _question_area(qid)
        per_area[area]["total"] += 1

        selected = answers.get(qid)
        if _selected_is_correct(q, selected):
            score += 1
            per_area[area]["ok"] += 1

    percentage = 0 if total == 0 else round((score / total) * 100)

    strong = []
    review = []
    for area, stats in per_area.items():
        if stats["ok"] == stats["total"]:
            strong.append(area)
        elif stats["ok"] < stats["total"]:
            review.append(area)

    recommendation_map = {
        "QoS": "Review MQTT QoS levels (0/1/2) with delivery trade-offs.",
        "Wildcards": "Practice topic filters with + and # in realistic hierarchies.",
        "Session/Keep Alive": "Revisit how Keep Alive differs from Persistent Session.",
        "Retain": "Practice retained-state use cases for newly connecting clients.",
        "LWT": "Review failure signaling flows using Last Will Testament.",
        "IoT Szenario": "Try building 3 more topic-filter scenarios from factory data.",
        "IoT Troubleshooting": "Work through startup and offline-debugging MQTT cases.",
    }

    lines = []
    lines.append("QUIZ RESULT")
    lines.append("")
    lines.append(f"Score       {score} / {total}")
    lines.append(f"Percentage  {percentage}%")
    lines.append("")

    lines.append("Strong:")
    if strong:
        for area in sorted(strong):
            lines.append(f"[OK] {area}")
    else:
        lines.append("[OK] -")

    lines.append("")
    lines.append("Review:")
    if review:
        for area in sorted(review):
            lines.append(f"[WARN] {area}")
    else:
        lines.append("[WARN] -")

    lines.append("")
    lines.append("Recommended:")
    if review:
        for area in sorted(review):
            lines.append(f"-> {recommendation_map.get(area, 'Review this topic with additional practice questions.')}")
    else:
        lines.append("-> Great job. Increase difficulty with timed scenario drills.")

    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("Usage: python scripts/analyze_quiz_results.py <quiz.json> <answers.json>")
        return 2

    quiz_path = Path(argv[1])
    answers_path = Path(argv[2])

    try:
        quiz = json.loads(quiz_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Failed to read quiz JSON: {exc}")
        return 1

    try:
        answers = json.loads(answers_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Failed to read answers JSON: {exc}")
        return 1

    if not isinstance(answers, dict):
        print("answers.json must be an object keyed by question id")
        return 1

    print(analyze(quiz, answers))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
