"""
OrthoAI v2 — Biomechanical Scoring Engine Interface
MIT License (this file) — see LICENSE-MIT
Commercial License (calibrated implementation) — see LICENSE-COMMERCIAL

────────────────────────────────────────────────────────────────────────────────

OPEN-CORE BOUNDARY — READ CAREFULLY

This file defines the PUBLIC INTERFACE that all scoring engines must implement.
Two implementations are available:

  1. StubScorer (included here, MIT)
     Returns plausible random scores for development and UI testing.
     Does NOT implement clinical logic.

  2. OrthalytixScorer (commercial, not in this repository)
     Full calibrated implementation with:
       - Evidence-based movement limits (Glaser 2017, Kravitz 2009)
       - Six-category composite scoring (Eq. 1 of arXiv:2603.00124v2)
       - Severity-graded findings with actionable recommendations
       - Over-engineering correction factor
       - IPR estimation from Bolton analysis
     Available via: pip install orthoai-engine  (requires Orthalytix license)

To swap engines:

    # Development (stub)
    from engine_stub import StubScorer
    scorer = StubScorer()

    # Production (commercial)
    from orthoai_engine import OrthalytixScorer   # pip install orthoai-engine
    scorer = OrthalytixScorer.from_license("YOUR_KEY")

    # Both satisfy the same interface:
    result = scorer.score(movements, num_stages=28)
    print(result.overall, result.grade, result.findings)

────────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import random


# ── Public data types (MIT) ───────────────────────────────────────────────────

@dataclass
class Movement6DOF:
    """Six-degree-of-freedom movement specification for a single tooth."""
    fdi:   int
    tx:    float = 0.0   # mesiodistal translation (mm)
    ty:    float = 0.0   # buccolingual translation (mm)
    tz:    float = 0.0   # vertical: >0 intrusion, <0 extrusion
    rx:    float = 0.0   # torque (°)
    ry:    float = 0.0   # tip (°)
    rz:    float = 0.0   # rotation (°)
    stage_start: int = 0

    @property
    def is_extrusion(self) -> bool:
        return self.tz < 0


@dataclass
class Finding:
    """A single clinical alert."""
    category:       str    # biomechanics | staging | attachments | ipr | occlusion
    severity:       str    # info | warning | critical
    title:          str
    description:    str
    recommendation: str
    tooth_fdi:      Optional[int]   = None
    value:          Optional[float] = None
    limit:          Optional[float] = None


@dataclass
class TreatmentScore:
    """Composite quality score for a treatment plan — v2 format."""
    overall:        float
    grade:          str          # A / B / C / D / F
    biomechanics:   float
    staging:        float
    attachments:    float
    ipr:            float
    occlusion:      float
    predictability: float
    findings:       list[Finding] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "overall":        round(self.overall, 1),
            "grade":          self.grade,
            "biomechanics":   round(self.biomechanics, 1),
            "staging":        round(self.staging, 1),
            "attachments":    round(self.attachments, 1),
            "ipr":            round(self.ipr, 1),
            "occlusion":      round(self.occlusion, 1),
            "predictability": round(self.predictability, 1),
            "findings": [
                {
                    "category":       f.category,
                    "severity":       f.severity,
                    "title":          f.title,
                    "description":    f.description,
                    "recommendation": f.recommendation,
                    "tooth_fdi":      f.tooth_fdi,
                    "value":          f.value,
                    "limit":          f.limit,
                }
                for f in self.findings
            ],
        }


# ── Abstract scorer interface (MIT) ──────────────────────────────────────────

class AbstractScorer(ABC):
    """
    Public interface for biomechanical scoring engines.

    Concrete implementations:
      StubScorer        — this file, development only
      OrthalytixScorer  — commercial, pip install orthoai-engine
    """

    @abstractmethod
    def score(
        self,
        movements: list[Movement6DOF],
        num_stages: int = 28,
        apply_overengineering: bool = True,
    ) -> TreatmentScore:
        """
        Evaluate a treatment plan and return a composite quality score.

        Args:
            movements             : List of 6-DoF tooth movements
            num_stages            : Planned number of aligner stages
            apply_overengineering : Multiply movements by correction factor
                                    before evaluation (Glaser Principle 4)
        Returns:
            TreatmentScore with overall (0–100), grade (A–F), 6 sub-scores,
            and a list of clinical findings.
        """
        ...

    @abstractmethod
    def per_tooth_info(self, mv: Movement6DOF) -> dict:
        """
        Return per-tooth metadata: needs_attachment, needs_ipr, predictability_pct.
        Used by the API to annotate the movements table in the frontend.
        """
        ...


# ── Stub implementation (MIT, development only) ───────────────────────────────

class StubScorer(AbstractScorer):
    """
    Development stub — returns plausible but NOT clinically valid scores.

    Use this during:
      - Frontend development and UI testing
      - CI/CD pipeline smoke tests
      - Demo deployments without a commercial license

    DO NOT use in clinical or research contexts.
    The numerical outputs are random and have no clinical meaning.
    """

    _STUB_WARNING = (
        "[StubScorer] WARNING: scores are non-clinical random values. "
        "For research/production use, install orthoai-engine."
    )

    def __init__(self, seed: int = 42, warn: bool = True):
        self._rng = random.Random(seed)
        if warn:
            import warnings
            warnings.warn(self._STUB_WARNING, stacklevel=2)

    def score(
        self,
        movements: list[Movement6DOF],
        num_stages: int = 28,
        apply_overengineering: bool = True,
    ) -> TreatmentScore:
        rng = self._rng
        overall = rng.uniform(72, 95)
        grade = "A" if overall >= 90 else "B" if overall >= 75 else "C"
        return TreatmentScore(
            overall=round(overall, 1),
            grade=grade,
            biomechanics=round(rng.uniform(70, 98), 1),
            staging=round(rng.uniform(68, 96), 1),
            attachments=round(rng.uniform(75, 100), 1),
            ipr=round(rng.uniform(80, 100), 1),
            occlusion=round(rng.uniform(70, 95), 1),
            predictability=round(rng.uniform(65, 90), 1),
            findings=[
                Finding(
                    category="biomechanics",
                    severity="info",
                    title="StubScorer — scores non cliniques",
                    description="Ce scorer est un stub de développement. "
                                "Installez orthoai-engine pour des scores calibrés.",
                    recommendation="pip install orthoai-engine  # requires Orthalytix license",
                )
            ],
        )

    def per_tooth_info(self, mv: Movement6DOF) -> dict:
        rng = self._rng
        return {
            "needs_attachment": abs(mv.rz) > 10 or mv.is_extrusion,
            "needs_ipr":        abs(mv.tx) > 2.0,
            "predictability":   round(rng.uniform(55, 95), 1),
            "magnitude":        round((mv.tx**2 + mv.ty**2 + mv.tz**2) ** 0.5, 3),
        }


# ── Engine loader helper ──────────────────────────────────────────────────────

def load_scorer(license_key: str | None = None) -> AbstractScorer:
    """
    Load the best available scorer:
      - If orthoai-engine is installed and license_key provided → OrthalytixScorer
      - Otherwise → StubScorer with warning

    Usage:
        scorer = load_scorer(os.environ.get("ORTHOAI_LICENSE_KEY"))
    """
    if license_key:
        try:
            from orthoai_engine import OrthalytixScorer   # type: ignore[import]
            return OrthalytixScorer.from_license(license_key)
        except ImportError:
            import warnings
            warnings.warn(
                "orthoai-engine not installed. Falling back to StubScorer.\n"
                "Install: pip install orthoai-engine  (requires Orthalytix license)",
                stacklevel=2,
            )
    return StubScorer(warn=license_key is None)
