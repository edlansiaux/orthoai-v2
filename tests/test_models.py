"""
OrthoAI v2 — Model architecture tests (requires torch)
MIT License — see LICENSE-MIT

Run only when torch is available:
    pytest tests/test_models.py -v
"""
import pytest
torch = pytest.importorskip("torch")

from orthoai.models.dgcnn import DGCNNSeg, DGCNNSegLoss
from orthoai.models.charm import CHaRM, CHaRMLoss


class TestDGCNN:
    def test_forward_shape(self):
        model = DGCNNSeg(k=5, emb_dims=64, num_classes=33)
        x = torch.randn(2, 3, 64)
        with torch.no_grad():
            out = model(x)
        assert out.shape == (2, 64, 33)

    def test_param_count(self):
        n = sum(p.numel() for p in DGCNNSeg().parameters())
        assert 10_000 < n < 10_000_000

    def test_loss(self):
        model = DGCNNSeg(k=5, emb_dims=64, num_classes=33)
        logits = model(torch.randn(2, 3, 64))
        labels = torch.randint(0, 33, (2, 64))
        loss = DGCNNSegLoss()(logits, labels)
        assert loss.item() > 0


class TestCHaRM:
    def test_forward_shapes(self):
        model = CHaRM(n_teeth=4, n_landmarks_per_tooth=3, emb_dims=32)
        x = torch.randn(2, 3, 33)
        with torch.no_grad():
            lm, hm, pres = model(x)
        assert lm.shape   == (2, 12, 3)
        assert hm.shape   == (2, 12, 33)
        assert pres.shape == (2, 4)
        assert (pres >= 0).all() and (pres <= 1).all()

    def test_loss(self):
        model = CHaRM(n_teeth=4, n_landmarks_per_tooth=3, emb_dims=32)
        x = torch.randn(2, 3, 33)
        _, h_pred, p_pred = model(x)
        loss = CHaRMLoss()(h_pred, torch.rand_like(h_pred), p_pred, torch.randint(0,2,(2,4)))
        assert loss.item() >= 0
