"""
OrthoAI v2 — Preset Clinical Archetypes
MIT License — see LICENSE-MIT

Four preset cases covering the primary clinical archetypes encountered
in an Invisalign caseload. Movement values are illustrative and match
the demo scenarios described in arXiv:2603.00124v2, Section 7.

These cases are used by the SaaS frontend for instant demo without
requiring model inference.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from engine_stub import Movement6DOF


@dataclass
class PresetCase:
    patient_id:   str
    patient_name: str
    case_type:    str
    description:  str
    num_stages:   int
    complexity:   str
    arch:         str
    movements:    list[Movement6DOF] = field(default_factory=list)

    @property
    def fdis(self) -> list[int]:
        return [m.fdi for m in self.movements]

    @property
    def duration_months(self) -> int:
        return round(self.num_stages * 14 / 30)


# ── Case 1: Class I moderate crowding ────────────────────────────────────────

def _case_crowding() -> list[Movement6DOF]:
    return [
        Movement6DOF(fdi=11, tx= 0.5, ty= 0.0, rz= 3.0, rx= 0.8),
        Movement6DOF(fdi=12, tx= 1.2, ty= 0.3, rz= 5.0, rx= 0.5),
        Movement6DOF(fdi=13, tx= 0.8, ty= 0.5, rz= 2.0, rx= 0.3),
        Movement6DOF(fdi=21, tx=-0.5, ty= 0.0, rz=-3.0, rx= 0.8),
        Movement6DOF(fdi=22, tx=-1.2, ty= 0.3, rz=-5.0, rx= 0.5),
        Movement6DOF(fdi=23, tx=-0.8, ty= 0.5, rz=-2.0, rx= 0.3),
        Movement6DOF(fdi=41, tx= 0.4, ty= 0.0, rz= 2.5, rx= 0.4),
        Movement6DOF(fdi=42, tx= 0.9, ty= 0.2, rz= 4.0, rx= 0.3),
        Movement6DOF(fdi=43, tx= 0.6, ty= 0.4, rz= 1.5, rx= 0.2),
        Movement6DOF(fdi=31, tx=-0.4, ty= 0.0, rz=-2.5, rx= 0.4),
        Movement6DOF(fdi=32, tx=-0.9, ty= 0.2, rz=-4.0, rx= 0.3),
        Movement6DOF(fdi=33, tx=-0.6, ty= 0.4, rz=-1.5, rx= 0.2),
    ]


# ── Case 2: Anterior open bite ────────────────────────────────────────────────

def _case_open_bite() -> list[Movement6DOF]:
    return [
        # Intrude upper incisors
        Movement6DOF(fdi=11, tz= 1.8, tx= 0.2, rz= 1.5, rx= 2.5),
        Movement6DOF(fdi=12, tz= 1.6, tx= 0.1, rz= 2.0, rx= 2.0),
        Movement6DOF(fdi=13, tz= 1.4, tx= 0.0, rz= 1.0, rx= 1.5),
        Movement6DOF(fdi=21, tz= 1.8, tx=-0.2, rz=-1.5, rx= 2.5),
        Movement6DOF(fdi=22, tz= 1.6, tx=-0.1, rz=-2.0, rx= 2.0),
        Movement6DOF(fdi=23, tz= 1.4, tx= 0.0, rz=-1.0, rx= 1.5),
        # Intrude lower incisors
        Movement6DOF(fdi=41, tz= 1.5, tx= 0.1, rz= 1.0),
        Movement6DOF(fdi=42, tz= 1.3, tx= 0.1, rz= 1.5),
        Movement6DOF(fdi=43, tz= 1.2, tx= 0.0, rz= 0.8),
        Movement6DOF(fdi=31, tz= 1.5, tx=-0.1, rz=-1.0),
        Movement6DOF(fdi=32, tz= 1.3, tx=-0.1, rz=-1.5),
        Movement6DOF(fdi=33, tz= 1.2, tx= 0.0, rz=-0.8),
        # Upper premolars — buccal torque
        Movement6DOF(fdi=14, rx= 4.0, ty= 0.5, tz=-0.3),
        Movement6DOF(fdi=15, rx= 4.0, ty= 0.5, tz=-0.3),
        Movement6DOF(fdi=24, rx= 4.0, ty= 0.5, tz=-0.3),
        Movement6DOF(fdi=25, rx= 4.0, ty= 0.5, tz=-0.3),
        # Upper molars — mild extrusion + rotation
        Movement6DOF(fdi=16, tx= 1.2, tz=-0.5, rx= 3.0, ry= 2.0),
        Movement6DOF(fdi=26, tx=-1.2, tz=-0.5, rx= 3.0, ry=-2.0),
    ]


# ── Case 3: Maxillary diastema ────────────────────────────────────────────────

def _case_diastema() -> list[Movement6DOF]:
    return [
        Movement6DOF(fdi=11, tx=-1.5, rx= 2.0, rz= 1.5),
        Movement6DOF(fdi=21, tx= 1.5, rx= 2.0, rz=-1.5),
        Movement6DOF(fdi=12, tx=-0.5, rz= 2.0),
        Movement6DOF(fdi=22, tx= 0.5, rz=-2.0),
        Movement6DOF(fdi=13, tx=-0.3, rz= 1.0),
        Movement6DOF(fdi=23, tx= 0.3, rz=-1.0),
    ]


# ── Case 4: Class II division 1 ───────────────────────────────────────────────

def _case_class2() -> list[Movement6DOF]:
    return [
        # Upper posterior — distalisation
        Movement6DOF(fdi=16, tx=-2.2, rx=-2.5, ry= 2.0, rz= 4.0),
        Movement6DOF(fdi=17, tx=-1.8, rx=-2.0, ry= 1.5, rz= 3.0),
        Movement6DOF(fdi=26, tx= 2.2, rx=-2.5, ry=-2.0, rz=-4.0),
        Movement6DOF(fdi=27, tx= 1.8, rx=-2.0, ry=-1.5, rz=-3.0),
        Movement6DOF(fdi=14, tx=-1.0, rx=-1.5, ry= 1.0),
        Movement6DOF(fdi=15, tx=-0.8, rx=-1.5, ry= 0.8),
        Movement6DOF(fdi=24, tx= 1.0, rx=-1.5, ry=-1.0),
        Movement6DOF(fdi=25, tx= 0.8, rx=-1.5, ry=-0.8),
        # Upper anteriors — retraction
        Movement6DOF(fdi=11, tx=-2.5, rx= 4.0, rz= 2.5),
        Movement6DOF(fdi=12, tx=-1.8, rx= 3.0, rz= 2.0),
        Movement6DOF(fdi=13, tx=-1.2, rx= 2.0, rz= 1.5),
        Movement6DOF(fdi=21, tx= 2.5, rx= 4.0, rz=-2.5),
        Movement6DOF(fdi=22, tx= 1.8, rx= 3.0, rz=-2.0),
        Movement6DOF(fdi=23, tx= 1.2, rx= 2.0, rz=-1.5),
        # Lower anteriors — protrusion
        Movement6DOF(fdi=41, tx= 0.8, rz= 2.0),
        Movement6DOF(fdi=42, tx= 0.5, rz= 1.5),
        Movement6DOF(fdi=43, tx= 0.3, rz= 1.0),
        Movement6DOF(fdi=31, tx=-0.8, rz=-2.0),
        Movement6DOF(fdi=32, tx=-0.5, rz=-1.5),
        Movement6DOF(fdi=33, tx=-0.3, rz=-1.0),
    ]


# ── Registry ──────────────────────────────────────────────────────────────────

PRESETS: list[PresetCase] = [
    PresetCase(
        patient_id="patient_001",
        patient_name="Sophie M.",
        case_type="Encombrement modéré CI",
        description="Classe I, encombrement antérieur ±5 mm, traitement bimax. "
                    "Cas pédagogique — excellent pour première démonstration.",
        num_stages=28, complexity="moderate", arch="both",
        movements=_case_crowding(),
    ),
    PresetCase(
        patient_id="patient_002",
        patient_name="Thomas B.",
        case_type="Béance antérieure",
        description="Béance 4 mm, intrusion incisive + torque prémolaires. "
                    "Cas complexe avec gestion d'ancrage vertical.",
        num_stages=42, complexity="complex", arch="both",
        movements=_case_open_bite(),
    ),
    PresetCase(
        patient_id="patient_003",
        patient_name="Emma L.",
        case_type="Diastème maxillaire",
        description="Diastème central 2.5 mm, fermeture par translation mésiale. "
                    "Cas simple, excellent pronostic prédictable.",
        num_stages=18, complexity="simple", arch="upper",
        movements=_case_diastema(),
    ),
    PresetCase(
        patient_id="patient_004",
        patient_name="Lucas D.",
        case_type="Classe II div. 1",
        description="Classe II squelettique légère, distalisation maxillaire "
                    "+ expansion mandibulaire. Cas complexe, plan long.",
        num_stages=48, complexity="complex", arch="both",
        movements=_case_class2(),
    ),
]

PRESETS_BY_ID: dict[str, PresetCase] = {p.patient_id: p for p in PRESETS}


def get_preset(patient_id: str) -> PresetCase | None:
    return PRESETS_BY_ID.get(patient_id)


def list_presets() -> list[dict]:
    return [
        {
            "patient_id":    p.patient_id,
            "patient_name":  p.patient_name,
            "case_type":     p.case_type,
            "description":   p.description,
            "num_stages":    p.num_stages,
            "complexity":    p.complexity,
            "arch":          p.arch,
            "n_teeth":       len(p.movements),
            "duration_months": p.duration_months,
        }
        for p in PRESETS
    ]
