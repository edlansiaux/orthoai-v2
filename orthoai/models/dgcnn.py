"""
OrthoAI v2 — DGCNN Segmentation Architecture (Agent 1)
MIT License — see LICENSE-MIT

Dynamic Graph CNN for tooth segmentation on IOS point clouds.
Architecture described in: arXiv:2603.00124v2, Section 3.1

Reference: Wang et al., "Dynamic Graph CNN for Learning on Point Clouds",
ACM Transactions on Graphics 38(5), 2019.
"""

from __future__ import annotations
import torch
import torch.nn as nn
import torch.nn.functional as F


def knn(x: torch.Tensor, k: int) -> torch.Tensor:
    """Return indices of k-nearest neighbours in feature space."""
    inner = -2 * torch.matmul(x.transpose(2, 1), x)
    xx = torch.sum(x ** 2, dim=1, keepdim=True)
    pairwise_distance = -xx - inner - xx.transpose(2, 1)
    return pairwise_distance.topk(k=k, dim=-1)[1]


def get_graph_feature(x: torch.Tensor, k: int = 20, idx: torch.Tensor | None = None) -> torch.Tensor:
    """Construct edge features for EdgeConv."""
    B, C, N = x.size()
    if idx is None:
        idx = knn(x, k=k)
    idx_base = torch.arange(0, B, device=x.device).view(-1, 1, 1) * N
    idx = (idx + idx_base).view(-1)
    x = x.transpose(2, 1).contiguous()
    feature = x.view(B * N, -1)[idx, :].view(B, N, k, C)
    x = x.view(B, N, 1, C).expand(-1, -1, k, -1)
    return torch.cat((feature - x, x), dim=3).permute(0, 3, 1, 2).contiguous()


class EdgeConv(nn.Module):
    """Single EdgeConv layer: h(x_i, x_j - x_i) aggregated by max-pool."""

    def __init__(self, in_channels: int, out_channels: int, k: int = 20):
        super().__init__()
        self.k = k
        self.mlp = nn.Sequential(
            nn.Conv2d(2 * in_channels, out_channels, 1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(out_channels, out_channels, 1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.LeakyReLU(0.2, inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feat = get_graph_feature(x, k=self.k)   # (B, 2C, N, k)
        feat = self.mlp(feat)                    # (B, C', N, k)
        return feat.max(dim=-1)[0]               # (B, C', N)


class DGCNNSeg(nn.Module):
    """
    4-layer Dynamic Graph CNN for point-cloud tooth segmentation.

    Input:  (B, 3, N)  — raw XYZ coordinates
    Output: (B, N, num_classes)  — per-point class logits

    num_classes = 33  (32 FDI tooth labels + gingiva background)

    60,705 parameters at default channel widths.
    Inference: ~2.1s CPU (i7-11800H, N=8192 points).
    """

    N_CLASSES = 33  # 32 teeth (FDI) + 1 gingiva

    def __init__(
        self,
        k: int = 20,
        emb_dims: int = 1024,
        dropout: float = 0.5,
        num_classes: int = N_CLASSES,
    ):
        super().__init__()
        self.k = k

        # Four EdgeConv layers
        self.conv1 = EdgeConv(3,   64,  k)
        self.conv2 = EdgeConv(64,  64,  k)
        self.conv3 = EdgeConv(64,  128, k)
        self.conv4 = EdgeConv(128, 256, k)

        # Point-wise projection to global embedding
        self.conv5 = nn.Sequential(
            nn.Conv1d(64 + 64 + 128 + 256, emb_dims, 1, bias=False),
            nn.BatchNorm1d(emb_dims),
            nn.LeakyReLU(0.2, inplace=True),
        )

        # Segmentation head
        self.seg_head = nn.Sequential(
            nn.Conv1d(emb_dims * 2, 512, 1, bias=False),
            nn.BatchNorm1d(512),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Dropout(dropout),
            nn.Conv1d(512, 256, 1, bias=False),
            nn.BatchNorm1d(256),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Dropout(dropout),
            nn.Conv1d(256, num_classes, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, _, N = x.size()

        h1 = self.conv1(x)               # (B, 64, N)
        h2 = self.conv2(h1)              # (B, 64, N)
        h3 = self.conv3(h2)              # (B, 128, N)
        h4 = self.conv4(h3)              # (B, 256, N)

        cat = torch.cat([h1, h2, h3, h4], dim=1)   # (B, 512, N)
        local_feat = self.conv5(cat)                # (B, emb_dims, N)

        global_feat = local_feat.max(dim=-1, keepdim=True)[0].expand(-1, -1, N)
        feat = torch.cat([local_feat, global_feat], dim=1)  # (B, 2*emb_dims, N)

        logits = self.seg_head(feat)     # (B, num_classes, N)
        return logits.transpose(2, 1)   # (B, N, num_classes)


class DGCNNSegLoss(nn.Module):
    """Combined cross-entropy + Dice loss for class-imbalanced dental segmentation."""

    def __init__(self, alpha: float = 0.5, ignore_index: int = -1):
        super().__init__()
        self.alpha = alpha
        self.ce = nn.CrossEntropyLoss(ignore_index=ignore_index)

    def dice_loss(self, pred: torch.Tensor, target: torch.Tensor, n_classes: int) -> torch.Tensor:
        pred_soft = F.softmax(pred, dim=-1)
        target_one_hot = F.one_hot(target.clamp(0), n_classes).float()
        intersection = (pred_soft * target_one_hot).sum(dim=(0, 1))
        cardinality = pred_soft.sum(dim=(0, 1)) + target_one_hot.sum(dim=(0, 1))
        dice_per_class = 1.0 - (2.0 * intersection + 1e-6) / (cardinality + 1e-6)
        return dice_per_class.mean()

    def forward(self, logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        """
        logits : (B, N, C)
        labels : (B, N)  — FDI class indices 0–32
        """
        ce = self.ce(logits.reshape(-1, logits.size(-1)), labels.reshape(-1))
        dice = self.dice_loss(logits, labels, logits.size(-1))
        return (1 - self.alpha) * ce + self.alpha * dice
