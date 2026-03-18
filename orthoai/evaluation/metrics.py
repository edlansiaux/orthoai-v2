"""
OrthoAI v2 — Evaluation Metrics
MIT License — see LICENSE-MIT

Public evaluation protocol matching arXiv:2603.00124v2, Section 6.
Reproduces the MEDE, MSR, planning quality, and feasibility metrics
used in Tables 2–4 of the paper.
"""

from __future__ import annotations
import math
from typing import Optional


# ── Landmark metrics ──────────────────────────────────────────────────────────

def mede(
    pred_landmarks: list[list[float]],
    gt_landmarks:   list[list[float]],
    presence_mask:  Optional[list[bool]] = None,
) -> float:
    """
    Mean Euclidean Distance Error (MEDE) in mm.

    Only considers landmarks where the tooth is present (presence_mask=True).
    Matches metric definition in CHaRNet (arXiv:2501.13073v5) and Table 3
    of arXiv:2603.00124v2.

    Args:
        pred_landmarks : (K, 3) predicted landmark coordinates
        gt_landmarks   : (K, 3) ground-truth landmark coordinates
        presence_mask  : (K,)   True if landmark should be evaluated

    Returns:
        Mean Euclidean distance in mm (lower is better).
    """
    if presence_mask is None:
        presence_mask = [True] * len(pred_landmarks)

    errors = []
    for pred, gt, present in zip(pred_landmarks, gt_landmarks, presence_mask):
        if not present:
            continue
        dist = math.sqrt(sum((p - g) ** 2 for p, g in zip(pred, gt)))
        errors.append(dist)

    return sum(errors) / len(errors) if errors else 0.0


def msr(
    pred_landmarks: list[list[float]],
    gt_landmarks:   list[list[float]],
    threshold_mm:   float = 2.0,
    presence_mask:  Optional[list[bool]] = None,
) -> float:
    """
    Mean Success Rate (MSR) — fraction of landmarks within `threshold_mm` of GT.

    Matches metric definition in CHaRNet and Table 3 of arXiv:2603.00124v2.

    Returns:
        MSR ∈ [0, 1] (higher is better).
    """
    if presence_mask is None:
        presence_mask = [True] * len(pred_landmarks)

    successes, total = 0, 0
    for pred, gt, present in zip(pred_landmarks, gt_landmarks, presence_mask):
        if not present:
            continue
        dist = math.sqrt(sum((p - g) ** 2 for p, g in zip(pred, gt)))
        successes += int(dist <= threshold_mm)
        total += 1

    return successes / total if total else 0.0


# ── Planning quality metrics ──────────────────────────────────────────────────

def planning_quality_v1(
    movements: list,
    movement_limits: dict,
) -> float:
    """
    OrthoAI v1 scalar quality score (reproduced for comparison).
    Q_v1 = 100 × mean_j mean_ℓ max(0, 1 − |m_jℓ| / L_ℓ)

    Note: this formula is published in arXiv:2603.00124 and is MIT-licensed.
    The movement_limits dict must be supplied by the caller.

    Args:
        movements       : list of movement objects with .fdi, .tx, .ty, .tz, .rx, .ry, .rz
        movement_limits : dict[tooth_type_str][axis_str] → (max_value, pred_label)

    Returns:
        Scalar quality score ∈ [0, 100].
    """
    import math

    def tooth_type(fdi: int) -> str:
        n = fdi % 10
        if n <= 2: return "incisor"
        if n == 3: return "canine"
        if n <= 5: return "premolar"
        return "molar"

    all_scores = []
    for mv in movements:
        tt = tooth_type(mv.fdi)
        lim = movement_limits.get(tt, {})
        axes = [
            ("translation_md", abs(mv.tx)),
            ("translation_bl", abs(mv.ty)),
            ("rotation",       abs(mv.rz)),
            ("torque",         abs(mv.rx)),
            ("tip",            abs(mv.ry)),
        ]
        if mv.tz >= 0:
            axes.append(("intrusion", mv.tz))
        else:
            axes.append(("extrusion", abs(mv.tz)))
        for key, val in axes:
            if key in lim:
                max_v = lim[key][0]
                all_scores.append(max(0.0, 1.0 - val / max_v))
            else:
                all_scores.append(1.0)

    return round(100.0 * sum(all_scores) / len(all_scores), 1) if all_scores else 100.0


def is_feasible(score: float, threshold: float = 70.0) -> bool:
    """
    Binary feasibility check: plan is feasible if quality score ≥ threshold.
    Threshold=70 matches the benchmark definition in arXiv:2603.00124v2.
    """
    return score >= threshold


# ── Benchmark summary ─────────────────────────────────────────────────────────

def summarise_results(results: list[dict]) -> dict:
    """
    Compute mean ± std and feasibility rate from a list of case results.

    Each result dict must contain:
      - "quality"  : float
      - "latency_s": float

    Returns summary matching Table 2 format in the paper.
    """
    import statistics

    qualities  = [r["quality"]   for r in results]
    latencies  = [r["latency_s"] for r in results]
    feasible   = [r["quality"]   for r in results if is_feasible(r["quality"])]

    return {
        "n_cases":        len(results),
        "quality_mean":   round(statistics.mean(qualities), 1),
        "quality_std":    round(statistics.stdev(qualities) if len(qualities) > 1 else 0.0, 1),
        "feasibility_pct": round(100.0 * len(feasible) / len(results), 1),
        "latency_mean_s": round(statistics.mean(latencies), 2),
        "latency_std_s":  round(statistics.stdev(latencies) if len(latencies) > 1 else 0.0, 2),
    }
