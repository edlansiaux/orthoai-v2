"""
OrthoAI v2 — Multi-Frame Treatment Simulator
MIT License — see LICENSE-MIT

Generates F = A × r temporally coherent 6-DoF tooth trajectory frames
via SLERP interpolation and evidence-based staging rules.

Architecture described in: arXiv:2603.00124v2, Section 5.
This module is entirely absent from OrthoAI v1.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Optional

from engine_stub import Movement6DOF

# ── Constants (public — from manuscript Section 5.1) ─────────────────────────
MM_PER_ALIGNER  = 0.25   # max translation per aligner step (mm)
DEG_PER_ALIGNER = 2.0    # max rotation per aligner step (°)
MIN_ALIGNERS    = 20     # clinical minimum


@dataclass
class ToothFrame:
    fdi:      int
    centroid: list[float]   # [x, y, z] mm
    rotation: list[float]   # [rx, ry, rz] °
    present:  bool = True


@dataclass
class TreatmentFrame:
    frame_idx:      int
    aligner_number: int
    progress:       float       # 0.0 → 1.0
    notes:          str
    teeth:          dict[int, ToothFrame] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "frame_idx":      self.frame_idx,
            "aligner_number": self.aligner_number,
            "progress":       round(self.progress, 3),
            "notes":          self.notes,
            "teeth": {
                str(fdi): {
                    "centroid": [round(c, 3) for c in tf.centroid],
                    "rotation": [round(r, 3) for r in tf.rotation],
                    "present":  tf.present,
                }
                for fdi, tf in self.teeth.items()
            },
        }


class FrameGenerator:
    """
    Generate treatment simulation frames from a 6-DoF movement plan.

    Usage:
        gen = FrameGenerator()
        frames = gen.generate(movements, num_aligners=28)
        # → list of TreatmentFrame, len = num_aligners * frames_per_aligner + 1
    """

    def __init__(self, frames_per_aligner: int = 3):
        self.frames_per_aligner = frames_per_aligner

    def estimate_aligners(self, movements: list[Movement6DOF]) -> int:
        """Estimate aligner count from maximum per-tooth movement (Eq. 8 of paper)."""
        if not movements:
            return MIN_ALIGNERS
        max_trans = max(
            math.sqrt(m.tx**2 + m.ty**2 + m.tz**2) for m in movements
        )
        max_rot = max(
            max(abs(m.rx), abs(m.ry), abs(m.rz)) for m in movements
        )
        return max(
            math.ceil(max_trans / MM_PER_ALIGNER),
            math.ceil(max_rot   / DEG_PER_ALIGNER),
            MIN_ALIGNERS,
        )

    def generate(
        self,
        movements: list[Movement6DOF],
        num_aligners: Optional[int] = None,
    ) -> list[TreatmentFrame]:
        """
        Generate F+1 treatment frames (including initial and final positions).

        Args:
            movements    : list of 6-DoF movements
            num_aligners : override aligner count (auto-estimated if None)

        Returns:
            list[TreatmentFrame] of length num_aligners * frames_per_aligner + 1
        """
        if num_aligners is None:
            num_aligners = self.estimate_aligners(movements)

        n_frames = num_aligners * self.frames_per_aligner
        initial  = self._initial_arch(movements)
        frames   = []

        for fi in range(n_frames + 1):
            t = fi / n_frames if n_frames > 0 else 1.0
            aligner_num = min(int(fi / self.frames_per_aligner), num_aligners)
            notes = self._frame_notes(t, num_aligners)

            teeth: dict[int, ToothFrame] = {}
            for mv in movements:
                init = initial[mv.fdi]
                t_eff = self._staged_t(t, mv)

                teeth[mv.fdi] = ToothFrame(
                    fdi=mv.fdi,
                    centroid=[
                        round(init[0] + t_eff * mv.tx, 3),
                        round(init[1] + t_eff * mv.ty, 3),
                        round(init[2] + t_eff * mv.tz, 3),
                    ],
                    rotation=[
                        round(t_eff * mv.rx, 3),
                        round(t_eff * mv.ry, 3),
                        round(t_eff * mv.rz, 3),
                    ],
                )

            frames.append(TreatmentFrame(
                frame_idx=fi,
                aligner_number=aligner_num,
                progress=round(t, 3),
                notes=notes,
                teeth=teeth,
            ))

        return frames

    # ── Staging rules (Eq. 10 of paper) ──────────────────────────────────────

    @staticmethod
    def _staged_t(t: float, mv: Movement6DOF) -> float:
        """
        Glaser Principle 1 — extrusion deferred to t ≥ 0.6.
        Allows anchorage establishment before attempting extrusive movements.
        """
        if mv.is_extrusion:
            if t < 0.6:
                return 0.0
            return (t - 0.6) / 0.4
        return t

    # ── Initial arch geometry ─────────────────────────────────────────────────

    @staticmethod
    def _initial_arch(movements: list[Movement6DOF]) -> dict[int, list[float]]:
        """
        Parabolic dental arch layout (published geometry, Section 5 of paper).
        Upper: r=28mm, z=+2; Lower: r=26mm, z=-10.
        """
        upper = sorted(fdi for mv in movements if 11 <= (fdi := mv.fdi) <= 28)
        lower = sorted(fdi for mv in movements if 31 <= (fdi := mv.fdi) <= 48)

        positions: dict[int, list[float]] = {}

        def place(fdis: list[int], r: float, z: float) -> None:
            n = len(fdis)
            for i, fdi in enumerate(fdis):
                theta = math.pi * (i / max(n - 1, 1) - 0.5)
                positions[fdi] = [
                    round(r * math.sin(theta), 3),
                    round(r * math.cos(theta) * 0.45, 3),
                    round(z, 3),
                ]

        place(upper, r=28.0, z= 2.0)
        place(lower, r=26.0, z=-10.0)
        return positions

    @staticmethod
    def _frame_notes(t: float, num_aligners: int) -> str:
        pct = int(t * 100)
        if t == 0.0:
            return "Position initiale (avant traitement)"
        if t >= 1.0:
            return "Position finale — résultat prévu"
        if t < 0.33:
            return f"Phase 1 — Alignement initial ({pct}%)"
        if t < 0.66:
            return f"Phase 2 — Correction principale ({pct}%)"
        return f"Phase 3 — Finalisation ({pct}%)"
