"""
OrthoAI v2 — Core test suite (no torch required)
MIT License — see LICENSE-MIT
"""
import math
import pytest
import warnings

from engine_stub import StubScorer, Movement6DOF, load_scorer
from orthoai.demo.presets import PRESETS, get_preset, list_presets
from orthoai.demo.synthetic import SyntheticCaseGenerator
from orthoai.demo.frame_generator import FrameGenerator
from orthoai.evaluation.metrics import mede, msr, summarise_results
from orthoai.agents.orchestrator import OrchestratorMode


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def scorer():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return StubScorer(seed=42, warn=False)

@pytest.fixture
def mvs():
    return [
        Movement6DOF(fdi=11, tx= 1.2, ty=0.3, rz= 5.0),
        Movement6DOF(fdi=21, tx=-1.2, ty=0.3, rz=-5.0),
        Movement6DOF(fdi=12, tx= 0.5, rz= 2.0),
        Movement6DOF(fdi=22, tx=-0.5, rz=-2.0),
    ]

@pytest.fixture
def fgen():
    return FrameGenerator(frames_per_aligner=2)


# ── StubScorer ────────────────────────────────────────────────────────────────

class TestStubScorer:
    def test_score_valid_range(self, scorer, mvs):
        s = scorer.score(mvs, num_stages=20)
        assert 0 <= s.overall <= 100
        assert s.grade in ("A","B","C","D","F")
        for attr in ("biomechanics","staging","attachments","ipr","occlusion","predictability"):
            assert 0 <= getattr(s, attr) <= 100

    def test_to_dict(self, scorer, mvs):
        d = scorer.score(mvs).to_dict()
        assert "overall" in d and "findings" in d
        assert isinstance(d["findings"], list)

    def test_per_tooth_info(self, scorer, mvs):
        for mv in mvs:
            info = scorer.per_tooth_info(mv)
            assert all(k in info for k in ("needs_attachment","needs_ipr","predictability","magnitude"))

    def test_load_scorer_fallback(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            s = load_scorer(None)
        assert isinstance(s, StubScorer)

    def test_extrusion_flag(self):
        assert Movement6DOF(fdi=11, tz=-1.0).is_extrusion is True
        assert Movement6DOF(fdi=11, tz= 1.0).is_extrusion is False


# ── Presets ───────────────────────────────────────────────────────────────────

class TestPresets:
    def test_count(self):
        assert len(PRESETS) == 4

    def test_all_have_movements(self):
        for p in PRESETS:
            assert len(p.movements) > 0

    def test_get(self):
        p = get_preset("patient_001")
        assert p is not None and p.patient_name == "Sophie M."

    def test_get_missing(self):
        assert get_preset("nope") is None

    def test_list_schema(self):
        for item in list_presets():
            assert all(k in item for k in ("patient_id","patient_name","num_stages","n_teeth"))
            assert item["n_teeth"] > 0

    def test_fdi_range(self):
        for p in PRESETS:
            for mv in p.movements:
                assert 11 <= mv.fdi <= 48

    def test_duration(self):
        for p in PRESETS:
            assert p.duration_months > 0


# ── Synthetic generator ───────────────────────────────────────────────────────

class TestSynthetic:
    def test_deterministic(self):
        c1 = SyntheticCaseGenerator(seed=7).next_case()
        c2 = SyntheticCaseGenerator(seed=7).next_case()
        assert c1.movements[0].fdi == c2.movements[0].fdi

    def test_different_seeds_differ(self):
        c1 = SyntheticCaseGenerator(seed=0).next_case()
        c2 = SyntheticCaseGenerator(seed=99).next_case()
        assert any(abs(a.tx - b.tx) > 0.01 for a, b in zip(c1.movements, c2.movements))

    def test_generate_n(self):
        cases = SyntheticCaseGenerator(seed=0).generate_n(9)
        assert len(cases) == 9
        complexities = {c.complexity for c in cases}
        assert complexities == {"simple","moderate","complex"}


# ── Frame generator ───────────────────────────────────────────────────────────

class TestFrameGen:
    def test_frame_count(self, fgen, mvs):
        frames = fgen.generate(mvs, num_aligners=10)
        assert len(frames) == 21  # 10*2 + 1

    def test_progress_bounds(self, fgen, mvs):
        frames = fgen.generate(mvs, num_aligners=10)
        assert frames[0].progress == pytest.approx(0.0)
        assert frames[-1].progress == pytest.approx(1.0)

    def test_extrusion_deferred(self, fgen):
        mv_ext = [Movement6DOF(fdi=11, tz=-1.5)]
        frames  = fgen.generate(mv_ext, num_aligners=20)
        init_z  = fgen._initial_arch(mv_ext)[11][2]
        # At t≈0.40 (<0.6), tz should not have moved
        early = next(f for f in frames if 0.38 < f.progress < 0.42)
        assert abs(early.teeth[11].centroid[2] - init_z) < 0.01

    def test_estimate_aligners(self, fgen):
        mvs = [Movement6DOF(fdi=11, rz=45.0)]
        a = fgen.estimate_aligners(mvs)
        assert a == max(math.ceil(45.0/2.0), 20)

    def test_to_dict(self, fgen, mvs):
        frames = fgen.generate(mvs, num_aligners=3)
        for f in frames:
            d = f.to_dict()
            assert all(k in d for k in ("frame_idx","progress","aligner_number","notes","teeth"))


# ── Metrics ───────────────────────────────────────────────────────────────────

class TestMetrics:
    def test_mede_perfect(self):
        pts = [[0,0,0],[1,1,1]]
        assert mede(pts, pts) == pytest.approx(0.0)

    def test_mede_unit(self):
        assert mede([[1,0,0]], [[0,0,0]]) == pytest.approx(1.0)

    def test_msr_within(self):
        assert msr([[0.5,0,0]], [[0,0,0]], threshold_mm=2.0) == pytest.approx(1.0)

    def test_msr_outside(self):
        assert msr([[5.0,0,0]], [[0,0,0]], threshold_mm=2.0) == pytest.approx(0.0)

    def test_summarise(self):
        results = [{"quality":q,"latency_s":1.0} for q in [70,80,90]]
        s = summarise_results(results)
        assert s["n_cases"] == 3
        assert s["quality_mean"] == pytest.approx(80.0)
        assert s["feasibility_pct"] == pytest.approx(100.0)

    def test_summarise_partial_feasible(self):
        results = [{"quality":q,"latency_s":1.0} for q in [60,80,90]]
        s = summarise_results(results)
        assert s["feasibility_pct"] == pytest.approx(200/3, rel=0.01)
