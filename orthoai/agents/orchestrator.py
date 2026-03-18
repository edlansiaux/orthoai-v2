"""
OrthoAI v2 — Orchestrator
MIT License — see LICENSE-MIT

Fuses Agent1 (DGCNN) and Agent2 (CHaRM) outputs via three modes:
  PARALLEL   — confidence-weighted centroid averaging, both agents always run
  SEQUENTIAL — CHaRM first; DGCNN invoked only for low-confidence teeth
  SINGLE     — single agent (replicates v1 behaviour with agent=1)

The default fusion weights (w1=0.4, w2=0.6) are set here.
Note: the commercial engine may override these weights with data-calibrated
values derived from the IOSLandmarks-1k benchmark.
"""

from __future__ import annotations
from enum import Enum
from typing import Optional
import time

from orthoai.agents.base import AgentOutput, BaseAgent, ToothState


class OrchestratorMode(str, Enum):
    PARALLEL   = "parallel"
    SEQUENTIAL = "sequential"
    SINGLE     = "single"


class Orchestrator:
    """
    Fuse Agent1 and Agent2 outputs into a unified set of ToothStates.

    Args:
        agent1       : DGCNN segmentation agent
        agent2       : CHaRM landmark agent (optional for SINGLE mode)
        mode         : fusion mode
        w1, w2       : base confidence weights for parallel fusion
        conf_threshold: CHaRM confidence below which DGCNN is invoked (SEQUENTIAL)
    """

    DEFAULT_W1 = 0.4   # DGCNN weight (lower: centroid-only geometry)
    DEFAULT_W2 = 0.6   # CHaRM weight (higher: landmark-level accuracy)

    def __init__(
        self,
        agent1: BaseAgent,
        agent2: Optional[BaseAgent] = None,
        mode: OrchestratorMode = OrchestratorMode.PARALLEL,
        w1: float = DEFAULT_W1,
        w2: float = DEFAULT_W2,
        conf_threshold: float = 0.5,
    ):
        self.agent1 = agent1
        self.agent2 = agent2
        self.mode = mode
        self.w1 = w1
        self.w2 = w2
        self.conf_threshold = conf_threshold

        if mode != OrchestratorMode.SINGLE and agent2 is None:
            raise ValueError("Agent2 required for PARALLEL and SEQUENTIAL modes.")

    def run(self, point_cloud) -> tuple[dict[int, ToothState], dict]:
        """
        Run orchestration on a point cloud.

        Returns:
            fused_teeth : dict[int, ToothState] — FDI → fused tooth state
            meta        : dict — latency and per-agent stats
        """
        t0 = time.perf_counter()

        if self.mode == OrchestratorMode.SINGLE:
            out1 = self.agent1.infer(point_cloud)
            fused = out1.teeth
            meta = {"mode": "single", "agent1_ms": out1.latency_ms}

        elif self.mode == OrchestratorMode.PARALLEL:
            out1 = self.agent1.infer(point_cloud)
            out2 = self.agent2.infer(point_cloud)   # type: ignore[union-attr]
            fused = self._parallel_fuse(out1, out2)
            meta = {
                "mode": "parallel",
                "agent1_ms": out1.latency_ms,
                "agent2_ms": out2.latency_ms,
            }

        elif self.mode == OrchestratorMode.SEQUENTIAL:
            out2 = self.agent2.infer(point_cloud)   # type: ignore[union-attr]
            low_conf_fdis = [
                fdi for fdi, ts in out2.teeth.items()
                if ts.confidence < self.conf_threshold
            ]
            if low_conf_fdis:
                out1 = self.agent1.infer(point_cloud)
                fused = self._sequential_fuse(out1, out2, low_conf_fdis)
                meta = {
                    "mode": "sequential+dgcnn",
                    "agent1_ms": out1.latency_ms,
                    "agent2_ms": out2.latency_ms,
                    "dgcnn_invoked_fdis": low_conf_fdis,
                }
            else:
                fused = out2.teeth
                meta = {"mode": "sequential_charm_only", "agent2_ms": out2.latency_ms}

        else:
            raise ValueError(f"Unknown mode: {self.mode}")

        meta["total_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        return fused, meta

    # ── Fusion implementations ────────────────────────────────────────────────

    def _parallel_fuse(
        self,
        out1: AgentOutput,
        out2: AgentOutput,
    ) -> dict[int, ToothState]:
        """
        Confidence-weighted centroid fusion (Eq. 4 of arXiv:2603.00124v2).

        c_fused = w1 * c_A1 + w2 * c_A2   (normalised by w1+w2)
        """
        all_fdis = set(out1.teeth) | set(out2.teeth)
        fused: dict[int, ToothState] = {}

        for fdi in all_fdis:
            ts1 = out1.teeth.get(fdi)
            ts2 = out2.teeth.get(fdi)

            if ts1 is None:
                fused[fdi] = ts2  # type: ignore[assignment]
            elif ts2 is None:
                fused[fdi] = ts1
            else:
                w_total = self.w1 + self.w2
                centroid = [
                    (self.w1 * ts1.centroid[i] + self.w2 * ts2.centroid[i]) / w_total
                    for i in range(3)
                ]
                # Prefer CHaRM landmarks when available
                fused[fdi] = ToothState(
                    fdi=fdi,
                    centroid=centroid,
                    axes=ts2.axes if ts2.landmarks else ts1.axes,
                    confidence=(self.w1 * ts1.confidence + self.w2 * ts2.confidence) / w_total,
                    present=ts1.present or ts2.present,
                    landmarks=ts2.landmarks,
                )

        return fused

    def _sequential_fuse(
        self,
        out1: AgentOutput,
        out2: AgentOutput,
        low_conf_fdis: list[int],
    ) -> dict[int, ToothState]:
        """
        Sequential mode: use CHaRM for high-confidence teeth,
        boost DGCNN weight (0.8) for low-confidence teeth.
        """
        fused = dict(out2.teeth)  # start from CHaRM baseline
        for fdi in low_conf_fdis:
            ts1 = out1.teeth.get(fdi)
            ts2 = out2.teeth.get(fdi)
            if ts1 is None:
                continue
            if ts2 is None:
                fused[fdi] = ts1
                continue
            # DGCNN-dominant weights for these specific teeth
            w1_local, w2_local = 0.8, 0.2
            centroid = [
                (w1_local * ts1.centroid[i] + w2_local * ts2.centroid[i])
                for i in range(3)
            ]
            fused[fdi] = ToothState(
                fdi=fdi,
                centroid=centroid,
                axes=ts1.axes,
                confidence=w1_local * ts1.confidence + w2_local * ts2.confidence,
                present=ts1.present,
                landmarks=ts2.landmarks,
            )
        return fused
