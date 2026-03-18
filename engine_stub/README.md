# engine_stub — Open-Core Boundary Documentation

This directory defines the **public interface** between the open-source
components and the proprietary Orthalytix scoring engine.

## Architecture

```
orthoai-v2 (this repo, MIT)          orthoai-engine (commercial, not here)
─────────────────────────────         ──────────────────────────────────────
engine_stub/
  AbstractScorer  ◄──────────────────  OrthalytixScorer(AbstractScorer)
  Movement6DOF    ◄────── shared ─────  (same types, no re-definition)
  TreatmentScore  ◄────── shared ─────
  StubScorer      (dev only)
  load_scorer()   ◄──────────────────  returns OrthalytixScorer if licensed
```

## What the commercial engine adds

| Capability | Stub | Commercial |
|---|---|---|
| Movement limit database | ❌ random | ✅ Glaser 2017 + Kravitz 2009 calibrated |
| Composite scoring weights | ❌ random | ✅ Eq. 1 of arXiv:2603.00124v2 |
| Severity penalty thresholds | ❌ none | ✅ 0.85^crit × 0.97^warn |
| Over-engineering factor | ❌ ignored | ✅ ×1.30 Glaser Principle 4 |
| Anchorage loss detection | ❌ none | ✅ simultaneous molar check |
| IPR estimation | ❌ none | ✅ Bolton analysis model |
| Predictability per axis | ❌ random | ✅ Kravitz 2009 regression |
| Clinical finding texts | ❌ stub | ✅ full French/English |

## How to plug in the commercial engine

```python
# 1. Install (requires valid license key)
pip install orthoai-engine

# 2. Set your license key
export ORTHOAI_LICENSE_KEY="your-key-here"

# 3. Use the load_scorer helper — drops in transparently
import os
from engine_stub import load_scorer

scorer = load_scorer(os.environ.get("ORTHOAI_LICENSE_KEY"))
result = scorer.score(movements, num_stages=28)
```

The API server (`api/main.py`) already uses `load_scorer()` — no code
changes needed after installing the engine.

## Get a license

→ https://orthalytix.com/orthoai  
→ hello@orthalytix.com  
→ Research licenses: free for academic institutions
