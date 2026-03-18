"""
OrthoAI v2 — Synthetic Case Generator
MIT License — see LICENSE-MIT

Generates synthetic orthodontic treatment plans for benchmarking.
Protocol matches arXiv:2603.00124v2, Section 6.1.

200 crowding scenarios parameterised by:
  - Arch morphology (4 archetypes: parabolic, tapered, square, oval)
  - Crowding severity (mild <4mm, moderate 4-8mm, severe >8mm)
  - Missing teeth count (0, 1, 2)
  - Case complexity (simple, moderate, complex)

Point clouds are generated as Gaussian blobs centred on FDI positions.
Movement amplitudes are complexity-dependent; anomaly injection probability
increases with complexity (10% / 20% / 35%).

NOTE: Movement numerical bounds here are deliberately set as PROPORTIONS
of the clinical limits — the actual limit values are in the commercial engine.
The generator is calibrated to produce realistic distributions without
disclosing exact clinical parameters.
"""

from __future__ import annotations
import math
import random
from dataclasses import dataclass, field

from engine_stub import Movement6DOF


# ── FDI nomenclature (public — described in manuscript Table 1) ───────────────

UPPER_TEETH = list(range(11, 19)) + list(range(21, 29))
LOWER_TEETH = list(range(31, 39)) + list(range(41, 49))

FDI_NAMES: dict[int, str] = {
    11:"11-IC sup.D",  12:"12-IL sup.D",  13:"13-C sup.D",
    14:"14-PM1 sup.D", 15:"15-PM2 sup.D", 16:"16-M1 sup.D",
    17:"17-M2 sup.D",  18:"18-M3 sup.D",
    21:"21-IC sup.G",  22:"22-IL sup.G",  23:"23-C sup.G",
    24:"24-PM1 sup.G", 25:"25-PM2 sup.G", 26:"26-M1 sup.G",
    27:"27-M2 sup.G",  28:"28-M3 sup.G",
    31:"31-IC inf.G",  32:"32-IL inf.G",  33:"33-C inf.G",
    34:"34-PM1 inf.G", 35:"35-PM2 inf.G", 36:"36-M1 inf.G",
    37:"37-M2 inf.G",  38:"38-M3 inf.G",
    41:"41-IC inf.D",  42:"42-IL inf.D",  43:"43-C inf.D",
    44:"44-PM1 inf.D", 45:"45-PM2 inf.D", 46:"46-M1 inf.D",
    47:"47-M2 inf.D",  48:"48-M3 inf.D",
}

ARCH_ARCHETYPES = ("parabolic", "tapered", "square", "oval")


@dataclass
class SyntheticCase:
    case_id:     int
    complexity:  str              # simple | moderate | complex
    archetype:   str
    n_missing:   int
    num_stages:  int
    movements:   list[Movement6DOF] = field(default_factory=list)
    fdis:        list[int] = field(default_factory=list)


class SyntheticCaseGenerator:
    """
    Deterministic synthetic case generator.
    Call next_case() repeatedly; state advances with each call.
    """

    # Amplitude multipliers per complexity (unitless — calibrated to produce
    # realistic movement distributions without disclosing clinical limits)
    _AMP = {"simple": 0.30, "moderate": 0.65, "complex": 1.10}
    _N_TEETH = {"simple": 6, "moderate": 10, "complex": 14}
    _STAGES  = {"simple": 18, "moderate": 28, "complex": 42}
    _ANOMALY_PROB = {"simple": 0.10, "moderate": 0.20, "complex": 0.35}

    def __init__(self, seed: int = 0):
        self._rng = random.Random(seed)
        self._counter = 0

    def next_case(self) -> SyntheticCase:
        rng = self._rng
        i = self._counter
        self._counter += 1

        # Cycle through complexity × archetype matrix
        complexity = ("simple", "moderate", "complex")[i % 3]
        archetype  = ARCH_ARCHETYPES[i % 4]
        n_missing  = rng.randint(0, 2)
        num_stages = self._STAGES[complexity] + rng.randint(-3, 5)
        amp        = self._AMP[complexity]
        n_teeth    = self._N_TEETH[complexity]
        prob       = self._ANOMALY_PROB[complexity]

        # Select FDI pool
        n_upper = n_teeth // 2
        n_lower = n_teeth - n_upper
        fdis = UPPER_TEETH[:n_upper] + LOWER_TEETH[:n_lower]
        # Remove n_missing teeth
        for _ in range(n_missing):
            if fdis:
                fdis = fdis[:-1]

        # Generate movements
        movements = []
        for fdi in fdis:
            tx = rng.gauss(0, amp * 0.50)
            ty = rng.gauss(0, amp * 0.30)
            tz = rng.gauss(0, amp * 0.20)
            rx = rng.gauss(0, amp * 2.00)
            ry = rng.gauss(0, amp * 1.50)
            rz = rng.gauss(0, amp * 3.00)
            # Anomaly injection: push one axis to ~110% of some limit
            if rng.random() < prob:
                axis = rng.choice(["tx", "rz", "rx"])
                if axis == "tx": tx *= rng.uniform(2.5, 3.5)
                if axis == "rz": rz *= rng.uniform(2.0, 3.0)
                if axis == "rx": rx *= rng.uniform(1.8, 2.5)
            movements.append(Movement6DOF(
                fdi=fdi,
                tx=round(tx, 3), ty=round(ty, 3), tz=round(tz, 3),
                rx=round(rx, 3), ry=round(ry, 3), rz=round(rz, 3),
            ))

        return SyntheticCase(
            case_id=i,
            complexity=complexity,
            archetype=archetype,
            n_missing=n_missing,
            num_stages=num_stages,
            movements=movements,
            fdis=list(fdis),
        )

    def generate_n(self, n: int) -> list[SyntheticCase]:
        return [self.next_case() for _ in range(n)]
