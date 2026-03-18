# OrthoAI v2 — AI-Assisted Clear Aligner Treatment Planning

[![arXiv](https://img.shields.io/badge/arXiv-2603.15663-b31b1b.svg)](https://arxiv.org/abs/2603.15663)
[![License: MIT](https://img.shields.io/badge/Open%20Components-MIT-green.svg)](LICENSE-MIT)
[![License: Commercial](https://img.shields.io/badge/Engine-Commercial-blue.svg)](LICENSE-COMMERCIAL)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
  
**OrthoAI v2** is a dual-agent deep learning pipeline for AI-assisted orthodontic treatment
planning with clear aligners. It extends [OrthoAI v1](https://arxiv.org/abs/2603.00124) by
adding a CHaRM landmark-detection agent, a six-category biomechanical scoring model, and a
multi-frame 4D staging simulator.

> Paper: *OrthoAI v2: From Single-Agent Segmentation to Dual-Agent Treatment Planning for
> Clear Aligners* — Lansiaux E., Leman M., arXiv 2603.15663, March 2026.

---

## What is and isn't in this repository

This project follows an **open-core model** :

| Component | Status | License |
|---|---|---|
| DGCNN segmentation architecture | ✅ Full source | MIT |
| CHaRM landmark detection architecture | ✅ Full source | MIT |
| Abstract agent & orchestrator interfaces | ✅ Full source | MIT |
| Synthetic benchmark + evaluation metrics | ✅ Full source | MIT |
| FastAPI schema + route definitions | ✅ Full source | MIT |
| React SaaS dashboard | ✅ Full source | MIT |
| Evaluation scripts | ✅ Full source | MIT |
| Manuscript (PDF + LaTeX) | ✅ Released | CC BY 4.0 |
| **Pre-trained model weights** | 🔒 Not included | Commercial |
| **Composite scoring calibration** | 🔒 Stub only | Commercial |
| **Staging rule parameters** | 🔒 Stub only | Commercial |
| **Training pipeline + data loaders** | 🔒 Not included | Commercial |
| **Clinical movement limit database** | 🔒 Stub only | Commercial |

**Why this structure?**
The academic contribution (architectures, evaluation protocol, benchmark) is fully reproducible
from this repository. The *clinical calibration* — the exact biomechanical constants,
composite scoring weights, and staging parameters — constitutes a proprietary IP and is licensed separately.

This mirrors the model used by OpenAI (released GPT-2 architecture, not weights or RLHF
pipeline), Mistral (released architecture + weights, not fine-tuning data), and MongoDB
(open-source engine, closed Atlas cloud layer).

---

## Quick start (open components)

```bash
git clone https://github.com/edlansiaux/orthoai-v2
cd orthoai-v2
pip install -e ".[dev]"

# Run evaluation on synthetic benchmark (200 crowding scenarios)
python scripts/evaluate.py --n_cases 200 --mode parallel

# Launch API with stub engine (demo data only, no real inference)
python -m api.main --stub

# Frontend dev server
cd frontend && npm install && npm run dev
```

## Commercial engine (Orthalytix)

The production-calibrated engine (real biomechanical constants, trained weights,
full composite scoring) is available via:

- **SaaS API** — `api.orthalytix.com/v2` — contact us for access tokens
- **On-premise license** — Docker image with encrypted engine bundle
- **Research license** — free for academic institutions, contact below


---

## Repository structure

```
orthoai-v2/
├── orthoai/
│   ├── models/
│   │   ├── dgcnn.py          # DGCNN architecture (MIT)
│   │   └── charm.py          # CHaRM architecture (MIT)
│   ├── agents/
│   │   ├── base.py           # Abstract agent interface (MIT)
│   │   ├── agent1_dgcnn.py   # DGCNN segmentation agent (MIT)
│   │   ├── agent2_charm.py   # CHaRM landmark agent (MIT)
│   │   └── orchestrator.py   # Fusion orchestrator (MIT)
│   ├── evaluation/
│   │   ├── metrics.py        # MEDE, MSR, quality score (MIT)
│   │   └── benchmark.py      # 200-case synthetic benchmark (MIT)
│   └── demo/
│       ├── synthetic.py      # Synthetic case generator (MIT)
│       └── presets.py        # 4 preset clinical archetypes (MIT)
├── engine_stub/
│   ├── __init__.py           # Public interface (MIT)
│   ├── scorer.py             # AbstractScorer + StubScorer (MIT)
│   └── README.md             # How to plug in commercial engine
├── api/
│   ├── main.py               # FastAPI app (MIT)
│   └── schemas.py            # Pydantic models (MIT)
├── frontend/                 # React dashboard (MIT)
├── scripts/
│   ├── evaluate.py           # Benchmark runner (MIT)
│   └── export_onnx.py        # ONNX export stub (MIT)
├── paper/                    # arXiv PDF + LaTeX source
├── docker/
│   ├── Dockerfile.open       # Open stack (no engine)
│   └── Dockerfile.commercial # Placeholder for licensed image
└── pyproject.toml
```

---

## Citation

```bibtex
@article{lansiaux2026orthoaiv2,
  title   = {{OrthoAI} v2: From Single-Agent Segmentation to
             Dual-Agent Treatment Planning for Clear Aligners},
  author  = {Lansiaux, Edouard; Leman, Margaux},
  journal = {arXiv preprint arXiv:2603.15663},
  year    = {2026},
  url     = {https://arxiv.org/abs/2603.15663}
}
```

If you use the v1 baseline in comparison:

```bibtex
@article{lansiaux2026orthoaiv1,
  title   = {{OrthoAI}: A Neurosymbolic Framework for Evidence-Grounded Biomechanical Reasoning in Clear Aligner Orthodontics},
  author  = {Lansiaux, Edouard; Leman, Margaux; Ammi, Mehdi},
  journal = {arXiv preprint arXiv:2603.00124},
  year    = {2026}
}
```
