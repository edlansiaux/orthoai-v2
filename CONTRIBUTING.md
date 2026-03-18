# Contributing to OrthoAI v2

Thank you for your interest in contributing. This document explains what you
can and cannot contribute to, given the open-core structure.

## What's open to contributions

All MIT-licensed components welcome PRs:

- **Model architectures** (`orthoai/models/`) — DGCNN and CHaRM improvements
- **Agent interfaces** (`orthoai/agents/`) — new agent types, orchestration modes
- **Evaluation** (`orthoai/evaluation/`) — new metrics, benchmark extensions
- **Demo data** (`orthoai/demo/`) — new preset cases, synthetic generators
- **Frontend** (`frontend/`) — UI improvements, new visualisations
- **API** (`api/`) — new routes, schema improvements
- **Tests** (`tests/`) — more coverage is always welcome
- **Docs** — README, docstrings, API documentation

## What is NOT open to contributions

The following are proprietary to Orthalytix SRL and cannot be contributed to
via the public repository:

- Clinical scoring calibration (movement limits, predictability coefficients)
- Pre-trained model weights
- Training data pipelines
- Commercial engine implementation

If you have clinical data or calibration improvements to contribute, please
contact us at research@orthalytix.com to discuss a research collaboration.

## How to contribute

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/my-improvement`
3. **Write tests** for any new functionality
4. **Run the test suite**: `pytest tests/test_all.py -v`
5. **Open a PR** with a clear description

## Code style

- Python: `ruff check` + `ruff format` (configured in `pyproject.toml`)
- React: standard JSX, no external CSS frameworks other than inline styles
- Commits: conventional format (`feat:`, `fix:`, `test:`, `docs:`)

## Reporting issues

- **Bug in open components** → GitHub Issues
- **Clinical/scoring concerns** → hello@orthalytix.com (confidential)
- **Security vulnerabilities** → security@orthalytix.com (private disclosure)

## Academic use

If you use OrthoAI v2 in research, please cite:

```bibtex
@article{lansiaux2026orthoaiv2,
  title  = {{OrthoAI} v2: From Single-Agent Segmentation to Dual-Agent Treatment Planning},
  author = {Lansiaux, Edouard},
  journal= {arXiv preprint arXiv:2603.00124v2},
  year   = {2026}
}
```
