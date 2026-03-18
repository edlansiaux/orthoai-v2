"""
OrthoAI v2 — Abstract Agent Interface
MIT License — see LICENSE-MIT

Defines the interface contract that both Agent1 (DGCNN) and Agent2 (CHaRM)
must satisfy. Also defines the shared ToothState data structure that flows
between agents, orchestrator, and scoring engine.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import torch


# ── Shared data types ─────────────────────────────────────────────────────────

@dataclass
class ToothState:
    """
    Minimal geometric representation of a single tooth, as estimated by an agent.
    Sufficient for biomechanical scoring and frame generation.
    """
    fdi:        int             # FDI tooth number (11–48)
    centroid:   list[float]     # [x, y, z] mm
    axes:       list[list[float]] = field(default_factory=lambda: [[1,0,0],[0,1,0],[0,0,1]])
    confidence: float = 1.0    # agent confidence ∈ [0, 1]
    present:    bool  = True   # False if tooth absent / not detected

    # Landmark-level data (Agent 2 only; None for Agent 1)
    landmarks:  Optional[list[list[float]]] = None  # (G, 3) landmark coords


@dataclass
class AgentOutput:
    """Output of a single agent pass."""
    agent_id:    int                  # 1 = DGCNN, 2 = CHaRM
    teeth:       dict[int, ToothState]  # FDI → ToothState
    latency_ms:  float = 0.0
    device:      str   = "cpu"


# ── Abstract base ─────────────────────────────────────────────────────────────

class BaseAgent(ABC):
    """
    Abstract base class for OrthoAI v2 agents.

    All agents must implement:
      - load_weights(path)  — load checkpoint
      - infer(point_cloud)  — run inference on a single IOS scan
      - from_pretrained()   — class method for loading official weights (commercial)
    """

    AGENT_ID: int = 0  # override in subclass

    def __init__(self, device: str = "cpu"):
        self.device = device
        self._model: "torch.nn.Module | None" = None
        self._loaded = False

    @abstractmethod
    def load_weights(self, path: str) -> None:
        """Load model weights from a checkpoint file."""
        ...

    @abstractmethod
    def infer(self, point_cloud: torch.Tensor) -> AgentOutput:
        """
        Run inference on a single IOS point cloud.

        Args:
            point_cloud : (N, 3) tensor of 3D points in mm

        Returns:
            AgentOutput with per-tooth states
        """
        ...

    @classmethod
    def from_pretrained(cls, token: str | None = None) -> "BaseAgent":
        """
        Load official Orthalytix pre-trained weights.

        Requires a valid API token. Obtain at: https://orthalytix.com/orthoai
        This method requires the commercial engine package to be installed:

            pip install orthoai-engine  # private PyPI — requires license key

        Raises:
            ImportError if orthoai-engine is not installed.
            PermissionError if token is invalid or expired.
        """
        try:
            from orthoai_engine import load_agent  # type: ignore[import]
            return load_agent(cls.AGENT_ID, token=token)
        except ImportError:
            raise ImportError(
                "Pre-trained weights require the commercial engine package.\n"
                "Install: pip install orthoai-engine  (requires Orthalytix license)\n"
                "Obtain a license at: https://orthalytix.com/orthoai"
            ) from None

    def is_loaded(self) -> bool:
        return self._loaded
