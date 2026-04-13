# PSAI-Bench: Physical Security AI Triage Benchmark

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-green.svg)](LICENSE)
[![CI](https://github.com/YuYongJu/psai-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/YuYongJu/psai-bench/actions/workflows/ci.yml)

**Do frontier AI models actually benefit from video when triaging physical security alerts — or are they just reasoning about metadata?**

PSAI-Bench is an evaluation framework that answers this question. It generates realistic security scenarios grounded in real datasets (UCF Crime, Caltech Pedestrian), scores model outputs on safety-weighted metrics, and measures the **perception-reasoning gap** — the difference between what a model achieves with metadata alone vs. metadata + video.

**Key finding:** GPT-4o achieves a near-perfect Threat Detection Rate (0.999) but collapses to a 0.580 Aggregate Score due to over-reliance on the SUSPICIOUS verdict (42.4% of responses). The model catches almost every threat but at the cost of drowning operators in false escalations — exactly the failure mode PSAI-Bench is designed to detect.

## Results

### UCF Crime Metadata Track (3,000 scenarios)

| System | Accuracy | TDR | FASR | Safety Score | ECE | Aggregate |
|--------|----------|-----|------|-------------|-----|-----------|
| **GPT-4o** | 0.645 | 0.999 | 0.792 | 0.947 | 0.186 | **0.580** |
| Severity Heuristic | 0.762 | 1.000 | 1.000 | 1.000 | — | 0.832 |
| Majority Class | 0.582 | 1.000 | 0.000 | 0.750 | — | 0.444 |
| Random | 0.326 | 0.656 | 0.307 | 0.569 | — | 0.446 |
| Always SUSPICIOUS | 0.179 | 1.000 | 0.000 | 0.750 | — | -0.204 |

> GPT-4o's raw accuracy (0.645) is beaten by the severity heuristic baseline (0.762) — a rule-based system that uses only the alert severity field. The model's strength is threat detection (TDR=0.999), but its SUSPICIOUS overuse (42.4% vs. the 30% penalty threshold) tanks the aggregate score.

### GPT-4o Per-Difficulty Breakdown

| Difficulty | Accuracy | Safety Score |
|-----------|----------|-------------|
| Easy | 0.723 | — |
| Medium | 0.587 | — |
| Hard | 0.625 | — |

## Evaluation Tracks

PSAI-Bench supports three evaluation tracks with increasing perceptual requirements:

| Track | Input | Scenarios | What It Tests |
|-------|-------|-----------|---------------|
| **Metadata** | Alert text, zone info, device stats, weather, time | 8,000 (UCF + Caltech) | Pure reasoning over structured context |
| **Visual** | Metadata + video clip URI | 2,900 (UCF Crime) | Whether video adds triage value |
| **Multi-Sensor** | Camera + PIR + badge + vibration + thermal | 1,000 (synthetic) | Sensor fusion reasoning |

## Metrics

| Metric | What It Measures |
|--------|-----------------|
| **TDR** (Threat Detection Rate) | Fraction of threats classified as THREAT or SUSPICIOUS |
| **FASR** (False Alarm Suppression Rate) | Fraction of benign alerts correctly classified as BENIGN |
| **Safety Score** | Weighted combination: `(w * TDR + FASR) / (w + 1)` at w=3 |
| **ECE** (Expected Calibration Error) | How well confidence scores match actual accuracy |
| **Aggregate Score** | `0.4 * accuracy + 0.4 * safety_score + 0.2 * calibration_factor - suspicious_penalty` |

The **SUSPICIOUS penalty** activates when a system uses the SUSPICIOUS verdict for >30% of responses, preventing the degenerate strategy of hedging everything.

## Installation

```bash
pip install -e .

# With API client support (for running evaluations)
pip install -e ".[api]"

# With development tools
pip install -e ".[dev]"
```

## Quick Start

### Generate scenarios

```bash
# Metadata track — UCF Crime dataset (3,000 scenarios)
psai-bench generate --track metadata --source ucf --n 3000 --seed 42

# Metadata track — Caltech Pedestrian dataset (5,000 scenarios)
psai-bench generate --track metadata --source caltech --n 5000 --seed 42

# Multi-sensor track (1,000 scenarios)
psai-bench generate --track multi_sensor --n 1000 --seed 42
```

### Run baselines

```bash
psai-bench baselines --scenarios data/generated/metadata_ucf_seed42.json
```

### Evaluate a frontier model

```bash
# Requires OPENAI_API_KEY environment variable
psai-bench evaluate --scenarios data/generated/metadata_ucf_seed42.json --model gpt-4o --n 100

# Available models: claude-sonnet, gpt-4o, gemini-flash
```

### Score outputs

```bash
psai-bench score --scenarios data/generated/metadata_ucf_seed42.json \
    --outputs results/evaluations/gpt-4o_ucf_metadata_run1.json
```

### Compare two systems

```bash
psai-bench compare --scenarios data/generated/metadata_ucf_seed42.json \
    --outputs-a results/evaluations/gpt-4o_run1.json \
    --outputs-b results/baselines/ucf/severity_heuristic_outputs.json
```

## Architecture

```
psai_bench/
  cli.py           # Click CLI with generate, score, evaluate, compare commands
  generators.py    # Scenario generators for all 3 tracks
  distributions.py # Realistic alert distribution models
  evaluators.py    # API wrappers for Claude, GPT-4o, Gemini
  scorer.py        # Scoring engine (TDR, FASR, Safety Score, ECE, Aggregate)
  baselines.py     # 4 statistical baselines
  statistics.py    # McNemar's test, bootstrap CIs, run consistency
  validation.py    # Scenario and submission validators
  schema.py        # JSON Schema definitions for alerts and outputs
  video_mapper.py  # Maps UCF Crime videos to visual track scenarios
  downloader.py    # HuggingFace dataset downloader
```

## Reproducibility

All generated data is deterministic given a seed. The canonical datasets are produced by:

```bash
psai-bench generate --track metadata --source ucf --n 3000 --seed 42
psai-bench generate --track metadata --source caltech --n 5000 --seed 42
```

**NumPy version note:** Scenario generation uses `numpy.random.RandomState` for determinism. Per [NEP 19](https://numpy.org/neps/nep-0019-rng-policy.html), the bit stream may differ across NumPy major versions. Results in this repository were generated with NumPy 1.24+ on Python 3.11.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## Citation

```bibtex
@misc{psai-bench-2025,
  title   = {PSAI-Bench: Physical Security AI Triage Benchmark},
  author  = {Apisar, Addison},
  year    = {2025},
  url     = {https://github.com/YuYongJu/psai-bench},
  note    = {Evaluates whether frontier AI models benefit from video in physical security triage}
}
```

## License

[Apache-2.0](LICENSE)
