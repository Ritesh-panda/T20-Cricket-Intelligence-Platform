"""Evaluation and Benchmarking Module for Cricket NLP Pipeline.

Measures and computes:
1. Entity mention detection precision, recall, and F1 score against labelled ground truth.
2. Entity resolution accuracy, ambiguity rate, and coverage.
3. Sentiment baseline classification metrics (Precision, Recall, Macro-F1).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ClassificationMetrics:
    """Standard precision, recall, and F1 metrics container."""
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    support: int = 0


@dataclass
class NEREvaluationResult:
    """Quantitative evaluation results for Named Entity Recognition."""
    total_ground_truth: int = 0
    total_predicted: int = 0
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    overall: ClassificationMetrics = field(default_factory=ClassificationMetrics)
    per_type: Dict[str, ClassificationMetrics] = field(default_factory=dict)


@dataclass
class ResolutionEvaluationResult:
    """Quantitative evaluation for entity resolution decisions."""
    total_mentions: int = 0
    correctly_resolved: int = 0
    ambiguous_count: int = 0
    unresolved_count: int = 0
    wrongly_resolved: int = 0
    accuracy: float = 0.0
    ambiguity_rate: float = 0.0
    resolution_coverage: float = 0.0


@dataclass
class SentimentEvaluationResult:
    """Quantitative evaluation for sentiment baselines."""
    total_samples: int = 0
    accuracy: float = 0.0
    macro_f1: float = 0.0
    per_class: Dict[str, ClassificationMetrics] = field(default_factory=dict)


def compute_ner_metrics(
    ground_truth: List[Dict[str, Any]],
    predicted: List[Dict[str, Any]],
) -> NEREvaluationResult:
    """
    Computes span-exact and entity-type matched precision, recall, and F1.
    Each item expects: {'surface': str, 'type': str, 'start': int, 'end': int}
    """
    gt_spans = {(g["start"], g["end"], g["type"], g["surface"].lower()) for g in ground_truth}
    pred_spans = {(p["start"], p["end"], p["type"], p["surface"].lower()) for p in predicted}

    tp_set = gt_spans.intersection(pred_spans)
    fp_set = pred_spans - gt_spans
    fn_set = gt_spans - pred_spans

    tp = len(tp_set)
    fp = len(fp_set)
    fn = len(fn_set)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    result = NEREvaluationResult(
        total_ground_truth=len(gt_spans),
        total_predicted=len(pred_spans),
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        overall=ClassificationMetrics(
            precision=round(precision, 3),
            recall=round(recall, 3),
            f1_score=round(f1, 3),
            support=len(gt_spans),
        ),
    )

    # Per-type breakdown
    all_types = {g["type"] for g in ground_truth}.union({p["type"] for p in predicted})
    for et in sorted(all_types):
        gt_t = {s for s in gt_spans if s[2] == et}
        pr_t = {s for s in pred_spans if s[2] == et}
        tp_t = len(gt_t.intersection(pr_t))
        fp_t = len(pr_t - gt_t)
        fn_t = len(gt_t - pr_t)

        p_t = tp_t / (tp_t + fp_t) if (tp_t + fp_t) > 0 else 0.0
        r_t = tp_t / (tp_t + fn_t) if (tp_t + fn_t) > 0 else 0.0
        f_t = (2 * p_t * r_t) / (p_t + r_t) if (p_t + r_t) > 0 else 0.0

        result.per_type[et] = ClassificationMetrics(
            precision=round(p_t, 3),
            recall=round(r_t, 3),
            f1_score=round(f_t, 3),
            support=len(gt_t),
        )

    return result


def compute_resolution_metrics(
    ground_truth: List[Dict[str, Any]],
    predicted: List[Dict[str, Any]],
) -> ResolutionEvaluationResult:
    """
    Evaluates resolution accuracy and ambiguity handling.
    Each item expects: {'surface': str, 'expected_id': str, 'expected_status': str}
    and predicted: {'surface': str, 'resolved_id': Optional[str], 'status': str}
    """
    total = len(ground_truth)
    if total == 0:
        return ResolutionEvaluationResult()

    correct = 0
    ambiguous = 0
    unresolved = 0
    wrong = 0

    for gt, pr in zip(ground_truth, predicted):
        p_status = pr.get("status")
        p_id = pr.get("resolved_id")
        exp_id = gt.get("expected_id")
        exp_status = gt.get("expected_status")

        if p_status == "AMBIGUOUS":
            ambiguous += 1
            if exp_status == "AMBIGUOUS":
                correct += 1
        elif p_status == "UNRESOLVED":
            unresolved += 1
            if exp_status == "UNRESOLVED":
                correct += 1
        elif p_status == "RESOLVED":
            if p_id == exp_id:
                correct += 1
            else:
                wrong += 1

    accuracy = correct / total
    ambiguity_rate = ambiguous / total
    coverage = (total - unresolved) / total

    return ResolutionEvaluationResult(
        total_mentions=total,
        correctly_resolved=correct,
        ambiguous_count=ambiguous,
        unresolved_count=unresolved,
        wrongly_resolved=wrong,
        accuracy=round(accuracy, 3),
        ambiguity_rate=round(ambiguity_rate, 3),
        resolution_coverage=round(coverage, 3),
    )


def compute_sentiment_metrics(
    ground_truth_labels: List[str],
    predicted_labels: List[str],
) -> SentimentEvaluationResult:
    """Computes multiclass precision, recall, and macro-F1 for sentiment labels."""
    total = len(ground_truth_labels)
    if total == 0:
        return SentimentEvaluationResult()

    classes = ["POSITIVE", "NEUTRAL", "NEGATIVE"]
    per_class = {}
    f1_sum = 0.0

    for cls in classes:
        tp = sum(1 for gt, pr in zip(ground_truth_labels, predicted_labels) if gt == cls and pr == cls)
        fp = sum(1 for gt, pr in zip(ground_truth_labels, predicted_labels) if gt != cls and pr == cls)
        fn = sum(1 for gt, pr in zip(ground_truth_labels, predicted_labels) if gt == cls and pr != cls)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        f1_sum += f1

        per_class[cls] = ClassificationMetrics(
            precision=round(prec, 3),
            recall=round(rec, 3),
            f1_score=round(f1, 3),
            support=sum(1 for gt in ground_truth_labels if gt == cls),
        )

    accuracy = sum(1 for gt, pr in zip(ground_truth_labels, predicted_labels) if gt == pr) / total
    macro_f1 = f1_sum / len(classes)

    return SentimentEvaluationResult(
        total_samples=total,
        accuracy=round(accuracy, 3),
        macro_f1=round(macro_f1, 3),
        per_class=per_class,
    )
