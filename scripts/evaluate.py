#!/usr/bin/env python3
"""
OrthoAI v2 — Benchmark Runner
MIT License — see LICENSE-MIT

Reproduces the 200-case synthetic benchmark from arXiv:2603.00124v2, Section 6.

Usage:
    # With stub engine (non-clinical scores)
    python scripts/evaluate.py

    # With commercial engine
    ORTHOAI_LICENSE_KEY=your-key python scripts/evaluate.py --n_cases 200

    # Save results to JSON
    python scripts/evaluate.py --output results/v2_benchmark.json
"""

import argparse
import json
import os
import sys
import warnings

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine_stub import load_scorer
from orthoai.evaluation.benchmark import BenchmarkConfig, run_benchmark


def main():
    parser = argparse.ArgumentParser(description="OrthoAI v2 benchmark runner")
    parser.add_argument("--n_cases", type=int, default=200)
    parser.add_argument("--seed",    type=int, default=0)
    parser.add_argument("--mode",    choices=["parallel","sequential","single"],
                        default="parallel")
    parser.add_argument("--output",  type=str, default=None,
                        help="Save JSON results to this path")
    parser.add_argument("--quiet",   action="store_true")
    args = parser.parse_args()

    license_key = os.environ.get("ORTHOAI_LICENSE_KEY")
    if not license_key:
        warnings.warn(
            "\nNo ORTHOAI_LICENSE_KEY found — using StubScorer.\n"
            "Scores are NOT clinically valid.\n"
            "Set ORTHOAI_LICENSE_KEY to use the calibrated commercial engine.\n",
            stacklevel=1,
        )

    scorer = load_scorer(license_key)

    config = BenchmarkConfig(
        n_cases=args.n_cases,
        seed=args.seed,
        mode=args.mode,
        verbose=not args.quiet,
    )

    print(f"\nOrthoAI v2 Benchmark — {args.n_cases} cases, mode={args.mode}")
    print(f"Engine: {type(scorer).__name__}")
    print("─" * 55)

    results = run_benchmark(scorer.score, config)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")

    return results


if __name__ == "__main__":
    main()
