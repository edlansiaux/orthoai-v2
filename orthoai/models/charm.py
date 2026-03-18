"""
OrthoAI v2 — CHaRM Landmark Detection Architecture (Agent 2)
MIT License — see LICENSE-MIT

Conditioned Heatmap Regression Methodology for dental landmark localisation.
Architecture described in: arXiv:2603.00124v2, Section 3.2

Reference: Rodríguez-Ortega et al., "CHARM: Conditioned Heatmap Regression
Methodology for Accurate and Fast Dental Landmark Localization",
arXiv:2501.13073v5, 2025.

Our implementation uses a lightweight PointMLP encoder (emb=128 vs 512 in
the original CHaRNet) to support consumer-CPU deployment.
"""

from __future__ import annotations
import torch
import torch.nn as nn
import torch.nn.functional as F


# ── Lightweight PointMLP blocks ───────────────────────────────────────────────

class SharedMLP(nn.Module):
    def __init__(self, in_ch: int, out_ch: int, bn: bool = True):
        super().__init__()
        layers: list[nn.Module] = [nn.Conv1d(in_ch, out_ch, 1, bias=not bn)]
        if bn:
            layers.append(nn.BatchNorm1d(out_ch))
        layers.append(nn.ReLU(inplace=True))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class PointMLPEncoder(nn.Module):
    """
    Lightweight PointMLP encoder: 3 → 64 → 128 → emb_dims with global context.
    Operates on (B, 3, N+1) point clouds (N scan points + 1 null conditioning point).
    """

    def __init__(self, emb_dims: int = 128):
        super().__init__()
        self.emb_dims = emb_dims
        self.local = nn.Sequential(
            SharedMLP(3,   64),
            SharedMLP(64,  128),
            SharedMLP(128, emb_dims),
        )
        self.global_proj = SharedMLP(emb_dims, emb_dims)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (B, 3, N+1) → local features (B, 2*emb_dims, N+1)"""
        local_feat = self.local(x)                                # (B, emb, N+1)
        global_feat = local_feat.max(dim=-1, keepdim=True)[0]     # (B, emb, 1)
        global_feat = self.global_proj(global_feat).expand_as(local_feat)
        return torch.cat([local_feat, global_feat], dim=1)        # (B, 2*emb, N+1)


# ── CHaRM model ───────────────────────────────────────────────────────────────

class CHaRM(nn.Module):
    """
    Conditioned Heatmap Regression Model for dental landmark detection.

    Architecture:
      - PointMLP encoder → per-point features (B, 2*emb, N+1)
      - Heatmap head     → K raw heatmaps (B, K, N+1)
      - Presence head    → T tooth presence probabilities (B, T)
      - CHaR gating      → conditioned heatmaps (B, K, N+1)

    Landmark extraction: argmax over conditioned heatmaps → (B, K, 3)

    Default: T=16 teeth, G=5 landmarks/tooth → K=80 landmarks.
    """

    def __init__(
        self,
        n_teeth: int = 16,         # teeth per arch (half-arch model)
        n_landmarks_per_tooth: int = 5,
        emb_dims: int = 128,
    ):
        super().__init__()
        self.T = n_teeth
        self.G = n_landmarks_per_tooth
        self.K = n_teeth * n_landmarks_per_tooth  # 80

        self.encoder = PointMLPEncoder(emb_dims)

        # Heatmap regression head: K heatmap channels
        self.heatmap_head = nn.Sequential(
            SharedMLP(2 * emb_dims, 256),
            SharedMLP(256, 128),
            nn.Conv1d(128, self.K, 1),   # (B, K, N+1)
        )

        # Tooth presence classification head
        self.presence_head = nn.Sequential(
            nn.Linear(2 * emb_dims, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(256, self.T),
            nn.Sigmoid(),   # (B, T) ∈ [0, 1]
        )

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        x : (B, 3, N+1)  — augmented point cloud (N points + 1 null point)

        Returns:
            landmarks   : (B, K, 3)   — estimated landmark coordinates
            raw_heatmaps: (B, K, N+1) — unconditioned heatmaps
            presence    : (B, T)       — tooth presence probabilities
        """
        B, _, NP1 = x.size()

        feat = self.encoder(x)                         # (B, 2*emb, N+1)

        # Raw heatmaps
        h_raw = self.heatmap_head(feat)                # (B, K, N+1)

        # Presence probabilities from global feature
        global_feat = feat.max(dim=-1)[0]              # (B, 2*emb)
        presence = self.presence_head(global_feat)     # (B, T)

        # CHaR conditioning (Eq. 3 of arXiv:2603.00124v2)
        h_conditioned = self._char_gate(h_raw, presence, NP1)  # (B, K, N+1)

        # Extract landmark coordinates by argmax
        landmarks = self._extract_landmarks(x, h_conditioned)  # (B, K, 3)

        return landmarks, h_conditioned, presence

    def _char_gate(
        self,
        h: torch.Tensor,
        p: torch.Tensor,
        n_plus_1: int,
    ) -> torch.Tensor:
        """
        Gate heatmap points 0..N-1 by tooth presence probability,
        and null point N by (1 - presence).

        h : (B, K, N+1)
        p : (B, T)         — repeated G times to cover K channels
        """
        B, K, NP1 = h.size()
        # Expand presence: (B, T) → (B, K) by repeating G times
        p_k = p.repeat_interleave(self.G, dim=1)  # (B, K)
        p_k = p_k.unsqueeze(-1)                   # (B, K, 1)

        scan_pts = h[:, :, :-1] * p_k              # points 0..N-1
        null_pt  = h[:, :, -1:] * (1.0 - p_k)     # null point N
        return torch.cat([scan_pts, null_pt], dim=-1)

    @staticmethod
    def _extract_landmarks(
        points: torch.Tensor,
        heatmaps: torch.Tensor,
    ) -> torch.Tensor:
        """
        Extract landmark coordinates as argmax of conditioned heatmaps.

        points   : (B, 3, N+1)
        heatmaps : (B, K, N+1)
        → landmarks (B, K, 3)
        """
        idx = heatmaps.argmax(dim=-1)               # (B, K)
        pts = points.transpose(1, 2)                # (B, N+1, 3)
        B, K = idx.size()
        idx_exp = idx.unsqueeze(-1).expand(B, K, 3) # (B, K, 3)
        pts_exp = pts.unsqueeze(1).expand(B, K, -1, 3).reshape(B * K, -1, 3)
        idx_flat = idx_exp.reshape(B * K, 1, 3)
        return pts_exp.gather(1, idx_flat).reshape(B, K, 3)


class CHaRMLoss(nn.Module):
    """
    Combined MSE heatmap regression + BCE presence classification loss.
    λ_reg=0.001, λ_cls=1.0 (from CHaRNet paper).
    """

    def __init__(self, lambda_reg: float = 0.001, lambda_cls: float = 1.0):
        super().__init__()
        self.lambda_reg = lambda_reg
        self.lambda_cls = lambda_cls
        self.bce = nn.BCELoss()

    def forward(
        self,
        heatmaps_pred: torch.Tensor,   # (B, K, N+1)
        heatmaps_gt:   torch.Tensor,   # (B, K, N+1)
        presence_pred: torch.Tensor,   # (B, T)
        presence_gt:   torch.Tensor,   # (B, T)
    ) -> torch.Tensor:
        mse  = F.mse_loss(heatmaps_pred, heatmaps_gt)
        bce  = self.bce(presence_pred, presence_gt.float())
        return self.lambda_reg * mse + self.lambda_cls * bce
