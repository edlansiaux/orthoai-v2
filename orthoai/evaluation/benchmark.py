"""
OrthoAI v2 — Synthetic Benchmark Harness
MIT License — see LICENSE-MIT

Reproduces the 200-case evaluation protocol of arXiv:2603.00124v2, Section 6.1.
Results are deterministic given the same seed.

Usage:
    python scripts/evaluate.py --n_cases 200 --mode parallel --seed 0

Note: quality scores will differ between the stub engine (random) and the
commercial engine (calibrated). The benchmark protocol and data generation
are MIT-licensed and fully reproducible; only the scoring calibration is
proprietary.
"""

from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Callable

from orthoai.demo.synthetic import SyntheticCaseGenerator
from orthoai.evaluation.metrics import summarise_results, is_feasible


@dataclass
class BenchmarkConfig:
    n_cases:     int   = 200
    seed:        int   = 0
    mode:        str   = "parallel"   # parallel | sequential | single
    verbose:     bool  = True


def run_benchmark(
    scorer_fn: Callable,          # callable(movements, num_stages) → TreatmentScore
    config: BenchmarkConfig = BenchmarkConfig(),
) -> dict:
    """
    Run the OrthoAI v2 synthetic benchmark.

    Args:
        scorer_fn : A callable matching AbstractScorer.score() signature.
                    Can be StubScorer().score or OrthalytixScorer(...).score.
        config    : BenchmarkConfig

    Returns:
        Summary dict with quality_mean, quality_std, feasibility_pct, latency stats.
    """
    gen = SyntheticCaseGenerator(seed=config.seed)
    results = []

    for i in range(config.n_cases):
        case = gen.next_case()
        t0 = time.perf_counter()
        score = scorer_fn(case.movements, num_stages=case.num_stages)
        latency = time.perf_counter() - t0

        results.append({
            "case_id":    i,
            "complexity": case.complexity,
            "quality":    score.overall,
            "grade":      score.grade,
            "latency_s":  latency,
        })

        if config.verbose and (i + 1) % 50 == 0:
            partial = summarise_results(results)
            print(f"  [{i+1:3d}/{config.n_cases}] "
                  f"Q={partial['quality_mean']:.1f}±{partial['quality_std']:.1f} "
                  f"Feas={partial['feasibility_pct']:.0f}%")

    summary = summarise_results(results)
    if config.verbose:
        print(f"\n── Benchmark results ({config.n_cases} cases, mode={config.mode}) ──")
        print(f"  Quality : {summary['quality_mean']:.1f} ± {summary['quality_std']:.1f}")
        print(f"  Grade A/B: {sum(1 for r in results if r['grade'] in ('A','B'))} / {config.n_cases}")
        print(f"  Feasible : {summary['feasibility_pct']:.0f}%")
        print(f"  Latency  : {summary['latency_mean_s']:.3f}s ± {summary['latency_std_s']:.3f}s")

    summary["per_complexity"] = {
        c: summarise_results([r for r in results if r["complexity"] == c])
        for c in ("simple", "moderate", "complex")
    }
    return summary
