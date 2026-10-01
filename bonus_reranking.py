"""Offline Exercise 3.5 analysis using saved retrieval traces.

The question is the reranking query. The expected answer is used only for
scoring after both rankings have been fixed; no answer generation occurs.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict, deque
from pathlib import Path

from template import RAGASEvaluator, rerank_by_overlap


GOLDEN_PATH = Path("golden_dataset.json")
ACTUAL_PATH = Path("artifacts/actual_answers.json")
OUTPUT_PATH = Path("artifacts/bonus_reranking.json")


def main() -> None:
    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    actual = json.loads(ACTUAL_PATH.read_text(encoding="utf-8"))
    pairs = golden["qa_pairs"]
    answers = actual["answers"]
    if [pair["id"] for pair in pairs] != [answer["id"] for answer in answers]:
        raise ValueError("Golden and actual-answer IDs must match in order")

    evaluator = RAGASEvaluator()
    records: list[dict] = []
    for pair, answer in zip(pairs, answers):
        if pair["question"] != answer["question"]:
            raise ValueError(f"Question mismatch for {pair['id']}")

        chunks = answer["retrieved_contexts"]
        original = [chunk["text"] for chunk in chunks]
        reranked = rerank_by_overlap(original, pair["question"])
        if Counter(reranked) != Counter(original):
            raise ValueError(f"Reranking changed the retrieved set for {pair['id']}")

        # Preserve chunk IDs even if two chunks have identical text.
        ids_by_text: dict[str, deque[str]] = defaultdict(deque)
        for chunk in chunks:
            ids_by_text[chunk["text"]].append(chunk["chunk_id"])
        reranked_ids = [ids_by_text[text].popleft() for text in reranked]

        expected = pair["expected_answer"]
        recall_before = evaluator.evaluate_context_recall(original, expected)
        recall_after = evaluator.evaluate_context_recall(reranked, expected)
        if not math.isclose(recall_before, recall_after, abs_tol=1e-12):
            raise ValueError(f"Context Recall changed for {pair['id']}")

        precision_before = evaluator.evaluate_context_precision(original, expected)
        precision_after = evaluator.evaluate_context_precision(reranked, expected)
        records.append(
            {
                "id": pair["id"],
                "context_recall_before": recall_before,
                "context_recall_after": recall_after,
                "context_precision_before": precision_before,
                "context_precision_after": precision_after,
                "delta_precision": precision_after - precision_before,
                "chunk_ids_before": [chunk["chunk_id"] for chunk in chunks],
                "chunk_ids_after": reranked_ids,
            }
        )

    count = len(records)
    mean = lambda key: sum(row[key] for row in records) / count
    summary = {
        "cases": count,
        "improved": sum(row["delta_precision"] > 1e-12 for row in records),
        "unchanged": sum(abs(row["delta_precision"]) <= 1e-12 for row in records),
        "worsened": sum(row["delta_precision"] < -1e-12 for row in records),
        "avg_context_recall_before": mean("context_recall_before"),
        "avg_context_recall_after": mean("context_recall_after"),
        "avg_context_precision_before": mean("context_precision_before"),
        "avg_context_precision_after": mean("context_precision_after"),
    }
    payload = {
        "method": "stable word-overlap sort using question only",
        "source_actual_generated_at": actual["generated_at"],
        "summary": summary,
        "results": records,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT_PATH}: {summary}")


if __name__ == "__main__":
    main()
