"""
OrthoAI v2 — FastAPI Application
MIT License — see LICENSE-MIT

REST API exposing the OrthoAI v2 pipeline for browser and CLI clients.
The scoring engine is loaded via load_scorer() — transparent stub/commercial swap.

Set ORTHOAI_LICENSE_KEY in environment to use the commercial engine.
Without a license key, the StubScorer is used with a runtime warning.
"""

from __future__ import annotations
import os
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from engine_stub import load_scorer, Movement6DOF, AbstractScorer
from orthoai.demo.presets import list_presets, get_preset, PresetCase
from orthoai.demo.synthetic import SyntheticCaseGenerator
from orthoai.demo.frame_generator import FrameGenerator

# ── App lifecycle ─────────────────────────────────────────────────────────────

scorer: AbstractScorer
frame_gen: FrameGenerator
synth_gen: SyntheticCaseGenerator


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scorer, frame_gen, synth_gen
    scorer    = load_scorer(os.environ.get("ORTHOAI_LICENSE_KEY"))
    frame_gen = FrameGenerator(frames_per_aligner=3)
    synth_gen = SyntheticCaseGenerator(seed=0)
    yield


app = FastAPI(
    title="OrthoAI v2",
    description=(
        "AI-assisted orthodontic treatment planning API. "
        "Open-core: architecture MIT, engine commercial. "
        "arXiv:2603.00124v2 — Lansiaux E., STaR-AI / CHU de Lille."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pydantic schemas ──────────────────────────────────────────────────────────

class Movement6DOFSchema(BaseModel):
    fdi:   int   = Field(..., ge=11, le=48, description="FDI tooth number")
    tx:    float = Field(0.0, description="Mesiodistal translation (mm)")
    ty:    float = Field(0.0, description="Buccolingual translation (mm)")
    tz:    float = Field(0.0, description="Vertical: >0 intrusion, <0 extrusion (mm)")
    rx:    float = Field(0.0, description="Torque (°)")
    ry:    float = Field(0.0, description="Tip (°)")
    rz:    float = Field(0.0, description="Rotation (°)")
    stage_start: int = Field(0, description="Aligner step at which movement begins")


class AnalyzeRequest(BaseModel):
    movements:             list[Movement6DOFSchema]
    num_stages:            int  = Field(28, ge=1, le=120)
    apply_overengineering: bool = Field(True)
    generate_frames:       bool = Field(True)
    patient_name:          Optional[str] = None


# ── Internal helpers ──────────────────────────────────────────────────────────

def _movement_schema_to_domain(m: Movement6DOFSchema) -> Movement6DOF:
    return Movement6DOF(
        fdi=m.fdi, tx=m.tx, ty=m.ty, tz=m.tz,
        rx=m.rx, ry=m.ry, rz=m.rz, stage_start=m.stage_start,
    )


def _build_response(
    case: "PresetCase | None",
    movements: list[Movement6DOF],
    num_stages: int,
    patient_id: str = "custom",
    patient_name: str = "Patient",
    case_type: str = "Custom",
    description: str = "",
    generate_frames: bool = True,
) -> dict:
    t0 = time.perf_counter()
    score = scorer.score(movements, num_stages=num_stages)
    elapsed = time.perf_counter() - t0

    # Per-tooth annotations
    movements_out = []
    for mv in movements:
        info = scorer.per_tooth_info(mv)
        movements_out.append({
            "fdi":              mv.fdi,
            "name":             _fdi_name(mv.fdi),
            "tx":               mv.tx, "ty": mv.ty, "tz": mv.tz,
            "rx":               mv.rx, "ry": mv.ry, "rz": mv.rz,
            "magnitude":        info.get("magnitude", 0.0),
            "needs_attachment": info.get("needs_attachment", False),
            "needs_ipr":        info.get("needs_ipr", False),
            "predictability":   info.get("predictability", 75.0),
            "is_extrusion":     mv.is_extrusion,
            "stage_start":      mv.stage_start,
        })

    # Frame generation
    frames_out = []
    if generate_frames:
        frames = frame_gen.generate(movements, num_aligners=num_stages)
        frames_out = [f.to_dict() for f in frames]

    n_crit = sum(1 for f in score.findings if f["severity"] == "critical")
    n_warn = sum(1 for f in score.findings if f["severity"] == "warning")

    return {
        "patient_id":   patient_id,
        "patient_name": patient_name,
        "case_type":    case_type,
        "description":  description,
        "num_stages":   num_stages,
        "duration_months": round(num_stages * 14 / 30),
        "score":        score.to_dict(),
        "movements":    movements_out,
        "frames":       frames_out,
        "metadata": {
            "processing_time_s": round(elapsed, 3),
            "n_movements":       len(movements),
            "n_frames":          len(frames_out),
            "n_critical":        n_crit,
            "n_warnings":        n_warn,
            "engine":            type(scorer).__name__,
            "orthoai_version":   "2.0.0",
        },
    }


def _fdi_name(fdi: int) -> str:
    names = {
        11:"11-IC sup.D",12:"12-IL sup.D",13:"13-C sup.D",
        14:"14-PM1 sup.D",15:"15-PM2 sup.D",16:"16-M1 sup.D",
        17:"17-M2 sup.D",18:"18-M3 sup.D",
        21:"21-IC sup.G",22:"22-IL sup.G",23:"23-C sup.G",
        24:"24-PM1 sup.G",25:"25-PM2 sup.G",26:"26-M1 sup.G",
        27:"27-M2 sup.G",28:"28-M3 sup.G",
        31:"31-IC inf.G",32:"32-IL inf.G",33:"33-C inf.G",
        34:"34-PM1 inf.G",35:"35-PM2 inf.G",36:"36-M1 inf.G",
        37:"37-M2 inf.G",38:"38-M3 inf.G",
        41:"41-IC inf.D",42:"42-IL inf.D",43:"43-C inf.D",
        44:"44-PM1 inf.D",45:"45-PM2 inf.D",46:"46-M1 inf.D",
        47:"47-M2 inf.D",48:"48-M3 inf.D",
    }
    return names.get(fdi, f"FDI-{fdi}")


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["meta"])
async def root():
    return {
        "name":    "OrthoAI v2",
        "version": "2.0.0",
        "paper":   "https://arxiv.org/abs/2603.00124",
        "engine":  type(scorer).__name__,
        "status":  "ok",
    }


@app.get("/api/health", tags=["meta"])
async def health():
    return {"status": "ok", "engine": type(scorer).__name__, "ts": time.time()}


@app.get("/api/patients", tags=["demo"])
async def get_patients():
    """List the four preset clinical archetypes."""
    return {"patients": list_presets()}


@app.get("/api/patients/{patient_id}", tags=["demo"])
async def get_patient(patient_id: str, frames: bool = True):
    """Full analysis for a preset patient."""
    case = get_preset(patient_id)
    if case is None:
        raise HTTPException(404, f"Patient '{patient_id}' not found. "
                                 f"Available: {list(p for p in ['patient_001','patient_002','patient_003','patient_004'])}")
    return _build_response(
        case=case,
        movements=case.movements,
        num_stages=case.num_stages,
        patient_id=case.patient_id,
        patient_name=case.patient_name,
        case_type=case.case_type,
        description=case.description,
        generate_frames=frames,
    )


@app.post("/api/analyze", tags=["planning"])
async def analyze(req: AnalyzeRequest):
    """Analyze a custom treatment plan."""
    movements = [_movement_schema_to_domain(m) for m in req.movements]
    if not movements:
        raise HTTPException(422, "movements list is empty")
    return _build_response(
        case=None,
        movements=movements,
        num_stages=req.num_stages,
        patient_name=req.patient_name or "Patient",
        case_type="Custom plan",
        generate_frames=req.generate_frames,
    )


@app.post("/api/demo", tags=["demo"])
async def demo(
    complexity: str = Query("moderate", enum=["simple","moderate","complex"]),
    seed:       int = Query(0),
    frames:     bool = Query(True),
):
    """Generate and analyze a synthetic demo case."""
    gen = SyntheticCaseGenerator(seed=seed)
    case = gen.next_case()
    # Override complexity if requested
    return _build_response(
        case=None,
        movements=case.movements,
        num_stages=case.num_stages,
        patient_id=f"demo_{seed}",
        patient_name="Demo Patient",
        case_type=f"Synthetic ({complexity})",
        description=f"Cas synthétique — complexité {complexity}, seed={seed}",
        generate_frames=frames,
    )


@app.get("/api/training/status", tags=["ml"])
async def training_status():
    """
    Return model training status and performance metrics.
    Weights are not included in the open-source repository.
    Results from arXiv:2603.00124v2, Table 3.
    """
    return {
        "dgcnn": {
            "status":    "pretrained",
            "params":    60705,
            "best_miou": 0.814,
            "best_tir":  0.812,
            "note":      "Weights available via Orthalytix commercial license",
        },
        "charm": {
            "status":    "pretrained",
            "mede_mm":   1.38,
            "msr_pct":   64.2,
            "note":      "Lightweight PointMLP (emb=128). See arXiv:2603.00124v2 Table 3.",
        },
        "training_curves": [],
        "engine": type(scorer).__name__,
        "weights_included": False,
        "weights_url": "https://orthalytix.com/orthoai#weights",
    }


# ── Static frontend ────────────────────────────────────────────────────────────
# Served when `npm run build` output is present in frontend/dist/
import pathlib
_DIST = pathlib.Path(__file__).parent.parent / "frontend" / "dist"
if _DIST.exists():
    app.mount("/", StaticFiles(directory=str(_DIST), html=True), name="frontend")
