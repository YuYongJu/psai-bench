# PSAI-Bench: Physical Security AI Triage Benchmark

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-green.svg)](LICENSE)
[![CI](https://github.com/YuYongJu/psai-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/YuYongJu/psai-bench/actions/workflows/ci.yml)

PSAI-Bench is an open-source benchmark for evaluating **any** AI system on physical security alert triage. Generate realistic scenarios, run your own system against them, and score the outputs.

## Quick Start: Bring Your Own System

### 1. Generate scenarios

```bash
psai-bench generate --track metadata --source ucf --n 3000 --seed 42 --version v2
```

### 2. Run your system

Feed the generated JSON to your system (LLM, ML model, rule engine, hybrid — anything that produces verdicts). See [Output Format](#output-format) for the required schema.

### 3. Score outputs

```bash
psai-bench score --scenarios data/generated/metadata_ucf_seed42_v2.json \
    --outputs path/to/your_system_outputs.json
```

## What PSAI-Bench Tests

v2.0 uses context-dependent ground truth — the same description text can be THREAT, SUSPICIOUS, or BENIGN depending on zone type and sensitivity, time of day, and device reliability. No single input field reveals the answer; systems must reason across multiple signals simultaneously.

See [Ground Truth Decision Rubric](docs/decision-rubric.md) for the full logic and worked examples.

## Metrics

| Metric | What It Measures |
|--------|-----------------|
| **TDR** (Threat Detection Rate) | Fraction of actual threats detected (classified THREAT or SUSPICIOUS) |
| **FASR** (False Alarm Suppression Rate) | Fraction of benign alerts correctly classified as BENIGN |
| **Decisiveness** | Fraction of verdicts that commit to THREAT or BENIGN (not SUSPICIOUS) |
| **Calibration (ECE)** | How well confidence scores match actual accuracy |
| **Per-Difficulty Accuracy** | Accuracy broken down by scenario difficulty tier |

## Results

**v2.0 scenarios have not yet been evaluated.** The v1.0 results were generated with scenarios that had single-field leakage — description text alone could predict ground truth with near-perfect accuracy. Those results are not meaningful under v2.0's context-dependent ground truth design. New evaluation results will be published once v2.0 scenario generation and scoring are validated.

## Evaluation Tracks

PSAI-Bench supports three evaluation tracks with increasing perceptual requirements:

| Track | Input | Scenarios | What It Tests |
|-------|-------|-----------|---------------|
| **Metadata** | Alert text, zone info, device stats, weather, time | 8,000 (UCF + Caltech) | Pure reasoning over structured context |
| **Visual** | Metadata + video clip URI | 2,900 (UCF Crime) | Whether video adds triage value |
| **Multi-Sensor** | Camera + PIR + badge + vibration + thermal | 1,000 (synthetic) | Sensor fusion reasoning |

## Built-in Evaluators

PSAI-Bench ships with built-in evaluators for GPT-4o, Claude, and Gemini as **reference implementations**. These are example integrations showing how to connect an LLM to the benchmark — they are not the intended workflow for production use.

```bash
# Example: run the built-in GPT-4o evaluator (requires OPENAI_API_KEY)
psai-bench evaluate --scenarios data/generated/metadata_ucf_seed42_v2.json --model gpt-4o --n 100
```

For serious benchmarking, use the [Bring Your Own System](#quick-start-bring-your-own-system) workflow.

## Output Format

Your system must produce a JSON array where each element has:

```json
{
  "alert_id": "string",
  "verdict": "THREAT | SUSPICIOUS | BENIGN",
  "confidence": 0.0
}
```

`confidence` is defined as the probability that the verdict is correct (0.0–1.0). The fields `reasoning` and `processing_time_ms` are optional and ignored by the scorer.

## Installation

```bash
pip install -e .

# With API client support (for running the built-in evaluators)
pip install -e ".[api]"

# With development tools
pip install -e ".[dev]"
```

## Architecture

```
psai_bench/
  cli.py           # Click CLI with generate, score, evaluate, compare commands
  generators.py    # Scenario generators for all 3 tracks
  distributions.py # Realistic alert distribution models + assign_ground_truth_v2
  evaluators.py    # API wrappers for Claude, GPT-4o, Gemini (reference implementations)
  scorer.py        # Scoring engine (TDR, FASR, Decisiveness, ECE, dashboard)
  baselines.py     # 4 statistical baselines
  statistics.py    # McNemar's test, bootstrap CIs, run consistency
  validation.py    # Scenario and submission validators
  schema.py        # JSON Schema definitions for alerts and outputs
  video_mapper.py  # Maps UCF Crime videos to visual track scenarios
  downloader.py    # HuggingFace dataset downloader
docs/
  decision-rubric.md  # Ground truth decision logic with worked examples
```

## Known Limitations

- **3-class triage only** — verdicts are THREAT / SUSPICIOUS / BENIGN. No dispatch actions (e.g., "send guard" vs. "review later") or severity sub-levels.
- **No video track in v2.0** — visual scenarios exist in the schema but v2.0 focuses on metadata-only reasoning. Video evaluation is planned for v3.0.
- **Single-annotator ground truth** — labels are assigned by a deterministic decision function, not by multiple human annotators. This means there is no inter-annotator agreement metric.
- **Synthetic scenarios only** — all scenarios are procedurally generated from distribution models, not drawn from real incident logs.
- **No temporal context** — each scenario is independent. Alert sequences and escalation patterns are out of scope for v2.0.

## Reproducibility

All generated data is deterministic given a seed. The canonical v2.0 dataset is produced by:

```bash
psai-bench generate --track metadata --source ucf --n 3000 --seed 42 --version v2
psai-bench generate --track metadata --source caltech --n 5000 --seed 42 --version v2
```

**NumPy version note:** Scenario generation uses `numpy.random.RandomState` for determinism. Per [NEP 19](https://numpy.org/neps/nep-0019-rng-policy.html), the bit stream may differ across NumPy major versions. Results in this repository were generated with NumPy 1.24+ on Python 3.11.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## Citation

```bibtex
@misc{psai-bench-2026,
  title   = {PSAI-Bench: Physical Security AI Triage Benchmark},
  author  = {Apisar, Addison},
  year    = {2026},
  url     = {https://github.com/YuYongJu/psai-bench},
  note    = {Evaluates AI system triage performance on non-trivially-solvable physical security scenarios}
}
```

## License

[Apache-2.0](LICENSE)
